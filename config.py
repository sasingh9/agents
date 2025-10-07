# Configuration settings for the Fund Setup Agent

# Gmail API settings
GMAIL_SENDER = "ssingh9@gmail.com"
GMAIL_RECIPIENT = "sangharshsingh@gmail.com"
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
GMAIL_CREDENTIALS_FILE = "credentials.json"
GMAIL_TOKEN_FILE = "token.json"

# OpenAI API settings
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"  # It's better to use environment variables for this

# Backend API settings
API_BASE_URL = "http://localhost:8080/api" # Assuming the backend runs on port 8080
API_USERNAME = "user" # Replace with actual username if needed
# The API password will be prompted for at runtime for security.

# Email search query
EMAIL_SEARCH_QUERY = "from:ssingh9@gmail.com subject:'Fund Setup Request'"