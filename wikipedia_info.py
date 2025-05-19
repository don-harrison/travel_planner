from langchain.document_loaders import PyPDFLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import WikipediaLoader
from langchain_google_genai import ChatGoogleGenerativeAI

def get_wikipedia_based_answer(
    location,
    interests,
    google_api_key,
    max_docs=10
):
    """
    Retrieves information from Wikipedia using fuzzy topic search and answers a question using LLM.
    
    Parameters:
        wiki_topic (str): Search terms or topic for Wikipedia search.
        question (str): Question to answer using the documents.
        google_api_key (str): Your Google API key for Gemini.
        model (str): Gemini model to use.
        max_docs (int): Maximum number of documents to load.
        temperature (float): LLM generation temperature.
        
    Returns:
        dict: {
            'answer': str,
            'used_titles': list of str
        }
    """
    model="gemini-2.0-flash"
    try:
        # Initialize Gemini model
        llm = ChatGoogleGenerativeAI(
            google_api_key=google_api_key,
            model=model
        )

        # Load Wikipedia documents using fuzzy search
        wiki_docs = WikipediaLoader(
            query=location,
            load_max_docs=max_docs,
            load_all_available_meta=True
        ).load()


        prompt = ChatPromptTemplate.from_template("Answer the question {question} using the provided documents as a reference. Return list of places from the documents: {context}")
        chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
        query  = "What are some interesting places to visit in {destination}? I am interested in " + interests
        context = "\n\n".join([doc.page_content for doc in wiki_docs])
        result = chain.invoke({"context": context, "question": query})

        return result

    except Exception as e:
        return {
            "error": str(e)
        }
