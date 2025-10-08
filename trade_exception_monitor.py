import asyncio
import json
import hashlib
import smtplib
import getpass
import base64
import configparser
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
import openai

# --- Configuration Loading ---
def load_config():
    """Loads configuration from config.ini"""
    config_file = 'config.ini'
    if not os.path.exists(config_file):
        print(f"Error: {config_file} not found.")
        print("Please copy config.ini.template to config.ini and fill in your details.")
        exit(1)

    config = configparser.ConfigParser()
    config.read(config_file)
    return config

config = load_config()

# --- Global Settings ---
PROCESSED_EXCEPTIONS_FILE = "processed_exceptions.json"

# Web Scraping Configuration
START_DATE_SELECTOR = 'input[type="datetime-local"]'
END_DATE_SELECTOR = 'input[type="datetime-local"]'
SEARCH_BUTTON_SELECTOR = 'button[type="submit"]'
RESULTS_TABLE_SELECTOR = 'div[role="grid"]'
MODAL_JSON_SELECTOR = 'pre#modal-description'

# Column indexes
CLIENT_REF_COLUMN_INDEX = 1
FAILURE_REASON_COLUMN_INDEX = 2
FAILED_JASON_COLUMN_INDEX = 4


async def scrape_trade_exceptions():
    """
    Scrapes the trade exception inquiry page for new exceptions within the last hour.
    This version is tailored for a Material-UI DataGrid and modal interaction.
    """
    # Get API credentials from config, prompt for password if blank
    api_username = config['API']['username']
    api_password = config['API'].get('password', '')
    if not api_password:
        prompt_message = f"Please enter the API password for user '{api_username}': "
        api_password = getpass.getpass(prompt_message)

    # Prepare credentials for HTTP Basic Authentication
    auth_string = f"{api_username}:{api_password}"
    encoded_auth_string = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    auth_header = f"Basic {encoded_auth_string}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Set the authentication header for all subsequent requests on this page
        await page.set_extra_http_headers({"Authorization": auth_header})

        try:
            print("Navigating to the trade exception inquiry page with authentication...")
            await page.goto("http://localhost:3000/trade-exception-inquiry", timeout=60000)

            # Calculate and format date range for datetime-local input
            now = datetime.now()
            start_date = now - timedelta(hours=24)
            # The format must be YYYY-MM-DDTHH:MM for datetime-local inputs
            start_date_str = start_date.strftime("%Y-%m-%dT%H:%M")
            end_date_str = now.strftime("%Y-%m-%dT%H:%M")

            # Fill in the form using positional selectors for date fields
            print(f"Searching for exceptions from {start_date_str} to {end_date_str}")
            date_inputs = page.locator(START_DATE_SELECTOR)
            await date_inputs.nth(0).fill(start_date_str)
            await date_inputs.nth(1).fill(end_date_str)
            await page.click(SEARCH_BUTTON_SELECTOR)

            # Wait for the search to complete by looking for either the first data row or the 'no rows' message.
            print("Waiting for search results to load...")
            first_row_locator = page.locator(f'{RESULTS_TABLE_SELECTOR} div[role="row"]:not([aria-rowindex="1"])')
            no_rows_locator = page.locator('text="No exceptions found."')

            # Wait for either locator to be visible, indicating the search is complete.
            await first_row_locator.or_(no_rows_locator).first.wait_for(timeout=30000)

            # Now that the content has loaded, check if the "no rows" message is what appeared.
            if await no_rows_locator.is_visible():
                print("No exception rows found on the page.")
                return []

            exceptions = []
            # Use locators to interact with the grid, preventing the 'ElementHandle' error.
            row_locator = page.locator(f'{RESULTS_TABLE_SELECTOR} div[role="row"]:not([aria-rowindex="1"])')
            row_count = await row_locator.count()
            print(f"Found {row_count} data rows in the grid.")

            for i in range(row_count):
                row = row_locator.nth(i)

                # Extract text using locators chained from the row locator
                client_ref = await row.locator('div[role="gridcell"]').nth(CLIENT_REF_COLUMN_INDEX).inner_text()
                failure_reason = await row.locator('div[role="gridcell"]').nth(FAILURE_REASON_COLUMN_INDEX).inner_text()

                # Click the '...' button to open the modal for the JSON
                json_button = row.locator('div[role="gridcell"]').nth(FAILED_JASON_COLUMN_INDEX).locator('button')
                await json_button.click()

                # Wait for the modal to appear and scrape the JSON content
                modal_content_locator = page.locator(MODAL_JSON_SELECTOR)
                await modal_content_locator.wait_for(state='visible', timeout=5000)
                failed_jason = await modal_content_locator.inner_text()

                # Close the modal by pressing the Escape key
                await page.keyboard.press('Escape')
                await modal_content_locator.wait_for(state='hidden', timeout=5000)

                exceptions.append({
                    "client_reference": client_ref,
                    "failure_reason": failure_reason,
                    "failed_jason": failed_jason,
                })

            return exceptions

        except Exception as e:
            print(f"An error occurred during scraping: {e}")
            print("Please ensure the application is running at http://localhost:3000/trade-exception-inquiry")
            print("and that the selectors in the configuration section are correct.")
            return []
        finally:
            await browser.close()


