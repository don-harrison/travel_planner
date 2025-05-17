import os
from dotenv import load_dotenv
import requests
from langchain.tools import StructuredTool
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent

PRICELINE_API_KEY = os.getenv("RAPIDAPI_KEY")
PRICELINE_API_URL = "https://priceline-com-provider.p.rapidapi.com/v1/hotels/locations"

# Set the model name for our LLMs.
GEMINI_MODEL = "gemini-2.0-flash"

# Store the API key in a variable.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_location_id(city_name):
    """
    Get the location ID for a given city name using the Priceline API.
    Args:
        city_name (str): The name of the city.
        Returns:
        str: The location ID.
    """

    url = "https://priceline-com2.p.rapidapi.com/hotels/auto-complete"

    headers = {
	"x-rapidapi-key": "b6aee17ad3msh6d2a5725b07d7bbp17488ajsnf62d344413af",
	"x-rapidapi-host": "priceline-com2.p.rapidapi.com"
    }
    params = {"query": city_name}

    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    print(data)
    location_id = response.json().get("cityID")
    if response.status_code == 200:
        data = response.json()
        # Print to inspect structure if needed
        # print(data)
        try:
            # Find the first CITY type result
            for item in data["data"]["searchItems"]:
                if item.get("type") == "CITY":
                    return item["id"]
            print("No CITY type found in searchItems.")
            return None
        except Exception as e:
            print("Error extracting location id:", e)
            return None
    else:
        print("LocationId request failed:", response.status_code, response.text)
        return None
    
def get_hotels_nearby(city_name, check_in, check_out, rooms=1, adults=1):
    """
    Get hotels nearby a city with specified check-in and check-out dates.
    Args:
        city_name (str): The name of the city.
        check_in (str): Check-in date in YYYY-MM-DD format.
        check_out (str): Check-out date in YYYY-MM-DD format.
        rooms (int): Number of rooms. Default is 1.
        adults (int): Number of adults. Default is 1.
        Returns:
        dict: The hotel data.
    """
    url = "https://priceline-com2.p.rapidapi.com/hotels/search"
    
    headers = {
		"x-rapidapi-key": PRICELINE_API_KEY,
		"x-rapidapi-host": "priceline-com2.p.rapidapi.com"
	}
    
    location_id = get_location_id(city_name)
    
    params = {
		"locationId": location_id,
		"checkIn": check_in,
		"checkOut": check_out,
		"rooms": str(rooms),
		"adults": str(adults)
	}
    
    response = requests.get(url, headers=headers, params=params)
    
    return response.json()


def find_hotels(city_name, check_in, check_out, rooms=1, adults=1):
    """
    Search for hotels in the destination city with specified dates.
    Args:
        city_name (str): The name of the city.
        check_in (str): Check-in date in YYYY-MM-DD format.
        check_out (str): Check-out date in YYYY-MM-DD format.
        rooms (int): Number of rooms. Default is 1.
        adults (int): Number of adults. Default is 1.
    Returns:
        str: The result of the search with info about hotels.
    """
    # Define the tool for searching flights with a single input
    search_hotels_tool = StructuredTool.from_function(
        func=lambda input: get_hotels_nearby(**eval(input)),  # Parse the input string as a dictionary
        name="SearchFlights",
        description="Search for hotels based on city name, check-in date, check-out date, number of rooms, and number of adults. Input should be a dictionary with 'city_name', 'check_in', 'check_out', 'rooms', and 'adults'.",
        parameters=[
            {"name": "input", "type": "string", "description": "A dictionary with 'city_name', 'check_in', 'check_out', 'rooms', and 'adults' as keys."},
        ]
    )

    # Initialize the LangChain agent with the tools
    llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, api_key=GEMINI_API_KEY)

    agent = initialize_agent([search_hotels_tool], llm, agent_type="zero-shot-react-description", verbose=True)

    # Use the agent to search for parks and activities matching interests
    result = agent.run(f"You are a travel agent searching for hotels. List 5 hotels with the best price to review ratio in {city_name} for the dates {check_in} to {check_out}. Include the number of rooms: {rooms} and adults: {adults}. Of the 5 best hotels give your recommendation and why. Return the results as if you were customer service. Make sure to include the address, check in and check out times, the price per night, total price for all nights, the brand, and amenities, the rating for each of the five options before your recommendation. If an error is thrown or no flights are available, just return 'available rooms were found' instead of an error message.")
    return result

if __name__ == "__main__":
    # print(get_location_id("Moab, UT"))  # Example city name
    # print(get_hotels_nearby("New York", "2025-05-27", "2025-05-30", rooms=1, adults=1))
    print(find_hotels("New York", "2025-05-27", "2025-05-30", rooms=1, adults=1))