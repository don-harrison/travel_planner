import requests
import os
import pandas as pd
from dotenv import load_dotenv
from langchain.tools import StructuredTool
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent

# Set the model name for our LLMs.
GEMINI_MODEL = "gemini-2.0-flash"

# Store the API key in a variable.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Load environment variables
load_dotenv()

# Your RapidAPI key
AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")

# Base URL for Amadeus API
BASE_URL = "https://test.api.amadeus.com/v2"

# Function to get flight offers
def get_bearer_token():
    """
    Get the Bearer token for Amadeus API using client credentials.
    Returns:
        str: The Bearer token.
    """
    
    auth_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_API_KEY,
        "client_secret": AMADEUS_CLIENT_SECRET
    }
    
    response = requests.post(auth_url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def get_flight_offers(origin, destination, departure_date, return_date):
    """
    Get flight offers from origin to destination with specified dates.

    Args:
        origin (str): The IATA code of the origin airport.
        destination (str): The IATA code of the destination airport.
        departure_date (str): The departure date in YYYY-MM-DD format.
        return_date (str): The return date in YYYY-MM-DD format.
    Returns:
        dict: The flight offers data.
    """

    token = get_bearer_token()
    if not token:
        print("Failed to retrieve Bearer token.")
        return None
    
    url = f"{BASE_URL}/shopping/flight-offers?originLocationCode={origin}&destinationLocationCode={destination}&departureDate={departure_date}&returnDate={return_date}&adults=1&nonStop=true&maxPrice=1000&currencyCode=USD"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None


def find_flights(origin, destination, departure_date, return_date):
    """
    Search for roundtrip flights from origin to destination with specified dates.
    
    Args:
        origin (str): The name of the city of origin.
        destination (str): The name of the city of destination.
        departure_date (str): The departure date in YYYY-MM-DD format.
        return_date (str): The return date in YYYY-MM-DD format.
    
    Returns:
        str: The result of the search with info about parks and activities.
    """

    # Load the airport codes from the CSV file
    airport_codes = pd.read_csv("Resources/airports.csv", encoding="latin1")

    # Define the tool for searching flights with a single input
    search_flights_tool = StructuredTool.from_function(
        func=lambda input: get_flight_offers(**eval(input)),  # Parse the input string as a dictionary
        name="SearchFlights",
        description="Search for flight offers based on origin, destination, departure date, and return date. Input should be a dictionary with 'origin', 'destination', 'departure_date', and 'return_date'.",
        parameters=[
            {"name": "input", "type": "string", "description": "A dictionary with 'origin', 'destination', 'departure_date', and 'return_date' as keys."}
        ]
    )

    # Initialize the LangChain agent with the tools
    llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, api_key=GEMINI_API_KEY)

    agent = initialize_agent([search_flights_tool], llm, agent_type="zero-shot-react-description", verbose=True)

    # Use the agent to search for parks and activities matching interests
    result = agent.run(f"You are a travel agent searching for the cheapest roundtrip flight from {origin} to {destination} for the dates {departure_date} and {return_date}. Using the airport codes from the airport_codes.csv file, get the three digit IATA code to input into the get_flight_offers function. Use the Amadeus API through the get_flight_offers function to find the 5 best flight offers. If there are multiple airports in the same city, make calls for each aiport to get the 5 best options. Of the 5 best flights give your reccomendation and why. Return the results as if you were customer service. Make sure to include the flight number, departure and arrival times, and the price for each of the five options before your recommendation.")
    return result


# Example usage
if __name__ == "__main__":

    origin = "Boston, MA"  # Los Angeles International Airport
    destination = "New York, New York"  # John F. Kennedy International Airport
    departure_date = "2025-12-01"
    return_date = "2025-12-15"

    # flight_offers = get_flight_offers("BOS", "JFK", departure_date, return_date)

    # if flight_offers:
    #     print(flight_offers)

    result = find_flights(origin, destination, departure_date, return_date)

    print(result)