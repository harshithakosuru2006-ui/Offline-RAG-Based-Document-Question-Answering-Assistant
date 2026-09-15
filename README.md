# SmartDoc AI-Offline-RAG-Based-Document-Question-Answering-Assistant


SmartDoc AI is an offline document question-answering application that uses Retrieval-Augmented Generation (RAG) to answer questions from uploaded PDF documents.

The system extracts text from PDF files, divides the text into smaller chunks, converts the chunks into embeddings, performs semantic vector search using FAISS, retrieves relevant information, and generates an answer using a locally running LLM through Ollama.

---

## Features

- Upload PDF documents
- Extract text from PDF files
- Text chunking
- Text embeddings
- Semantic vector search
- FAISS vector database
- Retrieval-Augmented Generation
- Local LLM using Ollama
- Context-aware answers
- Source and page references
- Flask REST API
- Simple web interface
- Works without external LLM APIs

---

## Technologies Used

- Python
- Flask
- HTML
- CSS
- JavaScript
- PyPDF
- Sentence Transformers
- FAISS
- Ollama
- Local LLM
- REST APIs
- RAG

---

## System Architecture

```text
                USER
                  |
                  v
        HTML/CSS/JavaScript
                  |
                  v
           Flask Backend
             /       \
            /         \
     Upload PDF       Ask Question
         |                  |
         v                  v
   Extract Text       Query Embedding
         |                  |
         v                  v
      Chunking         FAISS Search
         |                  |
         v                  v
     Embeddings        Relevant Chunks
         |                  |
         v                  v
    FAISS Index       Context Creation
                            |
                            v
                       Ollama LLM
                            |
                            v
                         Answerv
