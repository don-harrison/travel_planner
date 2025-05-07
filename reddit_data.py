# 1. Load .env and env vars
from dotenv import load_dotenv
load_dotenv()
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 2. Document loaders (from the community package)
from langchain_community.document_loaders import PyPDFLoader, WikipediaLoader, RedditPostsLoader

# 3. Chain constructor and prompt template
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# 4. Chat models (moved out of core into partner packages)
from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain.chat_models import ChatOpenAI

# 5. Initialize your LLM
if GEMINI_API_KEY:
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0.0,
    )

# # 7. Load Wikipedia pages into Documents
wiki_topic = "Salt Lake, Provo, Spanish Fork"
wiki_docs  = WikipediaLoader(
    query=wiki_topic,
    load_max_docs=10,
    load_all_available_meta=True
).load()
print([d.metadata["title"] for d in wiki_docs])


##REDDIT LOADER
# load using 'subreddit' mode
loader = RedditPostsLoader(
    client_id="use dons client id",
    client_secret="use dons client secret",
    user_agent="use dons user agent",
    categories=["new", "hot"],  # List of categories to load posts from
    mode="subreddit",
    search_queries=[
        "investing",
        "wallstreetbets",
    ],  # List of subreddits to load posts from
    number_posts=20,  # Default value is 10
)

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

reddit_docs = loader.load()

# 8. Build your prompt template
prompt = ChatPromptTemplate.from_template(
    "Answer the question {question} using the provided documents: {context}"
)

# 9. Create the “stuff” QA chain
chain = create_stuff_documents_chain(llm=llm, prompt=prompt)

# 10. Invoke it!
query  = "What are some interesting places to visit?"
result = chain.invoke({"context": reddit_docs, "question": query})
print(result)