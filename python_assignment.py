"""
Lab 1: Integrated Expense, Attendance, Grading and Billing Manager
Console, menu-driven program. Python 3.8+, standard library only.
"""
import math
from datetime import date

# ---------------- Configurable constants (CRS Section 15) ----------------
TAX_RATE = 0.18            # 18% tax, applied AFTER discount
PASS_MARK = 35             # any subject below this -> FAIL
ATTENDANCE_THRESHOLD = 75  # >= 75 Eligible
WARNING_LIMIT = 60         # 60-74.99 Warning, < 60 Shortage
DEFAULT_SUBJECTS = 5
CATEGORIES = ("Food", "Travel", "Utilities", "Stationery", "Other")
# (minimum subtotal, discount %) - highest matching slab wins
# NOTE: confirm slabs against Section 6.5 of the CRS
DISCOUNT_SLABS = ((10000, 15), (5000, 10), (1000, 5), (0, 0))
GRADE_SCALE = ((90, "A+", "Outstanding"), (80, "A", "Excellent"),
               (70, "B", "Very Good"), (60, "C", "Good"),
               (50, "D", "Satisfactory"), (35, "E", "Pass"),
               (0, "F", "Fail"))

# ---------------- In-memory data stores ----------------
expenses = []        # {"desc", "category", "amount"}
attendance = {"total_days": None, "records": []}  # records: {"name","id","present"}
students = []        # {"name","marks":[(subject, mark)]}
invoices = []        # {"bill_no","customer","date","items","subtotal",...}


# ======================= Validation helpers (Section 7) =======================
def get_int(prompt, min_val=1, max_val=float("inf"), error=None):
    """Prompt until an integer within [min_val, max_val] is entered."""
    while True:
        try:
            value = int(input(prompt).strip())
            if min_val <= value <= max_val:
                return value
        except ValueError:
            pass
        print(error or f"Enter a whole number between {min_val} and {max_val}.")


def get_float(prompt, min_val=0.0, max_val=float("inf"),
              error="Enter a valid number.", exclusive_min=False):
    """Prompt until a float in range is entered (exclusive_min => value > min_val)."""
    while True:
        try:
            value = float(input(prompt).strip())
            ok = value > min_val if exclusive_min else value >= min_val
            if ok and value <= max_val and math.isfinite(value):  # rejects nan / inf
                return value
        except ValueError:
            pass
        print(error)


def get_name(prompt):
    """Name: letters/spaces only, 2-40 characters."""
    while True:
        name = input(prompt).strip()
        if 2 <= len(name) <= 40 and name.replace(" ", "").isalpha():
            return name.title()
        print("Name must contain 2-40 letters.")


def get_choice(prompt, options):
    """Case-insensitive choice from a fixed list."""
    lookup = {o.lower(): o for o in options}
    while True:
        value = input(prompt).strip().lower()
        if value in lookup:
            return lookup[value]
        print("Choose a category from the list.")


# ======================= Expense module =======================
def add_expense():
    desc = input("Description: ").strip() or "N/A"
    category = get_choice(f"Category ({'/'.join(CATEGORIES)}): ", CATEGORIES)
    while True:  # re-prompt if the amount rounds to 0.00 (e.g. 0.001)
        amount = round(get_float("Amount: ", 0, error="Invalid amount. Please enter a positive number.",
                                 exclusive_min=True), 2)
        if amount > 0:
            break
        print("Invalid amount. Please enter a positive number.")
    expenses.append({"desc": desc, "category": category, "amount": amount})
    print("Expense added successfully!")


def expense_totals():
    totals = {c: 0.0 for c in CATEGORIES}
    for e in expenses:
        totals[e["category"]] += e["amount"]
    return totals


def view_expenses():
    if not expenses:
        print("No records available.")
        return
    print(f"\n{'No.':<5}{'Description':<22}{'Category':<12}{'Amount':>10}")
    print("-" * 49)
    for i, e in enumerate(expenses, 1):
        print(f"{i:<5}{e['desc'][:20]:<22}{e['category']:<12}{e['amount']:>10.2f}")


