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