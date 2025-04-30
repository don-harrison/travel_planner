import json
import os

DATA_FILE = "travel_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"destinations": [], "plans": {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)
