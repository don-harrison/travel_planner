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
    return _fetch_directions(api_key, origin, [], destination)

def get_directions_via_waypoints(api_key, origin, waypoints, destination, optimize=False):
    """
    Retrieves step-by-step directions from origin, through each waypoint in order,
    to the final destination.

    :param api_key: Your Google Maps API key.
    :param origin: Starting location as a string.
    :param waypoints: List of intermediate locations as strings.
    :param destination: Final destination as a string.
    :param optimize: If True, lets Google reorder waypoints for the shortest route.
    :return: List of tuples with (instruction, approx_address) for the full route.
    """
    return _fetch_directions(api_key, origin, waypoints, destination, optimize=optimize)

def _fetch_directions(api_key, origin, waypoints, destination, optimize=False):
    """
    Internal helper that builds the Directions API call with optional waypoints.
    """
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "key": api_key,
        "units": "metric"
    }
    if waypoints:
        # join with '|' and optionally prefix with "optimize:true|"
        wp_string = "|".join(waypoints)
        if optimize:
            wp_string = "optimize:true|" + wp_string
        params["waypoints"] = wp_string

    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        raise Exception(f"Google Maps API error: {response.status_code} - {response.text}")

    data = response.json()
    if data.get("status") != "OK":
        raise Exception(f"Google Maps API returned status: {data.get('status')}")

    steps_info = []
    # iterate through each leg (origin→wp1, wp1→wp2, …, lastWp→destination)
    for leg in data["routes"][0]["legs"]:
        for step in leg["steps"]:
            instruction = step.get("html_instructions", "")
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
    if data.get("status") == "OK" and data.get("results"):
        return data["results"][0]["formatted_address"]
    else:
        return f"Unknown location ({lat}, {lng})"