import requests

def get_wikipedia_extract(title, lang="en"):
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get("extract")
    else:
        return f"Error: {response.status_code}"

extract = get_wikipedia_extract("Paris")
print("Extract:", extract)