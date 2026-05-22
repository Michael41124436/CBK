# CBK Banking System Web App

A simple CBK banking system built with Python and Flask.

## Features

- CBK branded landing page
- Create account with:
  - Full name
  - National ID or Passport information
  - Phone number
  - Biometric phrase
  - 4-digit MPIN
  - Profile photo upload
  - ID front/back upload
  - Passport front/back upload
- User login using MPIN or biometric phrase
- Dashboard with:
  - Balance display
  - Deposit funds
  - Transfer to 19 Kenyan banks
  - Recent transactions
  - Profile view
  - Loan request page
  - About and Contact pages
- Admin login and account overview

## Bank list supported

- KCB Bank Kenya
- Equity Bank Kenya
- Co-operative Bank of Kenya
- NCBA Bank Kenya
- Absa Bank Kenya
- I&M Bank
- Standard Chartered Bank Kenya
- Stanbic Bank Kenya
- Diamond Trust Bank Kenya
- Family Bank
- National Bank of Kenya
- Sidian Bank
- Prime Bank
- Ecobank Kenya
- Kingdom Bank
- Credit Bank
- UBA Kenya Bank
- Gulf African Bank
- DIB Bank Kenya

## Run locally

1. Install Python 3.
2. Install Flask:

```bash
pip install flask
```

3. Run the app:

```bash
python app.py
```

4. Open http://127.0.0.1:5000 in your browser.

## Deploy on Render

1. Push this repository to GitHub.
2. In Render, create a new Web Service and connect your GitHub repo.
3. Set the build command to:

```bash
pip install -r requirements.txt
```

4. Set the start command to:

```bash
python app.py
```

5. Choose the Python environment and deploy.

Render will use the `PORT` environment variable automatically, and the app is configured to bind to `0.0.0.0`.

## Admin credentials

- Username: `admin`
- Password: `cbkadmin123`

## Notes

- Uploaded images are saved in the `uploads/` folder.
- Account data is stored in `accounts.json`.
- The web app shows everything on login: profile, balance, transfers, loans, and support pages.
