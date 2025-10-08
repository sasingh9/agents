# Trade Exception Monitor

This script automates the process of checking a web-based trade exception inquiry tool for new exceptions that have occurred within the last hour. If new exceptions are found, it sends an email notification with the details.

## Features

- Navigates to a web page and performs a search based on a dynamic date range (the last hour).
- Scrapes the results from an HTML table.
- Keeps track of previously processed exceptions to avoid sending duplicate notifications.
- Sends a detailed email notification for new exceptions, including the Client Reference, Failure Reason, and the full Failed JSON text.

## Prerequisites

- Python 3.7+
- Access to the target web application at `http://localhost:3000/trade-exception-inquiry`.

## Installation

1.  **Clone the repository or download the script.**

2.  **Install the required Python packages:**
    ```bash
    pip install playwright
    ```

3.  **Install the necessary browser drivers for Playwright:**
    This command downloads the browser binaries (Chromium, Firefox, WebKit) that Playwright uses to automate tasks.
    ```bash
    playwright install
    ```

## Configuration

All configuration is now handled in a separate `config.ini` file for better security. This file is **not** tracked by Git, so your secrets are safe.

### Step 1: Create your `config.ini` file

Copy the template file to create your own configuration file:
```bash
cp config.ini.template config.ini
```

### Step 2: Edit `config.ini`

Open the `config.ini` file in a text editor and fill in your details under the appropriate sections.

#### `[API]`
- `username`: The username for your application's backend API.
- `password`: You can leave this blank to be prompted for the password securely when the script runs.

#### `[LLM]`
- `api_key`: Your API key from the [OpenAI Platform](https://platform.openai.com/).

#### `[Email]`
- `username`: Your full Gmail address.
- `password`: Leave this blank to be prompted for your password or App Password securely at runtime.
- `to_address`: The email address where notifications will be sent.
- `from_address`: The email address the notification will be sent from (usually the same as your username).

## Usage

Once the script is configured, you can run it from your terminal:

```bash
python trade_exception_monitor.py
```

The script will launch a headless browser, perform the check, and print its findings to the console. If new exceptions are found, it will also send an email.

## Scheduling

To run this monitor automatically at regular intervals (e.g., every hour), you can use a scheduling tool like `cron` on Linux/macOS or Task Scheduler on Windows.

### Example `cron` Job

To run the script at the top of every hour, you can add the following line to your crontab (edit with `crontab -e`):

```cron
0 * * * * /usr/bin/python3 /path/to/your/script/trade_exception_monitor.py >> /path/to/your/logs/monitor.log 2>&1
```
*Make sure to replace the paths with the correct paths to your Python interpreter and the script.* This will also redirect the script's output to a log file.