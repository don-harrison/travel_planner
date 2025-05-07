# Additional imports for loading PDF documents and QA chain.

from langchain.document_loaders import PyPDFLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
# Additional imports for loading Wikipedia content.
from langchain_community.document_loaders import WikipediaLoader
# Initialize the model.
llm = ChatGoogleGenerativeAI(google_api_key=GEMINI_API_KEY, model=GEMINI_MODEL, temperature=0.0)
# Define the wikipedia topic as a string.
wiki_topic = "Salt Lake, Provo, Spanish Fork"
# Load the wikipedia results as documents, using a max of 10.
documents = WikipediaLoader(query=wiki_topic, load_max_docs=10, load_all_available_meta=True).load()
print([doc.metadata['title'] for doc in documents])
# Create the prompt template for the chain
prompt = ChatPromptTemplate.from_template("Answer the question {question} using the provided documents: {context}")
# Create the QA chain
chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
# Define a query as a string.
query = 'What are some interesting places to visit'
# Pass the documents and the query to the chain, and print the result.
result = chain.invoke({"context": documents, "question": query})
print(result)