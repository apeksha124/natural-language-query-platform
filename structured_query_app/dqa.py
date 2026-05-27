import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
import tempfile

# Page setup
st.set_page_config(page_title="📘 NLQ Docs", layout="wide")
st.markdown("""
    <style>
    html, body {
        background-color: #f2f5f7;
    }
    .stApp {
        font-family: "Segoe UI", sans-serif;
        padding: 1.5rem;
    }
    .block-container {
        padding: 2rem;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.08);
    }
    .stTextInput > div > div > input {
        font-size: 16px;
        padding: 8px;
    }
    .stButton > button {
        background-color: #0066cc;
        color: white;
        font-weight: bold;
        border-radius: 5px;
    }
    .stMarkdown h1 {
        font-size: 2rem;
        color: #004080;
    }
    .stMarkdown h3, .stSubheader {
        margin-top: 2rem;
        color: #006400;
    }
    </style>
""", unsafe_allow_html=True)

# App header
st.title("📘 NLQ Docs: Ask Questions from PDF Files")
st.caption("Upload a geology report and ask clear questions. Uses a local model to provide answers.")

question_answer = None

# Sidebar for upload
with st.sidebar:
    st.header("📄 Upload Your PDF")
    user_file = st.file_uploader("Upload geological PDF", type=["pdf"])

# Handle file
if user_file:
    with st.spinner("Reading your document..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
            temp.write(user_file.read())
            temp_path = temp.name

        pdf_loader = PyPDFLoader(temp_path)
        pages = pdf_loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
        split_pages = splitter.split_documents(pages)

        embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vector_store = FAISS.from_documents(split_pages, embedder)

        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""
You are a helpful geology assistant. Answer only using the information below.
If no answer is available, respond with: "Not found in document."

Context:
{context}

Question:
{question}

Answer:"""
        )

        model = Ollama(model="mistral")

        question_answer = RetrievalQA.from_chain_type(
            llm=model,
            retriever=vector_store.as_retriever(search_kwargs={"k": 2}),
            chain_type="stuff",
            chain_type_kwargs={"prompt": prompt},
        )

    st.success("✅ Document uploaded and ready.")

# Helper function
def clean_response(user_question, raw_answer):
    if isinstance(raw_answer, dict):
        response = raw_answer.get("result", "").strip()
    else:
        response = str(raw_answer).strip()

    if not response or response.lower() in ["not found in document", "not found in the document"]:
        return "Not found in document."

    q_text = user_question.strip(" ?").lower()
    a_text = response.strip().rstrip(".")

    if a_text.lower().startswith(q_text):
        a_text = a_text[len(q_text):].lstrip(":,. ")

    return f"{a_text}."

# Q&A interface
if question_answer:
    st.subheader("❓ Ask your question below")
    user_question = st.text_input("Enter your question about the PDF:", placeholder="e.g. What is the surface location?")
    if user_question:
        with st.spinner("Searching..."):
            raw_result = question_answer.invoke({"query": user_question})
            final_output = clean_response(user_question, raw_result)
            st.subheader("✅ Answer:")
            st.success(final_output)
