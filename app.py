import json
import os
import random
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "accounts.json")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "cbkadmin123")
AUTO_LOGOUT_SECONDS = 900
CURRENCIES = {
    "KSH": "KES",
    "USD": "$",
    "EUR": "€"
}
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


@app.before_request
def manage_session_timeout():
    if request.endpoint in ("static",):
        return
    last_activity = session.get("last_activity")
    now_ts = datetime.utcnow().timestamp()
    if last_activity and now_ts - last_activity > AUTO_LOGOUT_SECONDS:
        session.pop("account_number", None)
        session.pop("admin_logged_in", None)
        session.pop("last_activity", None)
        flash("You have been logged out after inactivity.", "info")
        return redirect(url_for("login"))
    session["last_activity"] = now_ts


def load_accounts():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        migrated = False
        for acct in data.values():
            if acct.get("fingerprint") and not acct.get("biometric"):
                acct["biometric"] = acct.get("fingerprint")
                acct.pop("fingerprint", None)
                migrated = True
            if "currency" not in acct:
                acct["currency"] = "KSH"
                migrated = True
            if "kyc_status" not in acct:
                acct["kyc_status"] = "Pending"
                migrated = True
            if "email_verified" not in acct:
                acct["email_verified"] = False
                migrated = True
            if "email_verification_token" not in acct:
                acct["email_verification_token"] = None
                migrated = True
            if "notifications" not in acct:
                acct["notifications"] = []
                migrated = True
            if "frozen" not in acct:
                acct["frozen"] = False
                migrated = True
            if "otp_code" not in acct:
                acct["otp_code"] = None
                migrated = True
            if "otp_expires_at" not in acct:
                acct["otp_expires_at"] = None
                migrated = True
            if "statement_requests" not in acct:
                acct["statement_requests"] = []
                migrated = True
            if "loan_requests" not in acct:
                acct["loan_requests"] = []
                migrated = True
            if "transfer_requests" not in acct:
                acct["transfer_requests"] = []
                migrated = True
            if "transactions" not in acct:
                acct["transactions"] = []
                migrated = True
            if "status" not in acct:
                acct["status"] = "Pending approval"
                migrated = True
        if migrated:
            try:
                with open(DATA_FILE, "w", encoding="utf-8") as wf:
                    json.dump(data, wf, indent=2)
            except Exception:
                pass
        return data


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


def generate_verification_token():
    return str(random.randint(100000, 999999))


def generate_otp_code():
    return str(random.randint(100000, 999999))


def append_notification(account, message):
    if "notifications" not in account:
        account["notifications"] = []
    account["notifications"].insert(0, {
        "message": message,
        "date": datetime.utcnow().isoformat(),
        "read": False
    })


def send_email(to_address, subject, body):
    if not to_address:
        print("Email not sent because recipient address is missing.")
        return False

    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    from_address = os.environ.get("EMAIL_FROM", "no-reply@cbkbank.com")

    message = EmailMessage()
    message["From"] = from_address
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    if smtp_server and smtp_user and smtp_password:
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(message)
            return True
        except Exception as e:
            print(f"Failed to send email to {to_address}: {e}")
            return False

    print("SMTP settings not configured; printing email to console instead.")
    print("--- EMAIL ---")
    print(f"To: {to_address}")
    print(f"Subject: {subject}")
    print(body)
    print("--- END EMAIL ---")
    return False


def generate_transaction_id():
    return f"TXN{random.randint(100000, 999999)}"


