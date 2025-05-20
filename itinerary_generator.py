from dotenv import load_dotenv
load_dotenv()

import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

import reddit_data as rd
import nps_api_search as nps
import flight_info as fi
import hotel_info as hi
import wikipedia_info as wi
from collections import defaultdict
import re
import time
from kivy.logger import Logger
from utils.storage import load_data, save_data

def safe_invoke(llm, prompt, delay=2, retries=3):
    """
    Calls LLM with delay and retry logic to avoid hitting rate limits.
    """
    for attempt in range(retries):
        try:
            time.sleep(delay)
            return llm.invoke(prompt)
        except Exception as e:
            if "ResourceExhausted" in str(e) and attempt < retries - 1:
                delay *= 2
                print(f"[Retrying] Quota hit, retrying in {delay} seconds...")
                continue
            raise


# Define the shape of the workflow state
class State(TypedDict):
    destination: str
    prompt: str
    origin: str
    date_start: str
    date_end: str
    interests: str
    limit: int
    itinerary: str
    itinerary_with_flight: str
    interest_with_hotel: str
    improved_itinerary: str
    final_itinerary: str
    sales_pitch: str


def get_waypoints_from_itinerary(steps, destination, data):
    """Send the raw itinerary steps to Gemini and return a list of non-empty lines."""

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0.0,
    )

    itinerary_text = "\n".join(steps)
    prompt = (
        "Take the following itinerary and extract the locations for each day. Add a \n\n character to the end of each location and add the word stop when the end of a day's activities is reached. The only permitted items in this list are locations and the word stop to delimit the end of a day's activities. Be specific with the location like 'destination,city,state'. Do not include any other information.\n\n"
        f"{itinerary_text}"
    )

    msg = safe_invoke(llm, prompt)
    Logger.info(f"Gemini Response: {msg.content}")
    
    # split into lines, strip blanks
    waypoints = [line.strip() for line in msg.content.splitlines() if line.strip()]

    Logger.info(f'Waypoints: {waypoints}')

    return waypoints

def extract_waypoint_schedule_from_gemini_output(steps, destination, data):
    """
    Turn the Gemini output into a dict of days → list of waypoints.
    
    Args:
        steps (list[str]): your original steps
    
    Returns:
        dict[str, list[str]]
    """
    if(len(data["plans"][destination]["daily_waypoints"]) > 0):
        # if we already have waypoints, return them
        Logger.info(f"Waypoints already exist for {destination}.")
        return data["plans"][destination]["daily_waypoints"]
    else:
        lines = get_waypoints_from_itinerary(steps, destination, data)
        schedule = {}
        day_count = 1
        current_day = None

        for line in lines:
            if line.lower() == "stop":
                # end current day
                current_day = None
                day_count += 1
                continue

            # start a new day if needed
            if current_day is None:
                current_day = f"Day {day_count}"
                schedule[current_day] = []

            # append this waypoint
            schedule[current_day].append(line)

        Logger.info(f"Extracted schedule: {schedule}")
        return schedule

def get_documents(destination: str, interests: str, limit: int = 10) -> list[Document]:
    """
    Fetch documents for the given destination and interests.
    Currently loads Reddit posts via reddit_data.
    """

    docs = []

    reddit_strings = rd.get_llm_string(destination, interests, limit=limit)
    reddit_docs = [Document(page_content=text) for text in reddit_strings]

    nps_strings = nps.search_parks_and_interests(destination, interests)
    
    nps_docs = [Document(page_content=text) for text in nps_strings]

    wikipedia_strings = wi.get_llm_string(destination, interests, limit=limit)
    wikipedia_docs = [Document(page_content=text) for text in wikipedia_strings]

    docs.extend(reddit_docs)
    docs.extend(nps_docs)
    docs.extend(wikipedia_docs)

    return docs

def get_flight_info(origin: str, destination: str, departure_date: str, return_date: str) -> str:
    """
    Get flight information for the itinerary.
    """
    return fi.find_flights(origin, destination, departure_date, return_date)

def get_hotel_info(city_name: str, check_in: str, check_out: str) -> str:
    """
    Get hotel information for the itinerary.
    """
    return hi.find_hotels(city_name, check_in, check_out)

