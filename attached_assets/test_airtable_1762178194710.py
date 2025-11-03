import os
from dotenv import load_dotenv
import requests
import json

# This script is designed to test your Airtable credentials independently.
# It requires the same .env file setup as the main scraper.

def test_airtable_connection():
    """
    Tests the Airtable connection by attempting to list records.
    This requires a valid API key, Base ID, and table name.
    """
    print("🚀 Starting Airtable connection test...")

    # Load environment variables from the .env file.
    load_dotenv()

    # Get credentials from the environment.
    AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
    AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
    
    # You may need to change this if your table is named differently.
    AIRTABLE_TABLE = "Jobs" 

    # Check if credentials are found.
    if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
        print("❌ Error: Airtable API Key or Base ID not found in .env file.")
        print("Please ensure your .env file has both AIRTABLE_API_KEY and AIRTABLE_BASE_ID.")
        return

    # Construct the API URL and headers.
    AIRTABLE_API_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}"
    AIRTABLE_HEADERS = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Define a simple payload to test the connection (in this case, just listing records).
    params = {"pageSize": 10}

    try:
        # Make the GET request to list records.
        response = requests.get(AIRTABLE_API_URL, headers=AIRTABLE_HEADERS, params=params)
        
        # Check for HTTP errors.
        response.raise_for_status()
        
        # Parse the JSON response.
        data = response.json()
        
        # Check if records were retrieved successfully.
        records = data.get("records", [])
        if records:
            print(f"✅ Success! Found {len(records)} records in your '{AIRTABLE_TABLE}' table.")
            # Print a sample record to confirm the data structure is correct.
            print("\nSample Record:")
            print(json.dumps(records[0], indent=2))
        else:
            print(f"✅ Success! Connection established, but no records were found in the '{AIRTABLE_TABLE}' table.")

    except requests.exceptions.HTTPError as err:
        print(f"❌ HTTP Error: {err}")
        print("This often means your API key or Base ID is incorrect, or you don't have permission to access the base.")
        print(f"Response content: {err.response.text}")
    except requests.exceptions.RequestException as err:
        print(f"❌ Request Error: {err}")
        print("Could not connect to Airtable. Check your internet connection or try again later.")
    except json.JSONDecodeError:
        print("❌ Error: Could not decode JSON response from Airtable.")
        print("This could indicate an issue with the API key or an unexpected server response.")
    except Exception as err:
        print(f"❌ An unexpected error occurred: {err}")

# Run the test.
if __name__ == "__main__":
    test_airtable_connection()
