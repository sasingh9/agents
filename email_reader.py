import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import config

def get_gmail_service():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(config.GMAIL_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(config.GMAIL_TOKEN_FILE, config.GMAIL_SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.GMAIL_CREDENTIALS_FILE, config.GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(config.GMAIL_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def search_emails(service, query):
    """Search for emails matching the query."""
    try:
        response = service.users().messages().list(userId='me', q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId='me', q=query, pageToken=page_token).execute()
            if 'messages' in response:
                messages.extend(response['messages'])

        return messages
    except HttpError as error:
        print(f'An error occurred: {error}')
        return []

def get_email_body(service, msg_id):
    """Get the body of an email."""
    try:
        message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        payload = message['payload']
        parts = payload.get('parts')

        if parts:
            for part in parts:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    return base64.urlsafe_b64decode(data).decode('utf-8')
        # If the email is not multipart
        elif 'body' in payload:
             data = payload['body']['data']
             return base64.urlsafe_b64decode(data).decode('utf-8')

        return "" # Return empty string if no plain text body is found
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

if __name__ == '__main__':
    # This is for testing purposes.
    # Note: You will need a credentials.json file from Google Cloud for this to work.
    # The user will be prompted to authenticate in the browser the first time.
    print("Please go to the following URL to authorize the application:")
    print("And place the downloaded credentials.json in this directory.")
    print("https://console.cloud.google.com/apis/credentials")

    gmail_service = get_gmail_service()
    if gmail_service:
        print("Successfully connected to Gmail.")
        emails = search_emails(gmail_service, config.EMAIL_SEARCH_QUERY)
        print(f"Found {len(emails)} emails matching the query.")
        if emails:
            # Get the body of the first email
            first_email_body = get_email_body(gmail_service, emails[0]['id'])
            print("\nBody of the first email:")
            print(first_email_body)
    else:
        print("Failed to connect to Gmail.")