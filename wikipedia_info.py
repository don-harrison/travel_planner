from langchain_community.document_loaders import WikipediaLoader
from langchain_core.documents import Document
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_llm_string(location: str, interests: str, limit=10) -> list[Document]:
    """
    Loads Wikipedia documents and asks Gemini to extract interesting places to visit.
    Returns the Gemini-generated answer wrapped as a Document.
    """
    # Step 1: Load docs
    raw_docs = WikipediaLoader(
        query=location,
        load_max_docs=limit,
        load_all_available_meta=True,
    ).load()

    docs = [
        doc if isinstance(doc, Document) else Document(page_content=str(doc), metadata={})
        for doc in raw_docs
    ]

    llm = ChatGoogleGenerativeAI(
        google_api_key=GEMINI_API_KEY,
        model="gemini-2.0-flash",
        temperature=0.0,
    )

    prompt = ChatPromptTemplate.from_template("Answer the question {question} using the provided documents as a reference. Return list of places from the documents: {context}")
    chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
    query  = "What are some interesting places to visit in {destination}? I am interested in " + interests
    
    result = chain.invoke({"context": docs, "question": query})

    return result