def build_initial_itinerary(
    state,
    prompt_template: str = (
        "Answer the question {question} using the provided documents as a reference. "
        "Return list of places from the documents: {context}"
    ),
    limit: int = 10
) -> str:
    """
    Builds an initial itinerary using LLM over documents from get_documents.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0.0,
    )

    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = create_stuff_documents_chain(llm=llm, prompt=prompt)

    query = (
        f"Create an itinerary for a trip to {state['destination']}" +
        f"with the following interests: {state['interests']}. " +
        f"The person taking the trip is starting in {state['origin']}. " +
        f"The dates are from: {state['date_start']} to {state['date_end']}. " +
        "Make sure each itinerary entry ends with \n"
    )
    docs = get_documents(state["destination"], state["interests"], limit=limit)
    result = chain.invoke({"context": docs, "question": query})

    return result


def generate_improved_itinerary(state: State) -> str:
    """
    Orchestrates a 3-step LLM workflow to generate, improve, and polish an itinerary.
    """
    print(state)

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0.0,
    )

    flight_info = get_flight_info(origin = state["origin"], destination = state["destination"], departure_date = state["date_start"], return_date = state["date_end"])
    hotel_info =  get_hotel_info(city_name = state["destination"], check_in = state["date_start"], check_out = state["date_end"])

    # Node 1: generate initial itinerary
    def generate_itinerary_node(state: State) -> dict:
        itinerary = build_initial_itinerary(
            state, limit=state.get("limit", 10)
        )
        
        return {"itinerary": itinerary}
    
    def generate_itinerary_with_flight(state: State) -> dict:
        """
        Generate flight information.
        """
        query = (
            f"Decide if a flight is worth it for going from {state['origin']} to {state['destination']}." +
            f"If it is decided to use flights, include the flight information in the itinerary and adjust the itinerary accordingly. " + 
            flight_info
        )
        result = safe_invoke(llm, query)

        return result
    
    def generate_itinerary_with_hotel(state: State) -> dict:
        """
        Generate hotel information.
        """
        query = (
            f"If the user does not have camping as an interest, incorporate a recommended hotel into the itinerary." + 
            hotel_info
        )
        result = safe_invoke(llm, query)

        return result

    # Node 2: add times to each activity
    def improve_itinerary_node(state: State) -> dict:
        query = f"Ensure this itinerary has times associated with each activity: {state['itinerary']}"
        msg = safe_invoke(llm, query)

        return {"improved_itinerary": msg.content}

    # Node 3: remove any unrelated content
    def polish_itinerary_node(state: State) -> dict:
        query = f"Remove any content in the response that is unrelated to times, days, and activities: {state['improved_itinerary']}"
        msg = safe_invoke(llm, query)

        return {"final_itinerary": msg.content + "\n" + flight_info + "\n" + hotel_info}
    
    def sales_pitch_node(state: State) -> dict:
        """
        Final node to return the final itinerary as a sales pitch for the trip in an markup format.
        """
        query = (
            f"As a travel blogger in your free time, you are also a travel agent. Your goal is to sell this trip to a client. "
            f"Using the following itinerary, create the sales pitch for the trip: {state['final_itinerary']}"
            f"Describe the trip in a way that makes it sound exciting and fun. Tell them what experiences they will have."
            f"Don't include the itinerary, flight, or hotel information in the response and keep the response to 350 words or less. "
        )
        msg = safe_invoke(llm, query)

        return {"sales_pitch": msg.content + "\n\n" + state["final_itinerary"]}

    # Build and wire the StateGraph
    workflow = StateGraph(State)
    workflow.add_node("generate_itinerary", generate_itinerary_node)
    workflow.add_node("generate_itinerary_with_flight", generate_itinerary_with_flight)
    workflow.add_node("generate_itinerary_with_hotel", generate_itinerary_with_hotel)
    workflow.add_node("improve_itinerary", improve_itinerary_node)
    workflow.add_node("polish_itinerary", polish_itinerary_node)
    workflow.add_node("generate_sales_pitch", sales_pitch_node)
    workflow.add_edge(START, "generate_itinerary")
    workflow.add_edge("generate_itinerary", "generate_itinerary_with_flight")
    workflow.add_edge("generate_itinerary_with_flight", "generate_itinerary_with_hotel")
    workflow.add_edge("generate_itinerary_with_hotel", "improve_itinerary")
    workflow.add_edge("improve_itinerary", "polish_itinerary")
    workflow.add_edge("polish_itinerary", "generate_sales_pitch")
    workflow.add_edge("generate_sales_pitch", END)

    chain = workflow.compile()
    
    result_state = chain.invoke({
        "destination": state["destination"],
        "prompt": state.get("prompt", ""),
        "origin": state["origin"],
        "date_start": state["date_start"],
        "date_end": state["date_end"],
        "interests": state["interests"],
        "limit": state.get("limit", 10),
        "itinerary": state.get("itinerary", ""),
        "improved_itinerary": state.get("improved_itinerary", ""),
        "final_itinerary": state.get("final_itinerary", ""),
        "sales_pitch": state.get("sales_pitch", "")
    })

    return result_state["sales_pitch"]
