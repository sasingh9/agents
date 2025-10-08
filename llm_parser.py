import openai
import json
import config

def extract_fund_details_with_llm(email_body):
    """
    Uses OpenAI's GPT model to extract structured fund details from an email body.

    Args:
        email_body (str): The plain text content of the fund setup email.

    Returns:
        dict: A dictionary containing the extracted fund details, or None if parsing fails.
    """
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "YOUR_OPENAI_API_KEY":
        raise ValueError("OpenAI API key is not configured in config.py")

    openai.api_key = config.OPENAI_API_KEY

    # This is the prompt that will be sent to the LLM. It includes instructions
    # on what to extract and in what format.
    prompt = f"""
    From the following email body, extract the fund setup information.
    Your response MUST be a single, valid JSON object and nothing else. Do not include any explanatory text before or after the JSON.
    The JSON object should have the following keys. If a value is not present in the email, use a JSON null value.
    - fundID (string)
    - fundName (string)
    - fundTicker (string)
    - isin (string)
    - fundType (string)
    - legalStructure (string)
    - domicile (string)
    - inceptionDate (string, in YYYY-MM-DD format)
    - fiscalYearEnd (string, in MM-DD format)
    - baseCurrency (string)
    - managementFee (number)
    - performanceFee (number)
    - fundAdministrator (string)
    - custodian (string)
    - primeBrokers (string, comma-separated)
    - investmentStrategy (string)
    - valuationFrequency (string)
    - subscriptionCycle (string)
    - redemptionCycle (string)
    - nav (number)
    - navDate (string, in YYYY-MM-DD format)
    - status (string, e.g., 'Active', 'Inactive', 'In-Progress')

    Email Body:
    ---
    {email_body}
    ---
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an intelligent assistant that extracts financial data from text. You must return the data as a single, valid JSON object and nothing else."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0, # Lower temperature for more deterministic output
        )

        # The response from the API is a JSON string in the content of the message.
        extracted_json_str = response.choices[0].message.content

        # The model might still return the JSON wrapped in markdown, so we clean it.
        if extracted_json_str.strip().startswith("```json"):
            extracted_json_str = extracted_json_str.strip()[7:-4]

        fund_details = json.loads(extracted_json_str)
        return fund_details

    except Exception as e:
        print(f"An error occurred while calling the OpenAI API: {e}")
        return None

if __name__ == '__main__':
    # This is an example for testing purposes.
    # To run this, you need to have your OpenAI API key in config.py

    # Example email body
    test_email_body = """
    Dear Team,

    Please set up the following new fund in the system:

    Fund Name: Apex Global Growth Fund
    Fund ID: APXGGF-001
    Ticker: AGGF
    ISIN: US0378331005
    Fund Type: Equity
    Status: Active
    Inception Date: 2023-01-15
    Base Currency: USD
    Investment Strategy: Invests in global equities with high growth potential.
    Fund Administrator: Global Fund Services
    Custodian: National Bank
    NAV: 105.50
    NAV Date: 2024-10-06

    Thank you.
    """

    print("Extracting fund details from sample email...")
    try:
        details = extract_fund_details_with_llm(test_email_body)
        if details:
            print("Successfully extracted details:")
            print(json.dumps(details, indent=2))
        else:
            print("Failed to extract details.")
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")