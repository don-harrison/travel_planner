# 🧭 Personalized Travel Planning Assistant

## 📌 Project Overview

This project is an AI-powered travel assistant that generates personalized multi-day itineraries based on a user’s selected destination and interests (e.g., hiking, food, fishing, history). It integrates structured and unstructured data from APIs and public content sources, and includes a graphical interface using KivyMD and MapView for enhanced user interaction.

---

## 🔍 How It Works

1. **User Input:** The user provides a destination and selects interests.
2. **Data Aggregation:**
   - **Reddit posts** are parsed using `praw` and loaded as searchable documents.
   - **Wikipedia, NPS API, and Rec.gov** provide factual summaries and outdoor activity listings.
   - **OpenRouteService** provides directions and travel time between locations.
   - **Hotel data** is provided via static placeholder entries in `hotel_info.py`.
3. **Itinerary Generation:**
   - LangChain pipelines build an itinerary based on interest matching.
   - LangGraph organizes the logic for input parsing → data matching → formatting.
4. **Output:** A structured, readable itinerary with 4–5 full days of activity planning.

---

## 💻 Technologies Used

| Category           | Tools & Libraries                                      |
|--------------------|--------------------------------------------------------|
| LLM & Orchestration| `LangChain`, `LangGraph`, `langchain_google_genai`     |
| Data Sources       | `praw` (Reddit), Wikipedia, NPS API, Rec.gov           |
| Routing & Mapping  | `openrouteservice`, `geopy`, `kivy_garden.mapview`     |
| UI Framework       | `KivyMD`, `.kv` layout files (`travel.kv`)             |
| Deployment         | `buildozer` (for Android packaging)                    |
| Utilities          | `dotenv`, `json`, `os`, `datetime`                     |

---

## 📦 File Overview

| File / Folder          | Description                                         |
|------------------------|-----------------------------------------------------|
| `main.py`              | Entry point that runs the full itinerary process    |
| `itinerary_generator.py` | Core logic for building the itinerary             |
| `google_directions.py` | Travel time/distance (OpenRouteService integration) |
| `nps_api_search.py`    | National Park Service API search                    |
| `rec_dot_gov_info.ipynb` | Notebook for Rec.gov park data exploration        |
| `reddit_data.py`, `reddit_documents.py` | Loads and structures Reddit content |
| `hotel_info.py`        | Static lodging recommendation logic                 |
| `flight_info.py`       | Mock/stub flight info                               |
| `travel.kv`            | Kivy GUI layout definition                          |
| `buildozer.spec`       | Android build config                                |
| `itinerary.txt`        | Example output itinerary                            |
| `requirements.txt`     | All necessary packages                              |

---

## 📈 Evaluation

Although this is not a predictive model, we evaluated our results by:
- Manually reviewing output itineraries to verify interest alignment.
- Checking for logistical feasibility (e.g., daily travel distances).
- Testing modular components independently (e.g., NPS API, route logic).
- Confirming app components rendered correctly in the Kivy GUI.
- Validating that output matched user intent across multiple test scenarios.

---

## 🚀 Future Development

- Add live scraping and sentiment filtering for Reddit.
- Expand and polish the KivyMD-based GUI; add touch interaction and completed MapView integration.
- Integrate real-time flight and lodging APIs like Amadeus or Booking.com.
- Enable itinerary saving, sharing, and export options (PDF, email, calendar).
- Optimize API requests using multithreading.
- Experiment with local LLM alternatives to Gemini for offline usage.

---
## 🧰 Setup Instructions

1. Clone the repo  
2. Set up your environment variables (`.env`) for API keys
   You will need to set the following keys:
      - GEMINI_API_KEY https://aistudio.google.com/app/apikey
      - REDDIT_CLIENT_ID https://old.reddit.com/prefs/apps
      - REDDIT_CLIENT_SECRET https://old.reddit.com/prefs/apps
      - REDDIT_USER_AGENT reddit.com
      - REDDIT_USERNAME reddit.com
      - REDDIT_PASSWORD reddit.com
      - NAV_API_KEY https://api.openrouteservice.org/
      - RAPIDAPI_KEY https://docs.rapidapi.com/docs/keys-and-key-rotation
      - AMADEUS_CLIENT_SECRET https://developers.amadeus.com/self-service
      - AMADEUS_API_KEY https://developers.amadeus.com/self-service
      - NPS_KEY https://www.nps.gov/subjects/developer/api-documentation.htm
      NOTE: Client Id and Client Secret and User Agent from creating an app at https://old.reddit.com/prefs/apps
      NOTE: Can Create a Reddit Account with reddit.com and use the username and password
4. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the app:

```bash
python main.py
```

5. (Optional) Build the Android app:

```bash
buildozer android debug
```
---
## 🔁 LangGraph Pipeline Overview

After fetching destination-related data from APIs, we pass it into LangChain to match locations more closely to the user's interests using prompt engineering. The refined set of documents is then passed into a LangGraph workflow to structure the itinerary generation process.

LangGraph organizes this flow into sequential LLM-powered nodes, each transforming or enriching the state:

1. **Generate Itinerary** – Creates a draft multi-day plan from interest-aligned documents.
2. **Add Flight Info** – Decides whether air travel is relevant and incorporates flight details if useful.
3. **Add Hotel Info** – Recommends accommodations unless the user has preferences like camping.
4. **Improve Itinerary** – Adds time blocks and adjusts the order of activities for realism.
5. **Polish Itinerary** – Cleans up extraneous text and ensures a readable daily format.
6. **Generate Sales Pitch** – Produces a blog-style summary to "sell" the trip, stored in state for final output.

This node-based orchestration allows for clean transitions, incremental LLM reasoning, and safeguards against hallucination. Each step is modular and traceable, with LangChain components providing flexible prompt templating and execution under the hood.

---

## 🦖 Early Challenges

Originally, we planned to scrape data directly from travel websites and community forums using botting techniques. We ran into site restrictions against scraping and kept trying to overcome it with things like sites 'robot.txt' for polite scraping.

Resolution:
We pivoted to using:
- The official NPS API for parks data
- Public Reddit posts via PRAW
- Wikipedia summary extraction

This gave us reliable, structured, and rate-limit-friendly content pipelines, we just had to be sure to limit our requests, which is easy to do since our app isn't very greedy so far.

---

## 🤖 Philosophy

The project explores whether modern LLMs can effectively format frequently updated, unstructured, or third-party data in real-time without any model training, similiar to RAG (Retrieval-Augmented Generation).

We believe that good-enough instruction-tuned LLMs, paired with a high-quality prompt pipeline and data retrieval system, are sufficient to generate user-aligned outputs from generic content.

---

## 👥 Team

Final Project – AI Bootcamp 2025  
Built by: 
Don Harrison
Hunter Klinglesmith
Dax Kelson
Liam Sloan

UofU | AI Bootcamp Final Project | 2025