def generate_loan_id():
    return f"LOAN{random.randint(100000, 999999)}"


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
        email = request.form.get("email", "").strip()
        dob = request.form.get("dob", "").strip()
        kra_pin = request.form.get("kra_pin", "").strip()
        biometric = request.form.get("biometric", "").strip()
        mpin = request.form.get("mpin", "").strip()

        currency = request.form.get("currency", "KSH")
        if currency not in CURRENCIES:
            currency = "KSH"

        if not full_name or not id_number or not phone or not email or not dob or not kra_pin or not biometric or not mpin:
            flash("Please complete all required fields.", "error")
            return redirect(url_for("register"))

        if "@" not in email or "." not in email:
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("register"))

        if not mpin.isdigit() or len(mpin) != 4:
            flash("MPIN must be exactly 4 digits.", "error")
            return redirect(url_for("register"))

        account_number = generate_account_number(accounts)
        photo_file = save_file(request.files.get("photo"), "photo", account_number)
        id_front_file = save_file(request.files.get("id_front"), "id_front", account_number)
        id_back_file = save_file(request.files.get("id_back"), "id_back", account_number)
        kra_doc_file = save_file(request.files.get("kra_doc"), "kra_doc", account_number)
        verification_token = generate_verification_token()

        accounts[account_number] = {
            "account_number": account_number,
            "name": full_name,
            "id_type": id_type,
            "id_number": id_number,
            "phone": phone,
            "email": email,
            "dob": dob,
            "kra_pin": kra_pin,
            "kra_doc": kra_doc_file,
            "biometric": biometric,
            "mpin": mpin,
            "currency": currency,
            "balance": 0.0,
            "approved": False,
            "status": "Pending approval",
            "kyc_status": "Pending",
            "email_verified": False,
            "email_verification_token": verification_token,
            "notifications": [],
            "frozen": False,
            "transactions": [],
            "transfer_requests": [],
            "statement_requests": [],
            "loan_requests": [],
            "photo": photo_file,
            "id_front": id_front_file,
            "id_back": id_back_file,
            "created_at": datetime.utcnow().isoformat()
        }
        append_notification(accounts[account_number], "Account request submitted. Verify your email to enable login.")
        verification_url = url_for("verify_email", account_number=account_number, token=verification_token, _external=True)
        subject = "CBK Email Verification"
        body = (
            f"Dear {full_name},\n\n"
            "Thank you for registering with CBK. Please verify your email address using the link below:\n"
            f"{verification_url}\n\n"
            "Once your email is verified, the account will be ready for admin approval.\n"
            "Thank you.\n"
        )
        send_email(email, subject, body)
        save_accounts(accounts)
        flash("Your account request has been submitted. Please verify your email and wait for admin approval.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", currencies=CURRENCIES)


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

        if account.get("frozen"):
            flash("Your account has been frozen. Contact CBK support.", "error")
            return redirect(url_for("login"))

        if not account.get("approved", False):
            flash("Your account request is pending admin approval.", "error")
            return redirect(url_for("login"))

        if method == "otp":
            expires_at = account.get("otp_expires_at")
            valid_code = account.get("otp_code")
            if valid_code and expires_at:
                try:
                    expiry = datetime.fromisoformat(expires_at)
                except ValueError:
                    expiry = None
                if expiry and expiry > datetime.utcnow():
                    if credential == valid_code:
                        account["otp_code"] = None
                        account["otp_expires_at"] = None
                    else:
                        flash("Invalid OTP code. Please check your email.", "error")
                        save_accounts(accounts)
                        return redirect(url_for("login"))
                else:
                    valid_code = None
            if not valid_code:
                otp = generate_otp_code()
                account["otp_code"] = otp
                account["otp_expires_at"] = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
                append_notification(account, "Your OTP code has been sent to your email.")
                subject = "CBK OTP Verification"
                body = (
                    f"Dear {account['name']},\n\n"
                    f"Your OTP login code is: {otp}\n"
                    "This code is valid for 10 minutes.\n\n"
                    "Thank you for banking with CBK.\n"
                )
                send_email(account.get("email"), subject, body)
                save_accounts(accounts)
                flash("OTP sent to your email. Enter it in the login form now.", "info")
                return redirect(url_for("login"))
        elif method == "mpin":
            if credential != account.get("mpin"):
                flash("Invalid MPIN.", "error")
                return redirect(url_for("login"))
        else:
            if credential != account.get("biometric"):
                flash("Invalid biometric passphrase.", "error")
                return redirect(url_for("login"))

        save_accounts(accounts)
        session["account_number"] = account_number
        flash(f"Welcome back, {account['name']}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/verify_email/<account_number>/<token>")
def verify_email(account_number, token):
    accounts = load_accounts()
    account = accounts.get(account_number)
    if not account:
        flash("Invalid verification link.", "error")
        return redirect(url_for("login"))
    if account.get("email_verification_token") == token:
        account["email_verified"] = True
        account["email_verification_token"] = None
        if account.get("approved"):
            account["status"] = "Active"
        append_notification(account, "Your email has been verified.")
        save_accounts(accounts)
        flash("Email verified successfully. You can now log in.", "success")
        return redirect(url_for("login"))
    flash("Invalid or expired verification link.", "error")
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    account_number = session.get("account_number")
    if not account_number:
        return redirect(url_for("login"))

    accounts = load_accounts()
    account = accounts.get(account_number)
    if not account:
        return redirect(url_for("login"))

    pending_transfers = sum(
        req.get("amount", 0) for req in account.get("transfer_requests", []) if req.get("status") == "Pending"
    )
    account["available_balance"] = max(account.get("balance", 0.0) - pending_transfers, 0.0)
    account["currency_symbol"] = CURRENCIES.get(account.get("currency", "KSH"), "KES")

    loans = account.get("loan_requests", [])
    approved_loans = [loan for loan in loans if loan.get("status") == "Approved"]
    pending_loans = [loan for loan in loans if loan.get("status") == "Pending"]
    total_outstanding = sum(loan.get("amount", 0.0) for loan in approved_loans)
    next_payment = "N/A"
    if approved_loans:
        first_schedule = next((loan.get("repayment_schedule", [None])[0] for loan in approved_loans if loan.get("repayment_schedule")), None)
        if first_schedule:
            next_payment = first_schedule.get("due_date", "N/A")

    account["loan_summary"] = {
        "approved_count": len(approved_loans),
        "pending_count": len(pending_loans),
        "total_outstanding": f"{account['currency_symbol']}{total_outstanding:.2f}",
        "next_payment": next_payment
    }
    account["unread_notifications"] = len([note for note in account.get("notifications", []) if not note.get("read")])
    save_accounts(accounts)
    return render_template("dashboard.html", account=account, bank_list=BANKS)


