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

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
    username=REDDIT_USERNAME,
    password=REDDIT_PASSWORD,
)

# verify that you’re logged in as that user
print("Logged in as:", reddit.user.me())

subs = reddit.subreddits.search("salt lake city travel", limit=50)
subs_list = []
for s in subs:
    subs_list.append(s.display_name)
    print(s.display_name)

# 5. Initialize your LLM
if GEMINI_API_KEY:
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0.0,
    )

# # # 7. Load Wikipedia pages into Documents
# wiki_topic = "Salt Lake, Provo, Spanish Fork"
# wiki_docs  = WikipediaLoader(
#     query=wiki_topic,
#     load_max_docs=10,
#     load_all_available_meta=True
# ).load()
# print([d.metadata["title"] for d in wiki_docs])

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
        number_posts=10,  # Default value is 10
    )
    
    tries = 0
    while tries < 3:  # Retry up to 5 times
        try:
            for doc in loader.load():
                reddit_docs.append(doc)
            break  # Exit the loop if loading is successful
        except Exception as e:
            print(f"Error loading subreddit {subreddit}: {e}")
            tries += 1

# # or load using 'username' mode
# loader = RedditPostsLoader(
#     client_id="YOUR CLIENT ID",
#     client_secret="YOUR CLIENT SECRET",
#     user_agent="extractor by u/Master_Ocelot8179",
#     categories=['new', 'hot'],
#     mode = 'username',
#     search_queries=['ga3far', 'Master_Ocelot8179'],         # List of usernames to load posts from
#     number_posts=20
#     )

# Note: Categories can be only of following value - "controversial" "hot" "new" "rising" "top"

# # 8. Build your prompt template
prompt = ChatPromptTemplate.from_template(
    "Answer the question {question} using the provided documents as a reference. Return list of places that match interests expressed in the following documents. Keep response limited to a list of places and descriptions described in the documents: {context}"
)

# # 9. Create the “stuff” QA chain
chain = create_stuff_documents_chain(llm=llm, prompt=prompt)

# # 10. Invoke it!
query  = "What are some interesting places to visit in Salt Lake City, Utah? I am interested in hiking and food"
result = chain.invoke({"context": reddit_docs, "question": query})
print(result)