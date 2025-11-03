from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime

# Replace with your actual Google Sheet ID (from the URL)
SHEET_ID = "1AhONVUmXWfo13-Ph29XydEewHlrSispovUcyuftUus4"
WORKSHEET_NAME = "Sheet1"  # Change if your tab has another name

# Auth
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
CREDS_FILE = "gspread_credentials.json"

creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)

# Open sheet
sh = gc.open_by_key(SHEET_ID)
ws = sh.worksheet(WORKSHEET_NAME)

# Test write
ws.append_row(["Test OK", datetime.now().isoformat(timespec="seconds")],
              value_input_option="USER_ENTERED")

print("Wrote a test row successfully.")