def get_exception_id(exception):
    """Creates a unique ID for an exception to avoid duplicates."""
    exception_str = json.dumps(exception, sort_keys=True)
    return hashlib.md5(exception_str.encode('utf-8')).hexdigest()


def load_processed_exceptions():
    """Loads the set of processed exception IDs from a file."""
    try:
        with open(PROCESSED_EXCEPTIONS_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_processed_exceptions(processed_ids):
    """Saves a set of processed exception IDs to a file."""
    with open(PROCESSED_EXCEPTIONS_FILE, "w") as f:
        json.dump(list(processed_ids), f, indent=2)


async def main():
    """
    Main function to run the scraper, check for new exceptions, and process them.
    """
    print("Starting trade exception monitor...")

    processed_exception_ids = load_processed_exceptions()
    print(f"Loaded {len(processed_exception_ids)} previously processed exception IDs.")

    scraped_exceptions = await scrape_trade_exceptions()

    new_exceptions = []
    for ex in scraped_exceptions:
        ex_id = get_exception_id(ex)
        if ex_id not in processed_exception_ids:
            new_exceptions.append(ex)
            processed_exception_ids.add(ex_id)

    if new_exceptions:
        print(f"\nFound {len(new_exceptions)} new exceptions. Requesting LLM suggestions...")
        for ex in new_exceptions:
            # Get LLM suggestion for the fix
            suggestion = await get_llm_suggestion(ex['failure_reason'], ex['failed_jason'])
            ex['llm_suggestion'] = suggestion

        print("\nProcessing complete. New exceptions with suggestions:")
        for ex in new_exceptions:
            print(f"  - Client Reference: {ex['client_reference']}")
            print(f"    Reason: {ex['failure_reason']}")
            print(f"    Suggestion: {ex.get('llm_suggestion', 'N/A')}")

        # Save the updated list of processed IDs
        save_processed_exceptions(processed_exception_ids)
        print(f"Updated processed exceptions file with {len(new_exceptions)} new entries.")

        # Send email notification with enriched data
        send_email_notification(new_exceptions)

    else:
        print("\nNo new exceptions found in the last hour.")


async def get_llm_suggestion(failure_reason, failed_json):
    """
    Contacts an LLM to get a suggestion for fixing a trade exception.
    """
    print(f"Requesting LLM suggestion for: {failure_reason[:50]}...")
    openai_api_key = config['LLM']['api_key']
    if not openai_api_key or openai_api_key == "YOUR_OPENAI_API_KEY":
        print("Warning: OpenAI API key is not configured. Skipping LLM suggestion.")
        return "OpenAI API key not configured."

    try:
        client = openai.AsyncOpenAI(api_key=openai_api_key)

        prompt = f"""
        A trade processing system has produced an exception.
        Your task is to analyze the failure reason and the associated JSON data to suggest a likely cause and a potential fix.
        The suggestion should be concise and actionable for a data entry operator or a support team.
        Failure Reason:
        "{failure_reason}"
        Failed JSON Data:
        ```json
        {failed_json}
        ```
        Please provide your suggestion on how to fix this error.
        """

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert financial data analyst providing helpful suggestions to resolve trade exceptions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=200,
        )
        suggestion = response.choices[0].message.content.strip()
        print("LLM suggestion received.")
        return suggestion
    except openai.RateLimitError as e:
        if "insufficient_quota" in str(e).lower():
            error_message = (
                "\n---[ OpenAI Error ]---\n"
                "Error: Your OpenAI account has insufficient quota.\n"
                "This usually means your free trial has ended or you've hit your monthly spending limit.\n"
                "To fix this, please check your plan and billing details at:\n"
                "https://platform.openai.com/account/billing/overview\n"
                "------------------------\n"
            )
            print(error_message)
            return "Could not get suggestion: OpenAI account has insufficient quota."
        else:
            print(f"OpenAI API rate limit exceeded: {e}")
            return "Could not get suggestion: OpenAI API rate limit exceeded."
    except Exception as e:
        print(f"Error getting LLM suggestion: {e}")
        return "Could not get a suggestion from the LLM due to an error."


