# Natural Language Query Platform 🚀

## Overview

Natural Language Query Platform is an AI-powered application that enables users to interact with both unstructured documents and structured databases using plain English queries. The platform combines Document Question Answering (RAG-based retrieval) and Natural Language to SQL conversion into a single Streamlit dashboard.

The system allows users to:

* Upload PDFs and ask questions directly from documents.
* Upload CSV files or connect MySQL databases.
* Generate SQL queries automatically using LLMs.
* Retrieve intelligent and context-aware answers.

This project demonstrates the practical implementation of NLP, semantic search, vector databases, and local Large Language Models.

---

# Features ✨

## Document Q&A Module

* Upload PDF, DOCX, and TXT files
* Semantic search using FAISS vector database
* Context-aware answer generation
* Retrieval-Augmented Generation (RAG)
* Local LLM integration using Ollama

## Database Q&A Module

* Query CSV files using natural language
* MySQL database connectivity
* Automatic SQL query generation
* Execute generated SQL queries
* Display tabular query results

## Integrated Dashboard

* Streamlit-based interactive UI
* Separate tabs for Document Q&A and Database Querying
* Real-time response generation
* User-friendly workflow

---

# Technologies Used 🛠️

| Technology            | Purpose                        |
| --------------------- | ------------------------------ |
| Python                | Core development               |
| Streamlit             | Frontend dashboard             |
| LangChain             | RAG pipeline & LLM integration |
| FAISS                 | Vector similarity search       |
| Sentence Transformers | Embedding generation           |
| Ollama                | Local LLM inference            |
| TinyLLaMA / Mistral   | Natural language processing    |
| MySQL                 | Structured database querying   |
| SQLite                | CSV query execution            |
| Pandas                | Data handling                  |
| PyMuPDF               | PDF text extraction            |

---

# Project Structure 📁

natural-language-query-platform/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── nlquery-project1/
│   ├── dqa.py
│   ├── embed_helper.py
│   ├── llm_helper.py
│   └── other source files
│
├── structured_query_app/
│   ├── app.py
│   ├── mysql_helper.py
│   ├── query_generator.py
│   └── other source files
│
├── Screenshots/
│   ├── dashboard.png
│   ├── document_qa.png
│   └── sql_output.png

---

# How It Works ⚙️

## Part 1: Document Question Answering

1. User uploads a document.
2. Text is extracted and cleaned.
3. Documents are split into chunks.
4. Embeddings are generated using Sentence Transformers.
5. FAISS stores embeddings for semantic retrieval.
6. Relevant chunks are retrieved.
7. Local LLM generates final natural language answers.

## Part 2: Database Querying

1. User uploads CSV or connects MySQL database.
2. Database schema is extracted.
3. User asks questions in plain English.
4. LLM converts NL → SQL.
5. SQL query executes automatically.
6. Results are displayed in tabular format.

---

# Installation & Setup 💻

## Clone Repository

git clone https://github.com/your-username/natural-language-query-platform.git

cd natural-language-query-platform

---

## Create Virtual Environment

python -m venv venv

### Activate Environment

#### Windows

venv\Scripts\activate

---

# Install Dependencies

pip install -r requirements.txt


---

# Install Ollama

Download and install Ollama:

https://ollama.com


# Pull Lightweight Model

ollama pull tinyllama

---

# Run Streamlit Application

streamlit run app.py

---

# Sample Queries 💬

## Document Q&A

* "What is the objective of the report?"
* "Provide the conclusion from the document."

## Database Q&A

* "Show employees with highest salary"
* "Count total employees in IT department"

---


# Key Learnings 📚

* Natural Language Processing (NLP)
* Retrieval-Augmented Generation (RAG)
* Vector Databases using FAISS
* Semantic Search
* Natural Language to SQL Conversion
* Local LLM Integration
* Streamlit Dashboard Development

---

# Future Improvements 🚀

* Multi-document querying
* Advanced analytics and charts
* Cloud deployment
* User authentication
* Better LLM optimization
* Multi-user support

---

# Author 👩‍💻

Apeksha Tiwari
B.Tech CSE Student
Graphic Era Hill University

---

# License 📄

This project is developed for educational and learning purposes.
