import os
import requests
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.agents import initialize_agent
from langchain.tools import Tool
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from langchain.tools import StructuredTool
from langchain.tools import Tool
import pandas as pd

NPS_API_KEY = os.getenv("NPS_KEY")
NPS_API_URL = "https://developer.nps.gov/api/v1/parks"

# Load environment variables.
load_dotenv()

# Set the model name for our LLMs.
GEMINI_MODEL = "gemini-2.0-flash"

# Store the API key in a variable.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def get_city_coordinates(city_name):
    """
        Get the latitude and longitude of a city using Nominatim geocoder.
        Args:
            city_name (str): The name of the city to geocode.
        Returns:
            tuple: A tuple containing the latitude and longitude of the city.
    """
    geolocator = Nominatim(user_agent="my_unique_application_name")
    location = geolocator.geocode(city_name)
    if location:
        return (location.latitude, location.longitude)
    return None

def get_parks_near_city(city_name, max_distance_km=100):
    """
        Get national parks within a certain distance of a city.
        Args:
            city_name (str): The name of the city to search near.
            max_distance_km (int): The maximum distance in kilometers to search for parks.
        Returns:
            list: A list of nearby parks and their distances from the city.
    """

    city_coords = get_city_coordinates(city_name)
    if not city_coords:
        return f"Could not find coordinates for {city_name}."

    params = {
        "limit": 1000,  # Fetch a wider range of parks
        "api_key": NPS_API_KEY
    }
    
    response = requests.get(NPS_API_URL, params=params)
    if response.status_code == 200:
        parks = response.json()["data"]
        nearby_parks = []

        for park in parks:
            if "latLong" in park and park["latLong"]:
                # Extract park coordinates
                lat_lon = park["latLong"].replace("lat:", "").replace("long:", "").split(",")
                park_coords = (float(lat_lon[0]), float(lat_lon[1]))
                distance = geodesic(city_coords, park_coords).km

                if distance <= max_distance_km:
                    nearby_parks.append({
                        "name": park["fullName"],
                        "distance_km": round(distance, 2),
                        "park_code": park["parkCode"]
                    })

        return nearby_parks if nearby_parks else f"No national parks found within {max_distance_km} km of {city_name}."
    else:
        return f"Error: {response.status_code}"



def NPS_API_Request_by_Park(request_type, park_code):
    """
        Function to make a request to the NPS API based on the request type and park code.
        Args:
            request_type (str): The type of request to make (e.g., parks, activities, places, thingstodo, events, newsreleases, visitorcenters, feespasses, tours, amenities).
            park_code (str): The park code to search for.
    """
    NPS_API_URL = "https://developer.nps.gov/api/v1/" + request_type

    params = {
        "parkCode": park_code,
        "api_key": NPS_API_KEY
    }

    response = requests.get(NPS_API_URL, params=params)
        
    if response.status_code == 200:
        requested_info = response.json()["data"]
        return pd.DataFrame(requested_info)
    else:
        print("Error: {response.status_code}")
        return None

# print("Parks Nearby: ", get_parks_near_city("St George, UT", max_distance_km=200), "\n")
# print("Tours at Park: ", NPS_API_Request_by_Park("tours", "arch"))
# national_park_search_near_city("Moab, UT", max_distance_km=100, interests=["hiking", "rock climbing"])

from langchain.tools import StructuredTool

def search_parks_and_interests(city_name, interests, max_distance_km=100):
    """
    Search for national parks near a city and find activities matching user interests.
    
    Args:
        city_name (str): The name of the city to search near.
        interests (list): A list of user interests.
        max_distance_km (int): The maximum distance in kilometers to search for parks.
    
    Returns:
        str: The result of the search with info about parks and activities.
    """
    # Define the tool for searching parks near a city with a single input
    search_parks_tool = StructuredTool.from_function(
        func=lambda input: get_parks_near_city(**eval(input)),  # Parse the input string as a dictionary
        name="SearchParksNearCity",
        description="Search for national parks within a certain distance of a city. Input should be a dictionary with 'city_name' and 'max_distance_km'.",
        parameters=[
            {"name": "input", "type": "string", "description": "A dictionary with 'city_name' and 'max_distance_km' as keys."}
        ]
    )

    # Define the tool for making additional API requests with a single input
    nps_request_tool = StructuredTool.from_function(
        func=lambda input: NPS_API_Request_by_Park(**eval(input)),  # Parse the input string as a dictionary
        name="NPS_API_Request_by_Park",
        description="Request additional information from the NPS API for a given park. Input should be a dictionary with 'request_type', and 'park_code'. Example request types include parks, activities, places, thingstodo, events, newsreleases, visitorcenters, feespasses, tours, amenities.",
        parameters=[
            {"name": "input", "type": "string", "description": "A dictionary with 'request_type', and 'park_code' as keys."}
        ]
    )

    # Initialize the LangChain agent with the tools
    tools = [search_parks_tool, nps_request_tool]

    llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, api_key=GEMINI_API_KEY)

    agent = initialize_agent(tools, llm, agent_type="zero-shot-react-description", verbose=True)

    # Use the agent to search for parks and activities matching interests
    result = agent.run(f"You are an expert travel blogger that specializes in national parks. Your goal is to help your friends plan visits to national parks near the location that they are travelling to and based on what they like to do. Find national parks near {city_name} within {max_distance_km} km. Then using requests for thingstodo in the park and their activities find items that match the following interests: {interests}. Then for the all the parks that match the interests and also provide information about the park including a summary of the park and some specific examples of the interests. For example, if the interest is hiking, provide some specific trails or locations within the parks that are great for hiking.")
    return result

# Example usage
if __name__ == "__main__":

    # print("Parks Nearby: ", get_parks_near_city("St George, UT", max_distance_km=200), "\n")
    # print("Tours at Park: ", NPS_API_Request_by_Park("tours", "arch"))

    # city_name = "Washington DC"
    # interests = ["history", "tours", "architecture"]

    city_name = "Moab, UT"
    interests = ["hiking", "rock climbing", "mountain biking", "scenic views", "wildlife watching"]

    result = search_parks_and_interests(city_name, interests)
    print(result)