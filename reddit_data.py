# 1. Load .env and env vars
from dotenv import load_dotenv
load_dotenv()
import os
import praw

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")

print(GEMINI_API_KEY,REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT)
# 2. Document loaders (from the community package)
from langchain_community.document_loaders import WikipediaLoader, RedditPostsLoader

# 3. Chain constructor and prompt template
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# 4. Chat models (moved out of core into partner packages)
from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.chat_models import ChatOpenAI

def get_llm_string(destination, interests, limit=10):
    '''
    Get LLM string from Reddit posts based on destination and interests.
    '''

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD,
    )

    #Get list of subreddits to look for documents Salt Lake City
    subs = reddit.subreddits.search(destination, limit=limit)
    subs_list = []

    for s in subs:
        subs_list.append(s.display_name)
        print(s.display_name)

    #Setup Gemini LLM
    if GEMINI_API_KEY:
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0.0,
        )

    reddit_docs = []

    ##REDDIT LOADER
    # load using 'subreddit' mode
    for subreddit in subs_list:
        loader = RedditPostsLoader(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
            categories=["new", "hot"],  # List of categories to load posts from
            mode="subreddit",
            search_queries=[subreddit],  # List of subreddits to load posts from
            number_posts=limit,  # Default value is 10
        )
        
        tries = 0
        while tries < 3:  # Retry up to 3 times
            try:
                for doc in loader.load():
                    reddit_docs.append(doc)
                break  # Exit the loop if loading is successful
            except Exception as e:
                print(f"Error loading subreddit {subreddit}: {e}")
                tries += 1

    prompt = ChatPromptTemplate.from_template("Answer the question {question} using the provided documents as a reference. Return list of places from the documents: {context}")
    chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
    query  = "What are some interesting places to visit in {destination}? I am interested in " + interests
    
    result = chain.invoke({"context": reddit_docs, "question": query})

    return result