@app.route("/logout")
def logout():
    session.pop("account_number", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/admin/deposit", methods=["GET", "POST"])
def admin_deposit():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    accounts = load_accounts()
    if request.method == "POST":
        account_number = request.form.get("account_number", "").strip()
        amount = request.form.get("amount", "0").strip()
        if account_number not in accounts:
            flash("Account number not found.", "error")
            return redirect(url_for("admin_deposit"))
        try:
            amount_value = float(amount)
            if amount_value <= 0:
                raise ValueError
        except ValueError:
            flash("Enter a valid deposit amount.", "error")
            return redirect(url_for("admin_deposit"))

        account = accounts[account_number]
        account["balance"] += amount_value
        account["transactions"].append({
            "type": "Deposit",
            "amount": amount_value,
            "balance": account["balance"],
            "date": datetime.utcnow().isoformat(),
            "approved_by": "admin"
        })
        save_accounts(accounts)
        subject = "CBK Deposit Notification"
        body = (
            f"Dear {account['name']},\n\n"
            f"KES {amount_value:.2f} has been deposited into your CBK account by the CBK admin.\n"
            f"Your new balance is KES {account['balance']:.2f}.\n\n"
            "Thank you for banking with CBK.\n"
        )
        send_email(account.get("email"), subject, body)
        flash(f"KES {amount_value:.2f} deposited to account {account_number}.", "success")
        return redirect(url_for("admin_deposit"))

    return render_template("admin_deposit.html", accounts=accounts)


@app.route("/admin/create_customer", methods=["GET", "POST"])
def admin_create_customer():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    accounts = load_accounts()
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        dob = request.form.get("dob", "").strip()
        id_type = request.form.get("id_type", "National ID")
        id_number = request.form.get("id_number", "").strip()
        phone = request.form.get("phone", "").strip()
        biometric = request.form.get("biometric", "").strip()
        mpin = request.form.get("mpin", "").strip()
        currency = request.form.get("currency", "KSH")
        if currency not in CURRENCIES:
            currency = "KSH"
        if not full_name or not email or not dob or not id_number or not phone or not biometric or not mpin:
            flash("Please complete all required fields.", "error")
            return redirect(url_for("admin_create_customer"))
        if not mpin.isdigit() or len(mpin) != 4:
            flash("MPIN must be exactly 4 digits.", "error")
            return redirect(url_for("admin_create_customer"))
        account_number = generate_account_number(accounts)
        
        # Handle optional document uploads
        photo_path = None
        id_front_path = None
        id_back_path = None
        
        if "photo" in request.files and request.files["photo"].filename:
            photo = request.files["photo"]
            if photo and photo.filename:
                ext = os.path.splitext(photo.filename)[1]
                photo_path = f"admin_photo_{account_number}_{int(datetime.utcnow().timestamp())}{ext}"
                photo.save(os.path.join(app.config["UPLOAD_FOLDER"], photo_path))
        
        if "id_front" in request.files and request.files["id_front"].filename:
            id_front = request.files["id_front"]
            if id_front and id_front.filename:
                ext = os.path.splitext(id_front.filename)[1]
                id_front_path = f"admin_id_front_{account_number}_{int(datetime.utcnow().timestamp())}{ext}"
                id_front.save(os.path.join(app.config["UPLOAD_FOLDER"], id_front_path))
        
        if "id_back" in request.files and request.files["id_back"].filename:
            id_back = request.files["id_back"]
            if id_back and id_back.filename:
                ext = os.path.splitext(id_back.filename)[1]
                id_back_path = f"admin_id_back_{account_number}_{int(datetime.utcnow().timestamp())}{ext}"
                id_back.save(os.path.join(app.config["UPLOAD_FOLDER"], id_back_path))
        
        accounts[account_number] = {
            "account_number": account_number,
            "name": full_name,
            "id_type": id_type,
            "id_number": id_number,
            "phone": phone,
            "email": email,
            "dob": dob,
            "kra_pin": "",
            "kra_doc": None,
            "biometric": biometric,
            "mpin": mpin,
            "currency": currency,
            "balance": 0.0,
            "available_balance": 0.0,
            "approved": True,
            "status": "Active",
            "kyc_status": "Verified",
            "email_verified": True,
            "email_verification_token": None,
            "notifications": [],
            "frozen": False,
            "transactions": [],
            "transfer_requests": [],
            "statement_requests": [],
            "loan_requests": [],
            "photo": photo_path,
            "id_front": id_front_path,
            "id_back": id_back_path,
            "created_at": datetime.utcnow().isoformat()
        }
        append_notification(accounts[account_number], "Your CBK account has been created by admin.")
        subject = "CBK Account Created"
        body = (
            f"Dear {full_name},\n\n"
            "Your CBK account has been created by CBK admin. You can now log in with your account number and MPIN.\n\n"
            "Thank you.\n"
        )
        send_email(email, subject, body)
        save_accounts(accounts)
        flash(f"Customer account {account_number} created successfully.", "success")
        return redirect(url_for("admin_create_customer"))
    return render_template("admin_create_account.html", currencies=CURRENCIES)


@app.route("/admin/settings", methods=["GET", "POST"])
def admin_settings():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    accounts = load_accounts()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "change_password":
            current = request.form.get("current_admin_password", "")
            new_password = request.form.get("new_admin_password", "")
            global ADMIN_PASSWORD
            if current != ADMIN_PASSWORD:
                flash("Current admin password is incorrect.", "error")
            elif not new_password:
                flash("Enter a new admin password.", "error")
            else:
                ADMIN_PASSWORD = new_password
                flash("Admin password updated successfully.", "success")
        elif action == "reset_customer_mpin":
            account_number = request.form.get("reset_mpin_account", "")
            new_mpin = request.form.get("new_customer_mpin", "")
            account = accounts.get(account_number)
            if not account:
                flash("Account not found.", "error")
            elif not new_mpin.isdigit() or len(new_mpin) != 4:
                flash("MPIN must be exactly 4 digits.", "error")
            else:
                account["mpin"] = new_mpin
                append_notification(account, "Your MPIN was reset by admin.")
                send_email(account.get("email"), "CBK MPIN Reset", f"Dear {account['name']},\n\nYour MPIN has been reset by CBK admin.\n\nThank you.\n")
                save_accounts(accounts)
                flash(f"MPIN for {account_number} has been reset.", "success")
    return render_template("admin_settings.html", accounts=accounts)


@app.route("/admin/reports")
def admin_reports():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    accounts = load_accounts()
    total_accounts = len(accounts)
    active_accounts = sum(1 for acct in accounts.values() if acct.get("approved") and acct.get("status") == "Active")
    pending_accounts = sum(1 for acct in accounts.values() if not acct.get("approved"))
    frozen_accounts = sum(1 for acct in accounts.values() if acct.get("frozen"))
    total_balance = sum(acct.get("balance", 0.0) for acct in accounts.values())
    loan_requests = [loan for acct in accounts.values() for loan in acct.get("loan_requests", [])]
    pending_loans = sum(1 for loan in loan_requests if loan.get("status") == "Pending")
    approved_loans = [loan for loan in loan_requests if loan.get("status") == "Approved"]
    rejected_loans = sum(1 for loan in loan_requests if loan.get("status") == "Rejected")
    outstanding_loans = sum(loan.get("amount", 0.0) for loan in approved_loans)
    recent_loans = sorted(
        [
            {
                "loan_id": loan["loan_id"],
                "account_number": acct["account_number"],
                "amount": loan["amount"],
                "currency_symbol": CURRENCIES.get(acct.get("currency", "KSH"), "KES"),
                "status": loan["status"],
                "repayment_term": f"{loan.get('term_months', 12)} months"
            }
            for acct in accounts.values() for loan in acct.get("loan_requests", []) if loan.get("status") == "Approved"
        ],
        key=lambda item: item["loan_id"],
        reverse=True
    )[:10]
    loan_eligibility_rate = round((len(approved_loans) / max(1, len(loan_requests))) * 100, 2)
    return render_template(
        "admin_reports.html",
        metrics={
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "pending_accounts": pending_accounts,
            "frozen_accounts": frozen_accounts,
            "total_balance": f"KES {total_balance:.2f}",
            "outstanding_loans": f"KES {outstanding_loans:.2f}",
            "pending_loans": pending_loans,
            "approved_loans": len(approved_loans),
            "rejected_loans": rejected_loans,
            "loan_eligibility_rate": loan_eligibility_rate,
            "recent_loans": recent_loans
        }
    )


@app.route("/admin/verify_kyc/<account_number>", methods=["POST"])
def admin_verify_kyc(account_number):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    accounts = load_accounts()
    account = accounts.get(account_number)
    if account:
        account["kyc_status"] = "Verified"
        if account.get("approved") and account.get("email_verified"):
            account["status"] = "Active"
        append_notification(account, "Your KYC verification is complete.")
        save_accounts(accounts)
        send_email(account.get("email"), "CBK KYC Verified", f"Dear {account['name']},\n\nYour KYC verification has been approved.\n\nThank you.\n")
        flash(f"KYC for {account_number} has been verified.", "success")
    else:
        flash("Account not found.", "error")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/reject_kyc/<account_number>", methods=["POST"])
def admin_reject_kyc(account_number):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    accounts = load_accounts()
    account = accounts.get(account_number)
    if account:
        account["kyc_status"] = "Rejected"
        account["status"] = "KYC Rejected"
        append_notification(account, "Your KYC verification has been rejected.")
        save_accounts(accounts)
        send_email(account.get("email"), "CBK KYC Rejected", f"Dear {account['name']},\n\nYour KYC verification has been rejected. Please contact CBK support.\n\nThank you.\n")
        flash(f"KYC for {account_number} has been rejected.", "info")
    else:
        flash("Account not found.", "error")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/freeze_account/<account_number>", methods=["POST"])
def admin_freeze_account(account_number):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    accounts = load_accounts()
    account = accounts.get(account_number)
    if account:
        account["frozen"] = True
        account["status"] = "Frozen"
        append_notification(account, "Your account has been frozen by admin.")
        save_accounts(accounts)
        send_email(account.get("email"), "CBK Account Frozen", f"Dear {account['name']},\n\nYour account has been frozen by CBK admin.\n\nThank you.\n")
        flash(f"Account {account_number} frozen.", "info")
    else:
        flash("Account not found.", "error")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/unfreeze_account/<account_number>", methods=["POST"])
def admin_unfreeze_account(account_number):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    accounts = load_accounts()
    account = accounts.get(account_number)
    if account:
        account["frozen"] = False
        account["status"] = "Active"
        append_notification(account, "Your account has been reactivated by admin.")
        save_accounts(accounts)
        send_email(account.get("email"), "CBK Account Reactivated", f"Dear {account['name']},\n\nYour account has been reactivated by CBK admin.\n\nThank you.\n")
        flash(f"Account {account_number} unfrozen.", "success")
    else:
        flash("Account not found.", "error")
    return redirect(url_for("admin_dashboard"))


@app.route("/notifications")
def notifications():
    account_number = session.get("account_number")
    if not account_number:
        return redirect(url_for("login"))
    accounts = load_accounts()
    account = accounts.get(account_number)
    for note in account.get("notifications", []):
        note["read"] = True
    save_accounts(accounts)
    account["currency_symbol"] = CURRENCIES.get(account.get("currency", "KSH"), "KES")
    return render_template("notifications.html", account=account)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    account_number = session.get("account_number")
    if not account_number:
        return redirect(url_for("login"))
    accounts = load_accounts()
    account = accounts.get(account_number)
    if request.method == "POST":
        current_mpin = request.form.get("current_mpin", "").strip()
        new_mpin = request.form.get("new_mpin", "").strip()
        confirm_mpin = request.form.get("confirm_mpin", "").strip()
        if current_mpin != account.get("mpin"):
            flash("Current MPIN is incorrect.", "error")
        elif new_mpin != confirm_mpin or not new_mpin.isdigit() or len(new_mpin) != 4:
            flash("New MPIN must match and be exactly 4 digits.", "error")
        else:
            account["mpin"] = new_mpin
            append_notification(account, "Your MPIN has been changed successfully.")
            save_accounts(accounts)
            flash("MPIN updated successfully.", "success")
    account["currency_symbol"] = CURRENCIES.get(account.get("currency", "KSH"), "KES")
    return render_template("settings.html", account=account)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("Admin logged out.", "info")
    return redirect(url_for("admin"))


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

    transaction_id = generate_transaction_id()
    transfer_request = {
        "transaction_id": transaction_id,
        "bank": bank,
        "destination_account": destination,
        "amount": amount_value,
        "status": "Pending",
        "requested_at": datetime.utcnow().isoformat()
    }
    account["transfer_requests"].append(transfer_request)
    save_accounts(accounts)

    subject = "CBK Transfer Request Received"
    body = (
        f"Dear {account['name']},\n\n"
        f"Your transfer request is currently being processed under Transaction ID: {transaction_id}.\n"
        "We will notify you once the transaction has been completed successfully.\n\n"
        "Thank you for banking with CBK.\n"
    )
    send_email(account.get("email"), subject, body)

    flash(f"Your transfer request is currently being processed under Transaction ID: {transaction_id}.", "success")
    return redirect(url_for("dashboard"))


@app.route("/profile")
def profile():
    account_number = session.get("account_number")
    if not account_number:
        return redirect(url_for("login"))
    accounts = load_accounts()
    account = accounts.get(account_number)
    if not account:
        flash("Account not found.", "error")
        return redirect(url_for("login"))
    account["currency_symbol"] = CURRENCIES.get(account.get("currency", "KSH"), "KES")
    return render_template("profile.html", account=account)


@app.route("/loan", methods=["GET", "POST"])
def loan():
    account_number = session.get("account_number")
    if not account_number:
        return redirect(url_for("login"))

    accounts = load_accounts()
    account = accounts.get(account_number)
    account["currency_symbol"] = CURRENCIES.get(account.get("currency", "KSH"), "KES")
    message = None
    success = False
    loan_calculation = None
    if request.method == "POST":
        action = request.form.get("action", "request")
        amount = request.form.get("loan_amount", "0").strip()
        term = request.form.get("loan_term", "12").strip()
        purpose = request.form.get("purpose", "").strip()
        try:
            loan_amount = float(amount)
            term_months = int(term)
            if loan_amount <= 0 or term_months <= 0:
                raise ValueError
        except ValueError:
            flash("Enter a valid loan amount and term.", "error")
            return redirect(url_for("loan"))

        monthly_rate = 0.12 / 12
        total_repayment = loan_amount * (1 + 0.12)
        monthly_payment = total_repayment / term_months
        loan_calculation = {
            "monthly_payment": monthly_payment,
            "total_repayment": total_repayment
        }

        if action == "calculate":
            message = f"Estimated monthly payment is {account['currency_symbol']}{monthly_payment:.2f}."
            success = True
        else:
            if account.get("kyc_status") != "Verified":
                flash("KYC verification is required to request a loan.", "error")
                return redirect(url_for("loan"))
            if loan_amount > account.get("balance", 0) * 5:
                flash("This loan amount exceeds your eligibility based on current balance.", "error")
                return redirect(url_for("loan"))

            loan_id = generate_loan_id()
            # build repayment schedule: monthly installments over term_months
            total_repayment_rounded = round(total_repayment, 2)
            installment_amount = round(monthly_payment, 2)
            # initialize schedule with equal installments, adjust last for rounding
            schedule = [installment_amount for _ in range(term_months)]
            sum_sched = round(sum(schedule), 2)
            if sum_sched != total_repayment_rounded:
                # adjust last installment
                schedule[-1] = round(total_repayment_rounded - round(sum(schedule[:-1]), 2), 2)

            repayment_schedule = []
            for i in range(1, term_months + 1):
                due_date = (datetime.utcnow() + timedelta(days=30 * i)).date().isoformat()
                repayment_schedule.append({
                    "installment_no": i,
                    "due_date": due_date,
                    "amount": schedule[i - 1],
                    "paid": False
                })

            loan_request = {
                "loan_id": loan_id,
                "amount": loan_amount,
                "purpose": purpose,
                "status": "Pending",
                "requested_at": datetime.utcnow().isoformat(),
                "term_months": term_months,
                "monthly_payment": round(monthly_payment, 2),
                "repayment_schedule": repayment_schedule
            }
            if "loan_requests" not in account:
                account["loan_requests"] = []
            account["loan_requests"].append(loan_request)
            save_accounts(accounts)

            subject = "CBK Loan Request Received"
            body = (
                f"Dear {account['name']},\n\n"
                f"Your loan request for {account['currency_symbol']}{loan_amount:.2f} has been received and is pending admin approval.\n"
                f"Loan Request ID: {loan_id}\n\n"
                "Thank you for banking with CBK.\n"
            )
            send_email(account.get("email"), subject, body)
            append_notification(account, f"Loan request {loan_id} submitted and pending approval.")
            save_accounts(accounts)
            message = f"Loan request submitted and is pending approval (ID: {loan_id})."
            success = True

    return render_template("loan.html", account=account, message=message, success=success, loan_calculation=loan_calculation)


@app.route("/statement", methods=["GET", "POST"])
def statement():
    account_number = session.get("account_number")
    if not account_number:
        return redirect(url_for("login"))

    accounts = load_accounts()
    account = accounts.get(account_number)
    account["currency_symbol"] = CURRENCIES.get(account.get("currency", "KSH"), "KES")
    message = None
    statement_transactions = []
    if request.method == "POST":
        start_date = request.form.get("start_date", "").strip()
        end_date = request.form.get("end_date", "").strip()
        if not start_date or not end_date:
            flash("Please select both start and end dates for the statement.", "error")
            return redirect(url_for("statement"))

        if "statement_requests" not in account:
            account["statement_requests"] = []
        request_record = {
            "start_date": start_date,
            "end_date": end_date,
            "requested_at": datetime.utcnow().isoformat(),
            "status": "Pending"
        }
        account["statement_requests"].append(request_record)
        save_accounts(accounts)
        statement_transactions = [
            tx for tx in account.get("transactions", [])
            if start_date <= tx.get("date", "")[:10] <= end_date
        ]
        message = f"Statement request submitted for {start_date} to {end_date}."

    return render_template(
        "statement.html",
        account=account,
        message=message,
        statement_transactions=statement_transactions
    )


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
    pending_accounts = [acct for acct in accounts.values() if not acct.get("approved", False)]
    pending_transfers = []
    pending_loans = []
    pending_kyc = [acct for acct in accounts.values() if acct.get("kyc_status") == "Pending"]
    for acct in accounts.values():
        for req in acct.get("transfer_requests", []):
            if req.get("status") == "Pending":
                pending_transfers.append({
                    "account_number": acct["account_number"],
                    "name": acct["name"],
                    "currency_symbol": CURRENCIES.get(acct.get("currency", "KSH"), "KES"),
                    **req
                })
        for lr in acct.get("loan_requests", []):
            if lr.get("status") == "Pending":
                pending_loans.append({
                    "account_number": acct["account_number"],
                    "name": acct["name"],
                    "currency_symbol": CURRENCIES.get(acct.get("currency", "KSH"), "KES"),
                    **lr
                })
    for acct in accounts.values():
        acct["currency_symbol"] = CURRENCIES.get(acct.get("currency", "KSH"), "KES")
    return render_template(
        "admin_dashboard.html",
        accounts=accounts,
        pending_accounts=pending_accounts,
        pending_transfers=pending_transfers,
        pending_loans=pending_loans,
        pending_kyc=pending_kyc
    )


@app.route("/admin/view_documents/<account_number>")
def admin_view_documents(account_number):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    accounts = load_accounts()
    account = accounts.get(account_number)
    if not account:
        flash("Account not found.", "error")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_view_documents.html", account=account)


@app.route("/admin/approve_account/<account_number>", methods=["POST"])
def admin_approve_account(account_number):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    accounts = load_accounts()
    account = accounts.get(account_number)
    if not account:
        flash("Account not found.", "error")
        return redirect(url_for("admin_dashboard"))
    account["approved"] = True
    account["status"] = "Active"
    save_accounts(accounts)
    subject = "CBK Account Approved"
    body = (
        f"Dear {account['name']},\n\n"
        "Your CBK account has been approved by admin and is now active.\n"
        f"Your account number is {account['account_number']}.\n\n"
        "Thank you for joining CBK.\n"
    )
    send_email(account.get("email"), subject, body)
    flash(f"Account {account_number} approved.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/reject_account/<account_number>", methods=["POST"])
def admin_reject_account(account_number):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    accounts = load_accounts()
    account = accounts.get(account_number)
    if not account:
        flash("Account not found.", "error")
        return redirect(url_for("admin_dashboard"))
    account["approved"] = False
    account["status"] = "Rejected"
    save_accounts(accounts)
    subject = "CBK Account Request Rejected"
    body = (
        f"Dear {account['name']},\n\n"
        "Your CBK account request has been rejected by admin.\n"
        "Please contact support for more details.\n\n"
        "Thank you.\n"
    )
    send_email(account.get("email"), subject, body)
    flash(f"Account {account_number} rejected.", "info")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/approve_transfer/<account_number>/<transaction_id>", methods=["POST"])
def admin_approve_transfer(account_number, transaction_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    accounts = load_accounts()
    account = accounts.get(account_number)
    if not account:
        flash("Account not found.", "error")
        return redirect(url_for("admin_dashboard"))
    for req in account.get("transfer_requests", []):
        if req.get("transaction_id") == transaction_id and req.get("status") == "Pending":
            if req["amount"] > account["balance"]:
                req["status"] = "Rejected"
                req["rejected_at"] = datetime.utcnow().isoformat()
                save_accounts(accounts)
                subject = "CBK Transfer Request Rejected"
                body = (
                    f"Dear {account['name']},\n\n"
                    f"Your transfer request {transaction_id} was rejected due to insufficient balance.\n"
                    "Please review your account and try again.\n\n"
                    "Thank you.\n"
                )
                send_email(account.get("email"), subject, body)
                flash(f"Transfer {transaction_id} rejected.", "info")
                return redirect(url_for("admin_dashboard"))

            account["balance"] -= req["amount"]
            req["status"] = "Completed"
            req["processed_at"] = datetime.utcnow().isoformat()
            account["transactions"].append({
                "type": "Transfer",
                "bank": req["bank"],
                "destination_account": req["destination_account"],
                "amount": req["amount"],
                "balance": account["balance"],
                "date": datetime.utcnow().isoformat(),
                "transaction_id": transaction_id,
                "approved_by": "admin"
            })
            save_accounts(accounts)
            subject = "CBK Transfer Completed"
            body = (
                f"Dear {account['name']},\n\n"
                f"Your transfer request {transaction_id} has been approved and completed.\n"
                f"KES {req['amount']:.2f} was sent to {req['bank']} account {req['destination_account']}.\n"
                f"Remaining balance is KES {account['balance']:.2f}.\n\n"
                "Thank you for banking with CBK.\n"
            )
            send_email(account.get("email"), subject, body)
            flash(f"Transfer {transaction_id} approved and completed.", "success")
            return redirect(url_for("admin_dashboard"))
    flash("Transfer request not found.", "error")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/reject_transfer/<account_number>/<transaction_id>", methods=["POST"])
def admin_reject_transfer(account_number, transaction_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    accounts = load_accounts()
    account = accounts.get(account_number)
    if not account:
        flash("Account not found.", "error")
        return redirect(url_for("admin_dashboard"))
    for req in account.get("transfer_requests", []):
        if req.get("transaction_id") == transaction_id and req.get("status") == "Pending":
            req["status"] = "Rejected"
            req["rejected_at"] = datetime.utcnow().isoformat()
            save_accounts(accounts)
            subject = "CBK Transfer Request Rejected"
            body = (
                f"Dear {account['name']},\n\n"
                f"Your transfer request {transaction_id} has been rejected by admin.\n"
                "Please contact support for help.\n\n"
                "Thank you.\n"
            )
            send_email(account.get("email"), subject, body)
            flash(f"Transfer {transaction_id} rejected.", "info")
            return redirect(url_for("admin_dashboard"))
    flash("Transfer request not found.", "error")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/approve_loan/<account_number>/<loan_id>", methods=["POST"])
def admin_approve_loan(account_number, loan_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    accounts = load_accounts()
    account = accounts.get(account_number)
    if not account:
        flash("Account not found.", "error")
        return redirect(url_for("admin_dashboard"))
    for lr in account.get("loan_requests", []):
        if lr.get("loan_id") == loan_id and lr.get("status") == "Pending":
            lr["status"] = "Approved"
            lr["processed_at"] = datetime.utcnow().isoformat()
            # Optionally credit loan amount
            account["balance"] += lr["amount"]
            account["transactions"].append({
                "type": "Loan",
                "amount": lr["amount"],
                "balance": account["balance"],
                "date": datetime.utcnow().isoformat(),
                "loan_id": loan_id,
                "approved_by": "admin"
            })
            save_accounts(accounts)
            subject = "CBK Loan Approved"
            body = (
                f"Dear {account['name']},\n\n"
                f"Your loan request {loan_id} for KES {lr['amount']:.2f} has been approved by CBK admin.\n"
                f"Your new balance is KES {account['balance']:.2f}.\n\n"
                "Thank you for banking with CBK.\n"
            )
            send_email(account.get("email"), subject, body)
            flash(f"Loan {loan_id} approved and funds credited.", "success")
            return redirect(url_for("admin_dashboard"))
    flash("Loan request not found.", "error")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/reject_loan/<account_number>/<loan_id>", methods=["POST"])
def admin_reject_loan(account_number, loan_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    accounts = load_accounts()
    account = accounts.get(account_number)
    if not account:
        flash("Account not found.", "error")
        return redirect(url_for("admin_dashboard"))
    for lr in account.get("loan_requests", []):
        if lr.get("loan_id") == loan_id and lr.get("status") == "Pending":
            lr["status"] = "Rejected"
            lr["rejected_at"] = datetime.utcnow().isoformat()
            save_accounts(accounts)
            subject = "CBK Loan Request Rejected"
            body = (
                f"Dear {account['name']},\n\n"
                f"Your loan request {loan_id} has been rejected by CBK admin.\n"
                "Please contact support for more information.\n\n"
                "Thank you.\n"
            )
            send_email(account.get("email"), subject, body)
            flash(f"Loan {loan_id} rejected.", "info")
            return redirect(url_for("admin_dashboard"))
    flash("Loan request not found.", "error")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete_account/<account_number>", methods=["POST"])
def admin_delete_account(account_number):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    accounts = load_accounts()
    if account_number not in accounts:
        flash("Account not found.", "error")
        return redirect(url_for("admin_dashboard"))
    del accounts[account_number]
    save_accounts(accounts)
    flash(f"Account {account_number} deleted.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/withdraw", methods=["GET", "POST"])
def admin_withdraw():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    accounts = load_accounts()
    if request.method == "POST":
        account_number = request.form.get("account_number", "").strip()
        amount = request.form.get("amount", "0").strip()
        if account_number not in accounts:
            flash("Account number not found.", "error")
            return redirect(url_for("admin_withdraw"))
        try:
            amount_value = float(amount)
            if amount_value <= 0:
                raise ValueError
        except ValueError:
            flash("Enter a valid withdraw amount.", "error")
            return redirect(url_for("admin_withdraw"))

        account = accounts[account_number]
        if amount_value > account["balance"]:
            flash("Insufficient balance for this withdrawal.", "error")
            return redirect(url_for("admin_withdraw"))

        account["balance"] -= amount_value
        account["transactions"].append({
            "type": "Admin Withdrawal",
            "amount": amount_value,
            "balance": account["balance"],
            "date": datetime.utcnow().isoformat(),
            "processed_by": "admin"
        })
        save_accounts(accounts)
        subject = "CBK Account Debit Notification"
        body = (
            f"Dear {account['name']},\n\n"
            f"KES {amount_value:.2f} has been debited from your CBK account by CBK admin.\n"
            f"Your new balance is KES {account['balance']:.2f}.\n\n"
            "Thank you for banking with CBK.\n"
        )
        send_email(account.get("email"), subject, body)
        flash(f"KES {amount_value:.2f} withdrawn from account {account_number}.", "success")
        return redirect(url_for("admin_withdraw"))

    return render_template("admin_withdraw.html", accounts=accounts)


@app.route("/reset_mpin", methods=["GET", "POST"])
def reset_mpin():
    if request.method == "POST":
        account_number = request.form.get("account_number", "").strip()
        email = request.form.get("email", "").strip()
        new_mpin = request.form.get("new_mpin", "").strip()
        confirm_mpin = request.form.get("confirm_mpin", "").strip()
        accounts = load_accounts()
        account = accounts.get(account_number)
        if not account:
            flash("Account not found.", "error")
            return redirect(url_for("reset_mpin"))
        if account.get("email") != email:
            flash("Email does not match our records.", "error")
            return redirect(url_for("reset_mpin"))
        if not new_mpin.isdigit() or len(new_mpin) != 4 or new_mpin != confirm_mpin:
            flash("MPINs must match and be exactly 4 digits.", "error")
            return redirect(url_for("reset_mpin"))
        account["mpin"] = new_mpin
        save_accounts(accounts)
        subject = "CBK MPIN Reset"
        body = (
            f"Dear {account['name']},\n\n"
            "Your MPIN has been successfully reset. If you did not request this, contact CBK support immediately.\n\n"
            "Thank you.\n"
        )
        send_email(account.get("email"), subject, body)
        flash("MPIN successfully reset.", "success")
        return redirect(url_for("login"))
    return render_template("reset_mpin.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
