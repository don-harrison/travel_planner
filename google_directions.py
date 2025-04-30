import requests

def get_directions(api_key, origin, destination):
    """
    Connects to the Google Maps Directions API and retrieves step-by-step directions
    from origin to destination.

    :param api_key: Your Google Maps API key.
    :param origin: Starting location as a string (e.g., "New York, NY").
    :param destination: Ending location as a string (e.g., "Boston, MA").
    :return: List of tuples with (instruction, approx_address).
    """
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "key": api_key,
        "units": "metric"
    }

    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        raise Exception(f"Google Maps API error: {response.status_code} - {response.text}")

    data = response.json()
    if data["status"] != "OK":
        raise Exception(f"Google Maps API returned status: {data['status']}")

    steps_info = []

    for leg in data["routes"][0]["legs"]:
        for step in leg["steps"]:
            instruction = step["html_instructions"]
            lat = step["end_location"]["lat"]
            lng = step["end_location"]["lng"]
            address = reverse_geocode(api_key, lat, lng)
            steps_info.append((instruction, address))

    return steps_info

def reverse_geocode(api_key, lat, lng):
    """
    Reverse geocodes a lat/lng coordinate into a human-readable address.

    :param api_key: Your Google Maps API key.
    :param lat: Latitude of the location.
    :param lng: Longitude of the location.
    :return: A formatted address string.
    """
    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": f"{lat},{lng}",
        "key": api_key
    }

    response = requests.get(geocode_url, params=params)
    if response.status_code != 200:
        return f"Unknown location ({lat}, {lng})"

    data = response.json()
    if data["status"] == "OK" and data["results"]:
        return data["results"][0]["formatted_address"]
    else:
        return f"Unknown location ({lat}, {lng})"
