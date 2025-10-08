# Fund Setup Agent

This agent automates the process of setting up new funds by reading details from emails and updating a backend system. It connects to a Gmail account using IMAP and a Google App Password.

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Secrets:**
    - Create a copy of the `secrets.py.example` file and name it `secrets.py`.
    - Open the new `secrets.py` file and fill in the following values:
        - `OPENAI_API_KEY`: Your key from the OpenAI platform.
        - `GMAIL_APP_PASSWORD`: The 16-character password you generate from your Google Account (see step 3).
        - `API_PASSWORD`: The password for your backend API user.
    - The `secrets.py` file is included in `.gitignore` and will not be committed to version control.

3.  **Generate a Google App Password (if you don't have one):**
    - Go to your Google Account settings: [myaccount.google.com](https://myaccount.google.com/).
    - Navigate to **Security**.
    - Make sure **2-Step Verification** is turned **On**. You cannot create App Passwords without it.
    - Under "Signing in to Google," click on **App passwords**. You may need to sign in again.
    - Under "Select app," choose **Other (Custom name)**.
    - Give it a name (e.g., "Fund Setup Agent") and click **Generate**.
    - Google will display a 16-character password. Copy this and place it in your `secrets.py` file.

4.  **Configure the Agent:**
    - Open `config.py`.
    - Verify that `GMAIL_USERNAME`, `API_BASE_URL`, and `API_USERNAME` are correct for your environment.

5.  **Run the Agent:**
    - Run the agent from your terminal:
      ```bash
      python fund_setup_agent.py
      ```
    - The agent will now run without prompting for passwords, as they are all loaded from your `secrets.py` file.

## How it Works

1.  **Email Monitoring:** The agent connects to Gmail's IMAP server using the credentials from `config.py` and `secrets.py`.
2.  **Email Filtering:** It searches for emails from the sender and with the subject specified in `config.py`.
3.  **Data Extraction:** For each new email, it uses the OpenAI API key to parse the body and extract fund attributes.
4.  **Duplicate Prevention:** It tracks processed emails by their unique `Message-ID` in `processed_message_ids.json`.
5.  **API Interaction:** It creates or updates fund records via the backend API using the configured credentials.
6.  **Security:**
    - All secrets (`OPENAI_API_KEY`, `GMAIL_APP_PASSWORD`, `API_PASSWORD`) are stored in a `secrets.py` file, which is ignored by Git.
    - This prevents sensitive credentials from being stored in the code or committed to version control.