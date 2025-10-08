import json
import os
import config
from email_reader import connect_to_gmail, search_emails_imap, get_email_body_and_message_id
from llm_parser import extract_fund_details_with_llm
from api_client import FundAPIClient

PROCESSED_MESSAGES_FILE = "processed_message_ids.json"

def load_processed_message_ids():
    """Loads the set of processed Message-IDs from a file."""
    if not os.path.exists(PROCESSED_MESSAGES_FILE):
        return set()
    with open(PROCESSED_MESSAGES_FILE, 'r') as f:
        try:
            return set(json.load(f))
        except json.JSONDecodeError:
            return set()

def save_processed_message_id(message_id):
    """Adds a processed Message-ID to the set and saves it."""
    processed_ids = load_processed_message_ids()
    processed_ids.add(message_id)
    with open(PROCESSED_MESSAGES_FILE, 'w') as f:
        json.dump(list(processed_ids), f)

def main():
    """Main orchestration logic for the Fund Setup Agent."""
    print("--- Fund Setup Agent Initializing ---")

    # Load the list of already processed emails
    processed_message_ids = load_processed_message_ids()
    print(f"Loaded {len(processed_message_ids)} processed Message-IDs.")

    mail_server = None
    try:
        # 1. Connect to Gmail via IMAP (prompts for App Password)
        print("\nStep 1: Connecting to Gmail via IMAP...")
        mail_server = connect_to_gmail()
        if not mail_server:
            print("Failed to connect to Gmail. Exiting.")
            return
        print("Successfully connected to Gmail.")

        # 2. Initialize API Client (prompts for API password)
        print("\nStep 2: Initializing API Client...")
        api_client = FundAPIClient(config.API_BASE_URL, config.API_USERNAME)
        print("API Client initialized.")

    except Exception as e:
        print(f"Failed during initialization: {e}")
        if mail_server:
            mail_server.logout()
        return

    try:
        # 3. Search for new fund setup emails
        print(f"\nStep 3: Searching for emails...")
        email_ids = search_emails_imap(mail_server)

        if not email_ids:
            print("No matching emails found.")
            return

        print(f"Found {len(email_ids)} email(s) matching the criteria.")

        # 4. Process each email
        for i, email_id in enumerate(email_ids):
            print(f"\n--- Processing email {i+1}/{len(email_ids)} (IMAP ID: {email_id}) ---")

            # Get email body and unique Message-ID
            email_body, message_id = get_email_body_and_message_id(mail_server, email_id)

            if not email_body or not message_id:
                print(f"Could not retrieve body or Message-ID for email. Skipping.")
                continue

            # Check if this message has already been processed
            if message_id in processed_message_ids:
                print(f"Message-ID '{message_id}' has already been processed. Skipping.")
                continue

            print(f"Found new email with Message-ID: {message_id}")

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

                # Mark email as processed using its permanent Message-ID
                save_processed_message_id(message_id)
                print(f"Marked Message-ID {message_id} as processed.")

            except Exception as e:
                print(f"An error occurred while interacting with the API for fund '{fund_id}': {e}")
                print("Skipping this email and continuing to the next one.")

    finally:
        # 5. Close the connection
        if mail_server:
            mail_server.logout()
            print("\nLogged out from Gmail and connection closed.")
        print("\n--- Agent finished ---")


if __name__ == "__main__":
    main()