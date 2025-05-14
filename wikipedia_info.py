from langchain.document_loaders import PyPDFLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import WikipediaLoader
from langchain_google_genai import ChatGoogleGenerativeAI

def get_wikipedia_based_answer(
    wiki_topic,
    question,
    google_api_key,
    model="gemini-pro",
    max_docs=10,
    temperature=0.0
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
    try:
        # Initialize Gemini model
        llm = ChatGoogleGenerativeAI(
            google_api_key=google_api_key,
            model=model,
            temperature=temperature
        )

        # Load Wikipedia documents using fuzzy search
        documents = WikipediaLoader(
            query=wiki_topic,
            load_max_docs=max_docs,
            load_all_available_meta=True
        ).load()

        titles = [doc.metadata['title'] for doc in documents]

        # Prepare prompt and chain
        prompt = ChatPromptTemplate.from_template(
            "Answer the question {question} using the provided documents: {context}"
        )
        chain = create_stuff_documents_chain(llm=llm, prompt=prompt)

        # Run chain and return result
        result = chain.invoke({"context": documents, "question": question})
        return {
            "answer": result,
            "used_titles": titles
        }

    except Exception as e:
        return {
            "error": str(e)
        }
