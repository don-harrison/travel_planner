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
from IPython.display import Image, display

# Graph state
class State(TypedDict):
    interests: str
    itinerary: str
    improved_itinerary: str
    final_itinerary: str

import reddit_data as rd
# import national_parks_data as npd
# import wikipedia_data as wd
# import google_maps_data as gmd

def get_documents(destination, interests, limit=10):
    docs = []
    # Load Reddit posts
    reddit_strings = rd.get_llm_string(destination, interests, limit=limit)
    reddit_docs = [Document(page_content=text) for text in reddit_strings]
    # wikipedia_docs = wd.get_llm_string(destination, interests, limit=limit)
    # national_parks_docs = npd.get_llm_string(destination, interests, limit=limit)
    
    #Google Maps needs to take in a list of waypoints given by llm returns for possible destinations
    # google_maps_docs = gmd.get_llm_string(destination, interests, limit=limit)

    docs.extend(reddit_docs)
    # docs.extend(wikipedia_docs)
    # docs.extend(national_parks_docs)

    return docs

#TODO: Add constitutional to make sure the llm produces an itinerary?
def build_itinerary(destination, 
                    interests, 
                    prompt = "Answer the question {question} using the provided documents as a reference. Return list of places from the documents: {context}",
                    limit=10):
    if GEMINI_API_KEY:
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0.0,
        )

    prompt = ChatPromptTemplate.from_template(prompt)
    chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
    query  = "Create an itinerary for a trip to " + destination + " with the following interests: " + interests + ". Make sure each itinerary entry ends with \\n"
    docs = get_documents(destination, interests, limit=limit)
    result = chain.invoke({"context": docs, "question": query + " " + interests})

    return result

# Nodes
def generate_improved_itinerary(state: State):
    """First LLM call to generate initial itinerary"""
    if GEMINI_API_KEY:
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0.0,
        )

    def generate_itinerary(state: State):
        itinerary = llm_call(f"Write an itinerary about {state['interests']}")
        return {"itinerary": itinerary}

    def improve_itinerary(state: State):
        """Second LLM call to improve the joke"""

        msg = llm.invoke(f"Ensure this itinerary has times associated with each activity: {state['itinerary']}")
        return {"improved_itinerary": msg.content}


    def polish_itinerary(state: State):
        """Third LLM call for final polish"""

        msg = llm.invoke(f"Remove anything unrealated to times, days, and activities: {state['improved_itinerary']}")
        return {"final_joke": msg.content}


    # Build workflow
    workflow = StateGraph(State)

    # Add nodes
    workflow.add_node("generate_joke", generate_joke)
    workflow.add_node("improve_joke", improve_joke)
    workflow.add_node("polish_joke", polish_joke)

    # Add edges to connect nodes
    workflow.add_edge(START, "generate_joke")
    workflow.add_conditional_edges(
        "generate_joke", check_punchline, {"Fail": "improve_joke", "Pass": END}
    )
    workflow.add_edge("improve_joke", "polish_joke")
    workflow.add_edge("polish_joke", END)

    # Compile
    chain = workflow.compile()

    # Show workflow
    display(Image(chain.get_graph().draw_mermaid_png()))

    # Invoke
    state = chain.invoke({"topic": "cats"})
    print("Initial joke:")
    print(state["joke"])
    print("\n--- --- ---\n")
    if "improved_joke" in state:
        print("Improved joke:")
        print(state["improved_joke"])
        print("\n--- --- ---\n")

        print("Final joke:")
        print(state["final_joke"])
    else:
        print("Joke failed quality gate - no punchline detected!")
    msg = llm.invoke(f"Write a short joke about {state['topic']}")
    return {"joke": msg.content}

# Define LLM call
def llm_call(prompt: str):
    return llm.invoke(HumanMessage(content=prompt)).content

# Nodes
def generate_joke(state: State):
    joke = llm_call(f"Write a short joke about {state['topic']}")
    return {"joke": joke}

def check_punchline(state: State):
    """Gate function to check if the joke has a punchline"""
    joke = state["joke"]
    if "?" in joke or "!" in joke:
        return "Fail"
    return "Pass"

def improve_joke(state: State):
    improved = llm_call(f"Make this joke funnier by adding wordplay: {state['joke']}")
    return {"improved_joke": improved}

def polish_joke(state: State):
    polished = llm_call(f"Add a surprising twist to this joke: {state['improved_joke']}")
    return {"final_joke": polished}

# Build workflow
workflow = StateGraph(State)

workflow.add_node("generate_joke", generate_joke)
workflow.add_node("improve_joke", improve_joke)
workflow.add_node("polish_joke", polish_joke)

workflow.set_entry_point("generate_joke")
workflow.add_conditional_edges(
    "generate_joke", check_punchline, {"Fail": "improve_joke", "Pass": END}
)
workflow.add_edge("improve_joke", "polish_joke")
workflow.add_edge("polish_joke", END)

# Compile
chain = workflow.compile()

# Visualize
display(Image(chain.get_graph().draw_mermaid_png()))

# Invoke chain
state = chain.invoke({"topic": "cats"})

print("Initial joke:")
print(state.get("joke", "[No joke generated]"))

if "improved_joke" in state:
    print("\nImproved joke:")
    print(state["improved_joke"])
    print("\nFinal joke:")
    print(state["final_joke"])
else:
    print("\nJoke passed the quality gate — no improvement needed.")