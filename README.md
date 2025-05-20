=========================
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

---

## 🧰 Setup Instructions

1. Clone the repo  
2. Set up your environment variables (`.env`) for API keys  
3. Install dependencies:

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

## 👥 Team

Final Project – AI Bootcamp 2025  
Built by: 
Don Harrison
Hunter Klinglesmith
Dax Kelson
Liam Sloan

UofU | AI Bootcamp Final Project | 2025