def expense_summary():
    if not expenses:
        print("No records available.")
        return
    print(f"\n{'CATEGORY':<14}{'TOTAL':>10}")
    for cat, tot in expense_totals().items():
        if tot > 0:
            print(f"{cat:<14}{tot:>10.2f}")
    print("-" * 24)
    print(f"{'GRAND TOTAL':<14}{sum(e['amount'] for e in expenses):>10.2f}")
    hi = max(expenses, key=lambda e: e["amount"])
    lo = min(expenses, key=lambda e: e["amount"])
    print(f"Highest expense: {hi['category']} - {hi['amount']:.2f}")
    print(f"Lowest expense : {lo['category']} - {lo['amount']:.2f}")


def expense_menu():
    while True:
        print("\n--- EXPENSE MANAGEMENT ---\n1. Add Expense\n2. View All Expenses\n"
              "3. Expense Summary\n4. Back")
        c = get_int("Enter your choice (1-4): ", 1, 4, "Invalid choice. Enter 1-4.")
        if c == 1: add_expense()
        elif c == 2: view_expenses()
        elif c == 3: expense_summary()
        else: return


# ======================= Attendance module =======================
def attendance_percentage(present, total):
    """Return percentage; guards against division by zero."""
    return round(present / total * 100, 2) if total > 0 else 0.0


def attendance_status(pct):
    if pct >= ATTENDANCE_THRESHOLD: return "Eligible"
    if pct >= WARNING_LIMIT: return "Warning"
    return "Shortage"


def set_total_days():
    attendance["total_days"] = get_int("Total working days: ", 1,
                                       error="Enter a whole number of at least 1.")


def mark_attendance():
    if attendance["total_days"] is None:
        set_total_days()
    total = attendance["total_days"]
    name = get_name("Name: ")
    pid = input("ID: ").strip() or "-"
    present = get_int("Days present: ", 0, total,
                      f"Days present must be between 0 and {total}.")
    attendance["records"].append({"name": name, "id": pid, "present": present})
    print("Attendance recorded.")


def view_attendance():
    if not attendance["records"]:
        print("No records available.")
        return
    total = attendance["total_days"]
    print(f"\n{'Name':<20}{'Total':>6}{'Present':>9}{'Att %':>9}  Status")
    print("-" * 56)
    for r in attendance["records"]:
        p = attendance_percentage(r["present"], total)
        print(f"{r['name']:<20}{total:>6}{r['present']:>9}{p:>9.2f}  {attendance_status(p)}")


def attendance_summary():
    recs = attendance["records"]
    if not recs:
        print("No records available.")
        return
    total = attendance["total_days"]
    pcts = [(r["name"], attendance_percentage(r["present"], total)) for r in recs]
    avg = sum(p for _, p in pcts) / len(pcts)
    hi = max(pcts, key=lambda x: x[1]); lo = min(pcts, key=lambda x: x[1])
    counts = {"Eligible": 0, "Warning": 0, "Shortage": 0}
    for _, p in pcts:
        counts[attendance_status(p)] += 1
    print(f"\nTotal students     : {len(recs)}")
    print(f"Average attendance : {avg:.2f}%")
    print(f"Highest            : {hi[0]} ({hi[1]:.2f}%)")
    print(f"Lowest             : {lo[0]} ({lo[1]:.2f}%)")
    print(f"Eligible: {counts['Eligible']} | Warning: {counts['Warning']} | Shortage: {counts['Shortage']}")


def attendance_menu():
    while True:
        print("\n--- ATTENDANCE MANAGEMENT ---\n1. Set Total Working Days\n2. Add Person\n"
              "3. View Attendance\n4. Attendance Summary\n5. Back")
        c = get_int("Enter your choice (1-5): ", 1, 5, "Invalid choice. Enter 1-5.")
        if c == 1: set_total_days()
        elif c == 2: mark_attendance()
        elif c == 3: view_attendance()
        elif c == 4: attendance_summary()
        else: return


