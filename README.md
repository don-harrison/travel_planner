Google Maps API
AMADEUS for booking hotels or
https://developer.hotelbeds.com/documentation/hotels/booking-api/
SerpAPI for google flights
WeatherAPI for checking weather

https://www.postman.com/amadeus4dev/amadeus-for-developers-s-public-workspace/collection/kquqijj/amadeus-for-developers

https://serpapi.com/google-flights-api

## Setup
Install requirements.txt: 
    pip install -r requirements.txt
open main.py and run the python script

## Features

1. Page with List of Destinations and ability to add to list. -DON
2. Able to click on destinations and go to a page with an input for interests and a input for time period to submit to llm. -DON
3. agentic ai takes in date range and interests:
    1. Uses Wikipedia, Reddit, TripAdvisor api to see whats in the area of destination that aligns with interests.
    2. Once the LLM forms list of possible attractions, use google maps to generate possible travel guide.
    3. Optional, have llm use location inputs from google maps directions to find more possible attractions.
    4. Optional, add weather api to suggest trip timeline modifications around weather
4. llm will use google flights api(serpapi) and kayak api or some hotel booking service to find reservations for the area.
5. Will return an itinerary and the tickets you need to buy for the trip all in one page.
    5. Optionally, return a travel blog style page of the trip as if a travel agency is working for you.
6. have an llm prompt user for responses to assist agentic ai in prompting context

## Minimal Viable Product (MVP)
1. Page with List of Destinations and ability to add to list.
2. Able to click on destinations and go to a page with an input for interests and a input for time period to submit to llm.
3. Returns itinerary
4. itinerary location generator:
    - Manage some kind of list of info source locations, either libraries or apis or python functions.
        - Google Maps   -Don
        - Reddit        -Liam and/or Don
        - Wikipedia     -Dax 
        - National Park Service - Hunter
    - There will be a python file dedicated to each "source". Each of these python files should have a to_llm_string function to return an string of info to feed into the LangChain context.
    - First Agent: Get List of interesting places. Will likely need to concat the "interests prompt" to the lang chain query to direct the llm.
    - Second Agent: Get approximate times for each place
    - Third Agent: Use approximate to generate valid itinerary.
5. Add ability to reprompt.

## Resources
* https://github.com/faouzij/TrackMe/blob/master/airports.txt
### APIs
* https://www.nps.gov/subjects/developer/api-documentation.htm#/
* https://test.api.amadeus.com/v
