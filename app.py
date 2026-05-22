import json
import os
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "accounts.json")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "cbkadmin123"
BANKS = [
    "KCB Bank Kenya",
    "Equity Bank Kenya",
    "Co-operative Bank of Kenya",
    "NCBA Bank Kenya",
    "Absa Bank Kenya",
    "I&M Bank",
    "Standard Chartered Bank Kenya",
    "Stanbic Bank Kenya",
    "Diamond Trust Bank Kenya",
    "Family Bank",
    "National Bank of Kenya",
    "Sidian Bank",
    "Prime Bank",
    "Ecobank Kenya",
    "Kingdom Bank",
    "Credit Bank",
    "UBA Kenya Bank",
    "Gulf African Bank",
    "DIB Bank Kenya"
]

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = "cbk_secret_key_2026"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def load_accounts():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_accounts(accounts):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_account_number(accounts):
    while True:
        number = str(random.randint(10**9, 10**10 - 1))
        if number not in accounts:
            return number


def save_file(field_storage, prefix, account_number):
    if field_storage and field_storage.filename and allowed_file(field_storage.filename):
        filename = secure_filename(field_storage.filename)
        suffix = f"_{prefix}_{account_number}_{int(datetime.utcnow().timestamp())}"
        filename = f"{os.path.splitext(filename)[0]}{suffix}{os.path.splitext(filename)[1]}"
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        field_storage.save(path)
        return filename
    return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        accounts = load_accounts()
        full_name = request.form.get("full_name", "").strip()
        id_type = request.form.get("id_type", "National ID")
        id_number = request.form.get("id_number", "").strip()
        phone = request.form.get("phone", "").strip()
        biometric = request.form.get("biometric", "").strip()
        mpin = request.form.get("mpin", "").strip()

        if not full_name or not id_number or not phone or not biometric or not mpin:
            flash("Please complete all required fields.", "error")
            return redirect(url_for("register"))

        if not mpin.isdigit() or len(mpin) != 4:
            flash("MPIN must be exactly 4 digits.", "error")
            return redirect(url_for("register"))

        account_number = generate_account_number(accounts)
        photo_file = save_file(request.files.get("photo"), "photo", account_number)
        id_front_file = save_file(request.files.get("id_front"), "id_front", account_number)
        id_back_file = save_file(request.files.get("id_back"), "id_back", account_number)
        passport_front_file = save_file(request.files.get("passport_front"), "passport_front", account_number)
        passport_back_file = save_file(request.files.get("passport_back"), "passport_back", account_number)

        accounts[account_number] = {
            "account_number": account_number,
            "name": full_name,
            "id_type": id_type,
            "id_number": id_number,
            "phone": phone,
            "biometric": biometric,
            "mpin": mpin,
            "balance": 0.0,
            "transactions": [],
            "photo": photo_file,
            "id_front": id_front_file,
            "id_back": id_back_file,
            "passport_front": passport_front_file,
            "passport_back": passport_back_file,
            "created_at": datetime.utcnow().isoformat()
        }
        save_accounts(accounts)
        flash(f"Account created successfully! Your CBK account number is {account_number}.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        accounts = load_accounts()
        account_number = request.form.get("account_number", "").strip()
        method = request.form.get("method", "mpin")
        credential = request.form.get("credential", "").strip()

        account = accounts.get(account_number)
        if not account:
            flash("Account number not found.", "error")
            return redirect(url_for("login"))

        if method == "mpin":
            if credential != account.get("mpin"):
                flash("Invalid MPIN.", "error")
                return redirect(url_for("login"))
        else:
            if credential != account.get("biometric"):
                flash("Invalid biometric phrase.", "error")
                return redirect(url_for("login"))

        session["account_number"] = account_number
        flash(f"Welcome back, {account['name']}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    account_number = session.get("account_number")
    if not account_number:
        return redirect(url_for("login"))

    accounts = load_accounts()
    account = accounts.get(account_number)
    return render_template("dashboard.html", account=account, bank_list=BANKS)


@app.route("/logout")
def logout():
    session.pop("account_number", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/deposit", methods=["POST"])
def deposit():
    account_number = session.get("account_number")
    if not account_number:
        return redirect(url_for("login"))

    amount = request.form.get("amount", "0").strip()
    try:
        amount_value = float(amount)
        if amount_value <= 0:
            raise ValueError
    except ValueError:
        flash("Enter a valid deposit amount.", "error")
        return redirect(url_for("dashboard"))

    accounts = load_accounts()
    account = accounts.get(account_number)
    account["balance"] += amount_value
    account["transactions"].append({
        "type": "Deposit",
        "amount": amount_value,
        "balance": account["balance"],
        "date": datetime.utcnow().isoformat()
    })
    save_accounts(accounts)
    flash(f"KES {amount_value:.2f} deposited to your account.", "success")
    return redirect(url_for("dashboard"))


@app.route("/transfer", methods=["POST"])
def transfer():
    account_number = session.get("account_number")
    if not account_number:
        return redirect(url_for("login"))

    bank = request.form.get("bank")
    destination = request.form.get("destination", "").strip()
    amount = request.form.get("amount", "0").strip()

    if bank not in BANKS:
        flash("Please select a valid destination bank.", "error")
        return redirect(url_for("dashboard"))

    if not destination:
        flash("Please enter a destination account number.", "error")
        return redirect(url_for("dashboard"))

    try:
        amount_value = float(amount)
        if amount_value <= 0:
            raise ValueError
    except ValueError:
        flash("Enter a valid transfer amount.", "error")
        return redirect(url_for("dashboard"))

    accounts = load_accounts()
    account = accounts.get(account_number)
    if amount_value > account["balance"]:
        flash("Insufficient balance for this transfer.", "error")
        return redirect(url_for("dashboard"))

    account["balance"] -= amount_value
    account["transactions"].append({
        "type": "Transfer",
        "bank": bank,
        "destination_account": destination,
        "amount": amount_value,
        "balance": account["balance"],
        "date": datetime.utcnow().isoformat()
    })
    save_accounts(accounts)
    flash(f"Transferred KES {amount_value:.2f} to {bank} ({destination}).", "success")
    return redirect(url_for("dashboard"))


@app.route("/loan", methods=["GET", "POST"])
def loan():
    account_number = session.get("account_number")
    if not account_number:
        return redirect(url_for("login"))

    accounts = load_accounts()
    account = accounts.get(account_number)
    approved = None
    message = None
    if request.method == "POST":
        amount = request.form.get("loan_amount", "0").strip()
        purpose = request.form.get("purpose", "").strip()
        try:
            loan_amount = float(amount)
            if loan_amount <= 0:
                raise ValueError
        except ValueError:
            flash("Enter a valid loan amount.", "error")
            return redirect(url_for("loan"))

        if loan_amount <= account["balance"] * 2 or loan_amount <= 500000:
            approved = True
            message = f"Your loan request for KES {loan_amount:.2f} is approved. Please contact CBK support to finalize your loan."
        else:
            approved = False
            message = "Your loan request requires further review. Contact CBK support for details."

    return render_template("loan.html", account=account, approved=approved, message=message)


@app.route("/statement", methods=["GET", "POST"])
def statement():
    account_number = session.get("account_number")
    if not account_number:
        return redirect(url_for("login"))

    accounts = load_accounts()
    account = accounts.get(account_number)
    message = None
    if request.method == "POST":
        start_date = request.form.get("start_date", "").strip()
        end_date = request.form.get("end_date", "").strip()
        if not start_date or not end_date:
            flash("Please select both start and end dates for the statement.", "error")
            return redirect(url_for("statement"))

        if "statement_requests" not in account:
            account["statement_requests"] = []
        account["statement_requests"].append({
            "start_date": start_date,
            "end_date": end_date,
            "requested_at": datetime.utcnow().isoformat(),
            "status": "Pending"
        })
        save_accounts(accounts)
        message = f"Statement request submitted for {start_date} to {end_date}. You can check your statement request history on this page."

    return render_template("statement.html", account=account, message=message)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.", "error")
    return render_template("admin.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    accounts = load_accounts()
    return render_template("admin_dashboard.html", accounts=accounts)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("Admin logged out.", "info")
    return redirect(url_for("admin"))


@app.route("/profile")
def profile():
    account_number = session.get("account_number")
    if not account_number:
        return redirect(url_for("login"))
    accounts = load_accounts()
    account = accounts.get(account_number)
    return render_template("profile.html", account=account)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
