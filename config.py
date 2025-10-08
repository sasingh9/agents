# Configuration settings for the Fund Setup Agent

# Try to import the secrets. If the file doesn't exist or is missing keys,
# provide a helpful message.
try:
    from secrets import OPENAI_API_KEY, GMAIL_APP_PASSWORD, API_PASSWORD
    # Check if the placeholder values have been changed
    if "YOUR_" in OPENAI_API_KEY or "YOUR_" in GMAIL_APP_PASSWORD or "YOUR_" in API_PASSWORD:
        print("WARNING: One or more secret values in `secrets.py` still use placeholder values.")
except ImportError:
    print("ERROR: `secrets.py` file not found or is missing required secrets.")
    print("Please create it by copying `secrets.py.example` and adding your secret values.")
    # Set to None so the application can fail gracefully later.
    OPENAI_API_KEY, GMAIL_APP_PASSWORD, API_PASSWORD = None, None, None

# IMAP settings for Gmail
IMAP_SERVER = "imap.gmail.com"
GMAIL_USERNAME = "sangharshsingh@gmail.com"

# Email search criteria
EMAIL_SENDER = "ssingh9@gmail.com"
EMAIL_SUBJECT = "Fund Setup Request"

# Backend API settings
API_BASE_URL = "http://localhost:8080/api"
API_USERNAME = "user"