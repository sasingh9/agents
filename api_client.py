import requests
import getpass
import json
import config

class FundAPIClient:
    def __init__(self, base_url, username, password=None):
        self.base_url = base_url
        self.username = username
        self.password = password or getpass.getpass(f"Enter API password for user '{username}': ")
        self.auth = (self.username, self.password)

    def _make_request(self, method, endpoint, data=None):
        """Helper function to make authenticated requests."""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.request(
                method,
                url,
                auth=self.auth,
                headers=headers,
                data=json.dumps(data) if data else None
            )
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            if response.status_code == 204: # No Content
                return None
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise

    def get_fund(self, fund_id):
        """
        Retrieves a fund by its ID to check if it exists.
        Returns the fund data if found, otherwise None.
        """
        try:
            return self._make_request('GET', f"/funds/{fund_id}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None # Fund not found, which is a valid outcome for this check
            raise # Re-raise other HTTP errors

    def create_fund(self, fund_data):
        """
        Creates a new fund.
        """
        return self._make_request('POST', '/funds', data=fund_data)

    def update_fund(self, fund_id, fund_data):
        """
        Updates an existing fund by its ID.
        """
        return self._make_request('PUT', f"/funds/{fund_id}", data=fund_data)

if __name__ == '__main__':
    # This is an example for testing purposes.
    # It assumes the backend API is running and accessible.
    print("Testing Fund API Client...")

    try:
        # The user will be prompted for their password here.
        api_client = FundAPIClient(config.API_BASE_URL, config.API_USERNAME)

        # Example: Check if a fund exists
        test_fund_id = "TEST-001"
        print(f"\nChecking for fund with ID: {test_fund_id}")
        existing_fund = api_client.get_fund(test_fund_id)

        if existing_fund:
            print(f"Fund '{test_fund_id}' found. Details:")
            print(json.dumps(existing_fund, indent=2))

            # Example: Update the fund
            print(f"\nUpdating fund '{test_fund_id}'...")
            update_data = {"status": "Updated by Test Client"}
            updated_fund = api_client.update_fund(test_fund_id, update_data)
            print("Update successful. Response:")
            print(json.dumps(updated_fund, indent=2))

        else:
            print(f"Fund '{test_fund_id}' not found.")

            # Example: Create the fund
            print(f"\nCreating new fund with ID: {test_fund_id}")
            new_fund_data = {
                "fundID": test_fund_id,
                "fundName": "API Client Test Fund",
                "fundTicker": "APITEST",
                "isin": "US1234567890",
                "fundType": "Test",
                "status": "Active"
            }
            created_fund = api_client.create_fund(new_fund_data)
            print("Fund creation successful. Response:")
            print(json.dumps(created_fund, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"\nCould not connect to the API at {config.API_BASE_URL}.")
        print("Please ensure the backend server is running and the URL in config.py is correct.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")