# ======================= Grading module =======================
def calculate_grade(percentage):
    for floor, grade, remark in GRADE_SCALE:
        if percentage >= floor:
            return grade, remark
    return "F", "Fail"


def add_student():
    name = get_name("Student name: ")
    n = get_int(f"Number of subjects (default {DEFAULT_SUBJECTS}): ", 1, 20)
    marks = []
    for i in range(1, n + 1):
        subj = input(f"Subject {i} name: ").strip() or f"Subject {i}"
        m = get_float(f"Marks in {subj} (0-100): ", 0, 100,
                      "Marks must be between 0 and 100.")
        marks.append((subj, m))
    students.append({"name": name, "marks": marks})
    print("Student added.")


def student_result(s):
    values = [m for _, m in s["marks"]]
    total = sum(values)
    maximum = 100 * len(values)
    avg = total / len(values)
    pct = total / maximum * 100
    grade, remark = calculate_grade(pct)
    passed = not any(m < PASS_MARK for m in values)   # subject-level fail rule
    return total, maximum, avg, pct, grade, passed


def generate_report_card(s):
    total, maximum, avg, pct, grade, passed = student_result(s)
    print("\n========== REPORT CARD ==========")
    print(f"Student : {s['name']}")
    print("-" * 37)
    print(f"{'Subject':<16}{'Marks':>8}")
    for subj, m in s["marks"]:
        print(f"{subj:<16}{m:>8.2f}")
    print("-" * 37)
    print(f"Total      : {total:.2f} / {maximum}")
    print(f"Average    : {avg:.2f}")
    print(f"Percentage : {pct:.2f}%")
    print(f"Grade      : {grade}")
    print(f"Result     : {'PASS' if passed else 'FAIL'}")
    print("=" * 37)


def view_report_cards():
    if not students:
        print("No records available.")
        return
    for s in students:
        generate_report_card(s)


def class_summary():
    if not students:
        print("No records available.")
        return
    results = [(s["name"], student_result(s)) for s in students]
    avg = sum(r[1][3] for r in results) / len(results)
    topper = max(results, key=lambda r: r[1][3])
    passes = sum(1 for r in results if r[1][5])
    print(f"\nClass average : {avg:.2f}%")
    print(f"Topper        : {topper[0]} ({topper[1][3]:.2f}%)")
    print(f"Pass count    : {passes}")
    print(f"Fail count    : {len(results) - passes}")


def grading_menu():
    while True:
        print("\n--- GRADING SYSTEM ---\n1. Add Student & Marks\n2. View Report Cards\n"
              "3. Class Summary\n4. Back")
        c = get_int("Enter your choice (1-4): ", 1, 4, "Invalid choice. Enter 1-4.")
        if c == 1: add_student()
        elif c == 2: view_report_cards()
        elif c == 3: class_summary()
        else: return


# ======================= Billing module =======================
def calculate_discount(subtotal):
    for floor, pct in DISCOUNT_SLABS:
        if subtotal >= floor:
            return round(subtotal * pct / 100, 2), pct
    return 0.0, 0


def calculate_tax(taxable):
    return round(taxable * TAX_RATE, 2)


def generate_invoice(inv):
    print("\n" + "=" * 44)
    print(f"{'INVOICE':^44}")
    print("=" * 44)
    print(f"Bill No : {inv['bill_no']:<12} Date: {inv['date']}")
    print(f"Customer: {inv['customer']}")
    print("-" * 44)
    print(f"{'Item':<16}{'Price':>9}{'Qty':>5}{'Total':>12}")
    for name, price, qty in inv["items"]:
        print(f"{name[:15]:<16}{price:>9.2f}{qty:>5}{price * qty:>12.2f}")
    print("-" * 44)
    print(f"{'Subtotal':<30}{inv['subtotal']:>14.2f}")
    print(f"{'Discount (' + str(inv['disc_pct']) + '%)':<30}{inv['discount']:>14.2f}")
    print(f"{'Taxable amount':<30}{inv['taxable']:>14.2f}")
    print(f"{'Tax (' + str(int(TAX_RATE * 100)) + '%)':<30}{inv['tax']:>14.2f}")
    print("-" * 44)
    print(f"{'GRAND TOTAL':<30}{inv['grand']:>14.2f}")
    print("=" * 44)
    print("Thank you for your purchase!")


