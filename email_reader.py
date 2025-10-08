import imaplib
import email
from email.header import decode_header
import config

def connect_to_gmail():
    """
    Connects to Gmail's IMAP server and logs in using credentials from config.

    Returns:
        imaplib.IMAP4_SSL: An authenticated IMAP connection object, or None on failure.
    """
    if not config.GMAIL_APP_PASSWORD or "YOUR_" in config.GMAIL_APP_PASSWORD:
        print("ERROR: Gmail App Password is not configured in `secrets.py`.")
        return None

    try:
        # Connect to the server
        mail = imaplib.IMAP4_SSL(config.IMAP_SERVER)

        # Login using the password from the config
        mail.login(config.GMAIL_USERNAME, config.GMAIL_APP_PASSWORD)

        return mail
    except imaplib.IMAP4.error as e:
        print(f"Failed to login to Gmail: {e}")
        print("Please ensure your `GMAIL_USERNAME` and `GMAIL_APP_PASSWORD` in your config/secrets are correct.")
        return None

def search_emails_imap(mail):
    """
    Searches for emails from a specific sender with a specific subject.

    Args:
        mail (imaplib.IMAP4_SSL): An authenticated IMAP connection object.

    Returns:
        list: A list of email IDs (as strings) matching the criteria.
    """
    try:
        mail.select('inbox')

        # Construct the search query
        query = f'(FROM "{config.EMAIL_SENDER}" SUBJECT "{config.EMAIL_SUBJECT}")'

        status, messages = mail.search(None, query)
        if status != 'OK':
            print("Error searching for emails.")
            return []

        # messages is a list of byte strings, e.g., [b'1 2 3']
        email_ids = messages[0].split()
        return [eid.decode() for eid in email_ids]

    except Exception as e:
        print(f"An error occurred while searching emails: {e}")
        return []

def get_email_body_and_message_id(mail, email_id):
    """
    Fetches the plain text body and the Message-ID of a specific email.

    Args:
        mail (imaplib.IMAP4_SSL): An authenticated IMAP connection object.
        email_id (str): The ID of the email to fetch.

    Returns:
        tuple: A tuple containing (body, message_id). Returns (None, None) on failure.
    """
    try:
        status, msg_data = mail.fetch(email_id, '(RFC822)')
        if status != 'OK':
            return None, None

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                message_id = msg.get('Message-ID')
                body = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        if content_type == 'text/plain' and 'attachment' not in content_disposition:
                            try:
                                body = part.get_payload(decode=True).decode()
                            except UnicodeDecodeError:
                                body = part.get_payload(decode=True).decode('latin-1')
                            break # Found the plain text part
                else:
                    try:
                        body = msg.get_payload(decode=True).decode()
                    except UnicodeDecodeError:
                        body = msg.get_payload(decode=True).decode('latin-1')

                return body, message_id
        return None, None
    except Exception as e:
        print(f"An error occurred while fetching email data for ID {email_id}: {e}")
        return None, None

if __name__ == '__main__':
    # This is for testing purposes.
    print("Testing IMAP Email Reader...")

    mail_server = connect_to_gmail()

    if mail_server:
        print("\nSuccessfully connected to Gmail via IMAP.")

        print("Searching for emails...")
        email_ids = search_emails_imap(mail_server)

        if not email_ids:
            print("No matching emails found.")
        else:
            print(f"Found {len(email_ids)} matching email(s).")

            # Fetch the body of the first email found
            first_email_id = email_ids[0]
            print(f"\nFetching body for email ID: {first_email_id}")
            body = get_email_body_imap(mail_server, first_email_id)

            if body:
                print("\n--- Email Body ---")
                print(body)
                print("--------------------")
            else:
                print("Could not retrieve email body.")

        # Close the connection
        mail_server.logout()
        print("\nLogged out and connection closed.")
    else:
        print("\nCould not establish connection to Gmail.")