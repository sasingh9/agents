# Fund Setup Agent

This agent automates the process of setting up new funds by reading details from emails and updating a backend system.

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure OpenAI API Key:**
    - Open `config.py`.
    - Replace `"YOUR_OPENAI_API_KEY"` with your actual OpenAI API key. It is highly recommended to use an environment variable for this in a production environment.

3.  **Enable the Gmail API and Get Credentials:**
    - Go to the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
    - Create a new project or select an existing one.
    - Enable the **Gmail API**.
    - Create credentials for an **OAuth client ID**.
    - Choose **Desktop app** as the application type.
    - After creation, download the JSON file.
    - Rename the downloaded file to `credentials.json` and place it in the root directory of this project, replacing the placeholder file.

4.  **Run the Agent for the First Time:**
    - When you run the agent for the first time, it will open a new tab in your browser and ask you to authorize access to your Gmail account.
    - After you approve, it will create a `token.json` file in the project directory. This file stores your authorization token so you don't have to log in every time.
    ```bash
    python fund_setup_agent.py
    ```

## How it Works

1.  **Email Monitoring:** The agent connects to the Gmail account specified in `config.py` (`sangharshsingh@gmail.com`).
2.  **Email Filtering:** It searches for unread emails from `ssingh9@gmail.com` with the subject "Fund Setup Request".
3.  **Data Extraction:** For each matching email, it uses an OpenAI LLM to parse the email body and extract key-value pairs corresponding to the fund's attributes (e.g., Fund Name, Ticker, ISIN).
4.  **API Interaction:**
    - It checks if a fund with the extracted `fundID` already exists by querying the `/api/funds/{fundID}` endpoint.
    - If the fund exists, it sends a `PUT` request to update the record.
    - If it doesn't exist, it sends a `POST` request to create a new fund.
5.  **Security:**
    - Gmail access is handled via OAuth2, so your password is not stored.
    - The backend API password is requested at runtime and is not stored in the code.