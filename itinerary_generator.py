from dotenv import load_dotenv
load_dotenv()

import os
import praw

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

from langchain_community.document_loaders import WikipediaLoader, RedditPostsLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

import reddit_data as rd
import nps_api_search as nps

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
    improved_itinerary: str
    final_itinerary: str


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

    docs.extend(reddit_docs)
    docs.extend(nps_docs)

    return docs


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

    # Node 1: generate initial itinerary
    def generate_itinerary_node(state: State) -> dict:
        itinerary = build_initial_itinerary(
            state, limit=state.get("limit", 10)
        )
        
        return {"itinerary": itinerary}

    # Node 2: add times to each activity
    def improve_itinerary_node(state: State) -> dict:
        msg = llm.invoke(
            f"Ensure this itinerary has times associated with each activity: {state['itinerary']}"
        )
        return {"improved_itinerary": msg.content}

    # Node 3: remove any unrelated content
    def polish_itinerary_node(state: State) -> dict:
        msg = llm.invoke(
            f"Remove any content in the response that is unrelated to times, days, and activities: "
            f"{state['improved_itinerary']}"
        )
        return {"final_itinerary": msg.content}

    # Build and wire the StateGraph
    workflow = StateGraph(State)
    workflow.add_node("generate_itinerary", generate_itinerary_node)
    workflow.add_node("improve_itinerary", improve_itinerary_node)
    workflow.add_node("polish_itinerary", polish_itinerary_node)
    workflow.add_edge(START, "generate_itinerary")
    workflow.add_edge("generate_itinerary", "improve_itinerary")
    workflow.add_edge("improve_itinerary", "polish_itinerary")
    workflow.add_edge("polish_itinerary", END)

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
        "final_itinerary": state.get("final_itinerary", "")
    })

    return result_state["final_itinerary"]
