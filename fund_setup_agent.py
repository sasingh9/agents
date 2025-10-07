import json
import config
from email_reader import get_gmail_service, search_emails, get_email_body
from llm_parser import extract_fund_details_with_llm
from api_client import FundAPIClient
import os

PROCESSED_EMAILS_FILE = "processed_emails.json"

def load_processed_emails():
    """Loads the set of processed email IDs from a file."""
    if not os.path.exists(PROCESSED_EMAILS_FILE):
        return set()
    with open(PROCESSED_EMAILS_FILE, 'r') as f:
        try:
            return set(json.load(f))
        except json.JSONDecodeError:
            return set()

def save_processed_email(email_id):
    """Adds a processed email ID to the set and saves it."""
    processed_emails = load_processed_emails()
    processed_emails.add(email_id)
    with open(PROCESSED_EMAILS_FILE, 'w') as f:
        json.dump(list(processed_emails), f)

def main():
    """Main orchestration logic for the Fund Setup Agent."""
    print("--- Fund Setup Agent Initializing ---")

    # Load the list of already processed emails
    processed_emails = load_processed_emails()
    print(f"Loaded {len(processed_emails)} processed email IDs.")

    try:
        # 1. Connect to Gmail
        print("\nStep 1: Connecting to Gmail...")
        gmail_service = get_gmail_service()
        if not gmail_service:
            print("Failed to connect to Gmail. Exiting.")
            return
        print("Successfully connected to Gmail.")

        # 2. Initialize API Client (prompts for password)
        print("\nStep 2: Initializing API Client...")
        api_client = FundAPIClient(config.API_BASE_URL, config.API_USERNAME)
        print("API Client initialized.")

    except Exception as e:
        print(f"Failed during initialization: {e}")
        return

    # 3. Search for new fund setup emails
    print(f"\nStep 3: Searching for emails with query: '{config.EMAIL_SEARCH_QUERY}'")
    emails = search_emails(gmail_service, config.EMAIL_SEARCH_QUERY)

    if not emails:
        print("No new fund setup emails found.")
        print("\n--- Agent finished ---")
        return

    print(f"Found {len(emails)} emails matching the query.")

    new_emails = [email for email in emails if email['id'] not in processed_emails]
    if not new_emails:
        print("No new, unprocessed emails found.")
        print("\n--- Agent finished ---")
        return

    print(f"Found {len(new_emails)} new emails to process.")

    # 4. Process each new email
    for i, email_summary in enumerate(new_emails):
        email_id = email_summary['id']
        print(f"\n--- Processing email {i+1}/{len(new_emails)} (ID: {email_id}) ---")

        # Get email body
        email_body = get_email_body(gmail_service, email_id)
        if not email_body:
            print(f"Could not retrieve body for email ID {email_id}. Skipping.")
            continue

        # Extract details using LLM
        print("Extracting fund details using LLM...")
        try:
            fund_details = extract_fund_details_with_llm(email_body)
            if not fund_details or not fund_details.get('fundID'):
                print("Failed to extract fund details or fundID is missing. Skipping.")
                continue
            print("Successfully extracted fund details:")
            print(json.dumps(fund_details, indent=2))
        except ValueError as e:
            print(f"LLM parsing error: {e}. Check your OpenAI key in config.py. Skipping.")
            continue
        except Exception as e:
            print(f"An unexpected error occurred during LLM parsing: {e}. Skipping.")
            continue

        # Check if fund exists and create/update
        fund_id = fund_details['fundID']
        try:
            print(f"Checking if fund '{fund_id}' already exists...")
            existing_fund = api_client.get_fund(fund_id)

            if existing_fund:
                print(f"Fund '{fund_id}' found. Updating existing record.")
                api_client.update_fund(fund_id, fund_details)
                print(f"Successfully updated fund '{fund_id}'.")
            else:
                print(f"Fund '{fund_id}' not found. Creating new record.")
                api_client.create_fund(fund_details)
                print(f"Successfully created fund '{fund_id}'.")

            # Mark email as processed
            save_processed_email(email_id)
            print(f"Marked email {email_id} as processed.")

        except Exception as e:
            print(f"An error occurred while interacting with the API for fund '{fund_id}': {e}")
            print("Skipping this email and continuing to the next one.")

    print("\n--- Agent finished processing all new emails ---")


if __name__ == "__main__":
    # Add a check for the credentials file to guide the user.
    if not os.path.exists('credentials.json'):
        print("ERROR: `credentials.json` not found.")
        print("Please follow the setup instructions in `README.md` to get your credentials file from Google Cloud.")
    else:
        main()