import os
import requests
import faiss
import numpy as np

from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


app = Flask(__name__)

UPLOAD_FOLDER = "documents"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024


# -----------------------------
# Configuration
# -----------------------------

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2"
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "all-MiniLM-L6-v2"
)


# -----------------------------
# Load Embedding Model
# -----------------------------

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)

print("Embedding model loaded.")


# -----------------------------
# Global Knowledge Base
# -----------------------------

document_chunks = []
vector_index = None


# -----------------------------
# Extract PDF Text
# -----------------------------

def extract_pdf_text(file_path):

    reader = PdfReader(file_path)

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        text = page.extract_text()

        if text:

            pages.append({
                "page": page_number,
                "text": text
            })

    return pages


# -----------------------------
# Text Chunking
# -----------------------------

def create_chunks(text, chunk_size=800, overlap=100):

    text = " ".join(text.split())

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        if chunk.strip():

            chunks.append(chunk)

        start = end - overlap

        if end >= len(text):
            break

    return chunks


# -----------------------------
# Create Vector Index
# -----------------------------

def index_document(file_path):

    global document_chunks
    global vector_index

    pages = extract_pdf_text(file_path)

    new_chunks = []

    for page in pages:

        page_chunks = create_chunks(
            page["text"]
        )

        for chunk in page_chunks:

            new_chunks.append({
                "text": chunk,
                "file": os.path.basename(file_path),
                "page": page["page"]
            })


    if not new_chunks:

        return 0


    # Generate embeddings

    texts = [
        item["text"]
        for item in new_chunks
    ]

    embeddings = embedding_model.encode(
        texts,
        normalize_embeddings=True
    )

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )


    # Create FAISS index

    if vector_index is None:

        dimension = embeddings.shape[1]

        vector_index = faiss.IndexFlatIP(
            dimension
        )


    vector_index.add(
        embeddings
    )

    document_chunks.extend(
        new_chunks
    )

    return len(new_chunks)


# -----------------------------
# Retrieve Relevant Documents
# -----------------------------

def retrieve_documents(
    question,
    top_k=4
):

    if vector_index is None:

        return []


    query_embedding = embedding_model.encode(
        [question],
        normalize_embeddings=True
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype="float32"
    )


    number_of_results = min(
        top_k,
        len(document_chunks)
    )


    scores, indices = vector_index.search(
        query_embedding,
        number_of_results
    )


    results = []


    for score, index in zip(
        scores[0],
        indices[0]
    ):

        if index >= 0:

            result = document_chunks[index].copy()

            result["score"] = float(score)

            results.append(result)


    return results


# -----------------------------
# Generate Answer with Ollama
# -----------------------------

def generate_answer(
    question,
    retrieved_documents
):

    context_parts = []


    for document in retrieved_documents:

        context_parts.append(
            f"""
Source: {document['file']}
Page: {document['page']}

{document['text']}
"""
        )


    context = "\n\n".join(
        context_parts
    )


    prompt = f"""
You are SmartDoc AI, an offline document assistant.

Answer the user's question using only the information
provided in the context.

Do not invent information.

If the answer cannot be found in the context,
respond with:

"I could not find that information in the uploaded document."

Give a clear and concise answer.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""


    payload = {

        "model": OLLAMA_MODEL,

        "prompt": prompt,

        "stream": False,

        "options": {
            "temperature": 0.2
        }
    }


    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120
    )


    response.raise_for_status()


    result = response.json()


    return result.get(
        "response",
        "No response generated."
    ).strip()


# -----------------------------
# Home Page
# -----------------------------

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# -----------------------------
# Upload PDF
# -----------------------------

@app.route(
    "/upload",
    methods=["POST"]
)
def upload_document():

    if "file" not in request.files:

        return jsonify({
            "error": "No file selected."
        }), 400


    file = request.files["file"]


    if file.filename == "":

        return jsonify({
            "error": "No file selected."
        }), 400


    if not file.filename.lower().endswith(".pdf"):

        return jsonify({
            "error": "Only PDF files are supported."
        }), 400


    filename = secure_filename(
        file.filename
    )


    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )


    file.save(file_path)


    try:

        chunks_added = index_document(
            file_path
        )


        return jsonify({

            "message":
                f"{filename} uploaded successfully.",

            "chunks":
                chunks_added

        })


    except Exception as error:

        return jsonify({

            "error": str(error)

        }), 500


# -----------------------------
# Ask Question
# -----------------------------

@app.route(
    "/ask",
    methods=["POST"]
)
def ask_question():

    data = request.get_json()


    if not data:

        return jsonify({
            "error": "Invalid request."
        }), 400


    question = data.get(
        "question",
        ""
    ).strip()


    if not question:

        return jsonify({
            "error": "Please enter a question."
        }), 400


    if not document_chunks:

        return jsonify({

            "error":
                "Please upload a PDF first."

        }), 400


    try:

        retrieved_documents = retrieve_documents(
            question
        )


        answer = generate_answer(
            question,
            retrieved_documents
        )


        sources = []


        for document in retrieved_documents:

            sources.append({

                "file":
                    document["file"],

                "page":
                    document["page"],

                "score":
                    round(
                        document["score"],
                        3
                    )
            })


        return jsonify({

            "answer": answer,

            "sources": sources

        })


    except requests.exceptions.ConnectionError:

        return jsonify({

            "error":
                "Ollama is not running. Start Ollama and try again."

        }), 500


    except Exception as error:

        return jsonify({

            "error": str(error)

        }), 500


# -----------------------------
# Run Application
# -----------------------------

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )