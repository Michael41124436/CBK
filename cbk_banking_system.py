import json
import os
import random
import sys
import getpass

DATA_FILE = "accounts.json"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "cbkadmin123"
BANKS = ["NCBA", "Equity", "Coopbank", "Absa", "Trust Bank"]


def load_accounts():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_accounts(accounts):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2)


def generate_account_number(accounts):
    while True:
        account_number = str(random.randint(10**9, 10**10 - 1))
        if account_number not in accounts:
            return account_number


def pause():
    input("\nPress Enter to continue...")


def welcome():
    print("\n" + "=" * 40)
    print("              WELCOME TO CBK")
    print("=" * 40)
    print("Central Banking System (CBK)")
    print("1. Create a new account")
    print("2. User login")
    print("3. Admin login")
    print("4. Exit")


def create_account(accounts):
    print("\n--- Create a new CBK account ---")
    name = input("Full name: ").strip()
    while not name:
        name = input("Full name cannot be empty. Please enter your name: ").strip()

    id_type = ""
    while id_type not in ["1", "2"]:
        print("Choose ID type:")
        print("1. National ID")
        print("2. Passport")
        id_type = input("Enter 1 or 2: ").strip()
    id_label = "National ID" if id_type == "1" else "Passport"
    id_number = input(f"{id_label} number: ").strip()
    while not id_number:
        id_number = input(f"{id_label} number is required: ").strip()

    phone = input("Phone number: ").strip()
    while not phone:
        phone = input("Phone number is required: ").strip()

    print("\nSet biometric passphrase for login.")
    print("This is a unique biometric password phrase you will use for biometric login.")
    biometric = input("Enter your biometric phrase: ").strip()
    while not biometric:
        biometric = input("Biometric phrase is required: ").strip()

    pin = getpass.getpass("Set a 4-digit MPIN: ").strip()
    while not (pin.isdigit() and len(pin) == 4):
        pin = getpass.getpass("MPIN must be exactly 4 digits. Try again: ").strip()

    account_number = generate_account_number(accounts)
    accounts[account_number] = {
        "name": name,
        "id_type": id_label,
        "id_number": id_number,
        "phone": phone,
        "biometric": biometric,
        "mpin": pin,
        "balance": 0.0,
        "transactions": []
    }
    save_accounts(accounts)
    print(f"\nAccount created successfully! Your CBK account number is: {account_number}")
    print("Use this number with MPIN or biometric login.")
    pause()


def user_login(accounts):
    print("\n--- User Login ---")
    account_number = input("Account number: ").strip()
    if account_number not in accounts:
        print("Account not found.")
        pause()
        return
    print("Login method:")
    print("1. MPIN")
    print("2. Biometric")
    method = input("Choose 1 or 2: ").strip()
    if method == "1":
        pin = getpass.getpass("Enter MPIN: ").strip()
        if pin != accounts[account_number]["mpin"]:
            print("Invalid MPIN.")
            pause()
            return
    elif method == "2":
        biometric = input("Enter biometric phrase: ").strip()
        if biometric != accounts[account_number]["biometric"]:
            print("Invalid biometric phrase.")
            pause()
            return
    else:
        print("Invalid login method.")
        pause()
        return
    print(f"\nWelcome back, {accounts[account_number]['name']}!")
    user_menu(accounts, account_number)


def admin_login(accounts):
    print("\n--- Admin Login ---")
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ").strip()
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        print("Invalid admin credentials.")
        pause()
        return
    print("\nAdmin access granted.")
    admin_menu(accounts)


def user_menu(accounts, account_number):
    while True:
        account = accounts[account_number]
        print("\n--- CBK User Dashboard ---")
        print(f"Hello, {account['name']} | Balance: KES {account['balance']:.2f}")
        print("1. View account details")
        print("2. Deposit funds")
        print("3. Transfer / Withdraw to another bank")
        print("4. View transaction history")
        print("5. Logout")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            display_account_details(account_number, account)
        elif choice == "2":
            deposit_funds(accounts, account_number)
        elif choice == "3":
            transfer_to_bank(accounts, account_number)
        elif choice == "4":
            show_transactions(account)
        elif choice == "5":
            print("Logging out...")
            pause()
            break
        else:
            print("Invalid option.")


def display_account_details(account_number, account):
    print("\n--- Account Details ---")
    print(f"Account Number: {account_number}")
    print(f"Name: {account['name']}")
    print(f"ID Type: {account['id_type']}")
    print(f"ID Number: {account['id_number']}")
    print(f"Phone: {account['phone']}")
    print(f"Balance: KES {account['balance']:.2f}")
    pause()


def deposit_funds(accounts, account_number):
    amount_str = input("Enter amount to deposit: KES ").strip()
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("Invalid amount.")
        pause()
        return
    accounts[account_number]["balance"] += amount
    accounts[account_number]["transactions"].append({
        "type": "Deposit",
        "amount": amount,
        "balance": accounts[account_number]["balance"]
    })
    save_accounts(accounts)
    print(f"Deposit successful. New balance: KES {accounts[account_number]['balance']:.2f}")
    pause()


def transfer_to_bank(accounts, account_number):
    account = accounts[account_number]
    print("\n--- Transfer / Withdraw to another bank ---")
    for idx, bank in enumerate(BANKS, start=1):
        print(f"{idx}. {bank}")
    choice = input("Select destination bank: ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(BANKS)):
        print("Invalid bank selection.")
        pause()
        return
    bank_name = BANKS[int(choice) - 1]
    target_account = input(f"Enter destination account number at {bank_name}: ").strip()
    if not target_account:
        print("Destination account number is required.")
        pause()
        return
    amount_str = input("Enter amount to transfer: KES ").strip()
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("Invalid amount.")
        pause()
        return
    if amount > account["balance"]:
        print("Insufficient funds.")
        pause()
        return
    account["balance"] -= amount
    account["transactions"].append({
        "type": "Bank Transfer",
        "bank": bank_name,
        "destination_account": target_account,
        "amount": amount,
        "balance": account["balance"]
    })
    save_accounts(accounts)
    print(f"Successfully transferred KES {amount:.2f} to {bank_name} account {target_account}.")
    print(f"Remaining balance: KES {account['balance']:.2f}")
    pause()


def show_transactions(account):
    print("\n--- Transaction History ---")
    if not account["transactions"]:
        print("No transactions yet.")
    else:
        for idx, tx in enumerate(account["transactions"], start=1):
            if tx["type"] == "Deposit":
                print(f"{idx}. Deposit KES {tx['amount']:.2f} | Balance: KES {tx['balance']:.2f}")
            else:
                print(f"{idx}. Transfer to {tx['bank']} {tx['destination_account']} | KES {tx['amount']:.2f} | Balance: KES {tx['balance']:.2f}")
    pause()


def admin_menu(accounts):
    while True:
        print("\n--- CBK Admin Dashboard ---")
        print("1. View all accounts")
        print("2. Search account by number")
        print("3. Delete an account")
        print("4. Reset a user MPIN")
        print("5. Logout")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            list_accounts(accounts)
        elif choice == "2":
            search_account(accounts)
        elif choice == "3":
            delete_account(accounts)
        elif choice == "4":
            reset_user_mpin(accounts)
        elif choice == "5":
            print("Admin logout...")
            pause()
            break
        else:
            print("Invalid option.")


def list_accounts(accounts):
    print("\n--- CBK Accounts ---")
    if not accounts:
        print("No accounts registered yet.")
    else:
        for acc_num, info in accounts.items():
            print(f"{acc_num} | {info['name']} | Balance: KES {info['balance']:.2f} | ID: {info['id_number']}")
    pause()


def search_account(accounts):
    account_number = input("Enter account number to search: ").strip()
    if account_number not in accounts:
        print("Account not found.")
    else:
        display_account_details(account_number, accounts[account_number])
    pause()


def delete_account(accounts):
    account_number = input("Enter account number to delete: ").strip()
    if account_number not in accounts:
        print("Account not found.")
        pause()
        return
    confirm = input(f"Are you sure you want to delete account {account_number}? (yes/no): ").strip().lower()
    if confirm == "yes":
        del accounts[account_number]
        save_accounts(accounts)
        print("Account deleted.")
    else:
        print("Deletion canceled.")
    pause()


def reset_user_mpin(accounts):
    account_number = input("Enter account number to reset MPIN: ").strip()
    if account_number not in accounts:
        print("Account not found.")
        pause()
        return
    new_pin = getpass.getpass("Enter new 4-digit MPIN: ").strip()
    while not (new_pin.isdigit() and len(new_pin) == 4):
        new_pin = getpass.getpass("MPIN must be exactly 4 digits. Try again: ").strip()
    accounts[account_number]["mpin"] = new_pin
    save_accounts(accounts)
    print("User MPIN has been reset.")
    pause()


def main():
    accounts = load_accounts()
    while True:
        welcome()
        choice = input("Choose an option: ").strip()
        if choice == "1":
            create_account(accounts)
        elif choice == "2":
            user_login(accounts)
        elif choice == "3":
            admin_login(accounts)
        elif choice == "4":
            print("Thank you for using CBK. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid option. Please enter a number from 1 to 4.")
            pause()


if __name__ == "__main__":
    main()