def send_email_notification(exceptions):
    """Sends an email with the details of new exceptions and LLM suggestions."""
    print("Preparing to send email notification...")

    # Create the email content
    subject = f"New Trade Exceptions Detected ({datetime.now():%Y-%m-%d %H:%M}) - AI Suggestions Included"
    body_html = "<h3>New trade exceptions were found, with AI-powered suggestions:</h3>"

    for ex in exceptions:
        suggestion = ex.get('llm_suggestion', 'No suggestion available.').replace('\n', '<br>')
        body_html += f"""
        <hr style="border-top: 1px solid #ddd;">
        <div style="padding: 10px 0;">
            <p><strong>Client Reference:</strong> {ex.get('client_reference', 'N/A')}</p>
            <p><strong>Failure Reason:</strong> {ex.get('failure_reason', 'N/A')}</p>
            <div style="background-color: #f0f4f8; border-left: 4px solid #4a69bd; padding: 10px; margin: 10px 0;">
                <p style="margin: 0; font-weight: bold;">AI-Powered Suggestion:</p>
                <p style="margin: 5px 0 0 0;">{suggestion}</p>
            </div>
            <p><strong>Failed JSON:</strong></p>
            <pre style="background-color: #eeeeee; padding: 10px; border-radius: 4px; white-space: pre-wrap; word-break: break-all;"><code>{ex.get('failed_jason', '{{}}')}</code></pre>
        </div>
        """

    msg = MIMEMultipart()

    email_from = config['Email']['from_address']
    email_to = config['Email']['to_address']

    msg['From'] = email_from
    msg['To'] = email_to
    msg['Subject'] = subject
    msg.attach(MIMEText(body_html, 'html'))

    try:
        smtp_username = config['Email']['username']
        smtp_password = config['Email'].get('password', '')
        if not smtp_password:
            prompt_message = f"Please enter the SMTP password for {smtp_username}: "
            smtp_password = getpass.getpass(prompt_message)

        # Connect to the SMTP server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(email_from, email_to, msg.as_string())
        print("Email notification sent successfully!")
    except smtplib.SMTPAuthenticationError:
        error_message = (
            "\n---[ Gmail SMTP Error ]---\n"
            "Error: Authentication failed. Gmail did not accept the username and password.\n\n"
            "Common Causes & Solutions:\n"
            "1.  **2-Step Verification is ON:** If you use 2-Step Verification, you CANNOT use your regular password.\n"
            "    You MUST generate and use an 'App Password'.\n"
            "    - Go to: https://myaccount.google.com/apppasswords\n"
            "    - Create a new App Password for this script and use the 16-digit password it provides.\n\n"
            "2.  **Incorrect Password:** You may have mistyped the password or App Password.\n\n"
            "3.  **Incorrect Username:** Ensure the `username` in your config.ini is your full, correct Gmail address.\n"
            "---------------------------\n"
        )
        print(error_message)
    except smtplib.SMTPException as e:
        print(f"An SMTP error occurred: {e}")
        print("Please check your SMTP server details and network connection.")
    except Exception as e:
        print(f"An unexpected error occurred while sending the email: {e}")


if __name__ == "__main__":
    asyncio.run(main())