def new_bill():
    customer = get_name("Customer name: ")
    bill_no = f"B{len(invoices) + 1:04d}"
    items = []
    while True:
        name = input("Item name (or 'done' to finish): ").strip()
        if name.lower() == "done":
            break
        if not name:
            print("Item name cannot be empty.")
            continue
        price = get_float("Unit price: ", 0, error="Price must be greater than 0.",
                          exclusive_min=True)
        qty = get_int("Quantity: ", 1, error="Quantity must be a whole number >= 1.")
        items.append((name, round(price, 2), qty))
    if not items:
        print("No items added.")
        return
    subtotal = round(sum(p * q for _, p, q in items), 2)
    discount, pct = calculate_discount(subtotal)
    taxable = round(subtotal - discount, 2)
    tax = calculate_tax(taxable)
    inv = {"bill_no": bill_no, "customer": customer, "date": date.today().isoformat(),
           "items": items, "subtotal": subtotal, "discount": discount, "disc_pct": pct,
           "taxable": taxable, "tax": tax, "grand": round(taxable + tax, 2)}
    invoices.append(inv)
    generate_invoice(inv)


def billing_menu():
    while True:
        print("\n--- BILLING SYSTEM ---\n1. Create New Bill\n2. View Past Invoices\n3. Back")
        c = get_int("Enter your choice (1-3): ", 1, 3, "Invalid choice. Enter 1-3.")
        if c == 1: new_bill()
        elif c == 2:
            if not invoices: print("No records available.")
            for inv in invoices: generate_invoice(inv)
        else: return


# ======================= Reports module =======================
def export_report(filename, lines):
    """Optional FR-53: write captured report text to a file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Report exported to {filename}")
    except OSError as err:
        print(f"Could not export report: {err}")


def reports_menu():
    import io, contextlib
    funcs = {1: ("expense", expense_summary), 2: ("attendance", attendance_summary),
             3: ("grading", class_summary),
             4: ("billing", lambda: [generate_invoice(i) for i in invoices] or print("No records available."))}
    while True:
        print("\n--- REPORTS ---\n1. Expense Report\n2. Attendance Report\n"
              "3. Grading Report\n4. Billing Report\n5. Back")
        c = get_int("Enter your choice (1-5): ", 1, 5, "Invalid choice. Enter 1-5.")
        if c == 5:
            return
        name, fn = funcs[c]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            fn()
        text = buf.getvalue()
        print(text, end="")
        if "No records available" not in text:
            if input("Export to file? (y/n): ").strip().lower() == "y":
                export_report(f"{name}_report.txt", text.splitlines())


# ======================= Main program =======================
def display_menu():
    print("\n" + "=" * 46)
    print("EXPENSE | ATTENDANCE | GRADING | BILLING")
    print("=" * 46)
    print("1. Expense Management\n2. Attendance Management\n3. Grading System\n"
          "4. Billing System\n5. View Reports\n6. Exit")
    print("-" * 46)


def main():
    actions = {1: expense_menu, 2: attendance_menu, 3: grading_menu,
               4: billing_menu, 5: reports_menu}
    try:
        while True:
            display_menu()
            choice = get_int("Enter your choice (1-6): ", 1, 6,
                             "Invalid choice. Enter a number between 1 and 6.")
            if choice == 6:
                print("Thank you for using the system. Goodbye!")
                break
            actions[choice]()
    except (KeyboardInterrupt, EOFError):
        print("\nProgram interrupted. Goodbye!")


if __name__ == "__main__":
    main()
