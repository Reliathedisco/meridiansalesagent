import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import anthropic

load_dotenv()

app = FastAPI(title="Meridian RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = Path(os.environ.get("DOCS_DIR", Path(__file__).resolve().parent / "documents"))


def load_and_chunk_documents() -> list[dict]:
    chunks = []
    for filepath in sorted(DOCS_DIR.glob("*.md")):
        content = filepath.read_text()
        filename = filepath.name
        sections = content.split("\n## ")
        for i, section in enumerate(sections):
            text = section.strip() if i == 0 else f"## {section}".strip()
            if len(text) < 20:
                continue
            chunks.append({
                "text": text,
                "source": filename,
                "section": i + 1,
                "id": f"{filename} §{i + 1}",
            })
    return chunks


class RAGPipeline:
    def __init__(self):
        self.chunks: list[dict] = []
        self.vectorizer = TfidfVectorizer(
            stop_words="english", max_features=5000, ngram_range=(1, 2)
        )
        self.tfidf_matrix = None
        self.client = anthropic.Anthropic()

    def index(self, chunks: list[dict]):
        self.chunks = chunks
        texts = [c["text"] for c in chunks]
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = scores.argsort()[::-1][:top_k]
        return [
            {**self.chunks[idx], "score": round(float(scores[idx]), 2)}
            for idx in top_indices
            if scores[idx] > 0.0
        ]

    def generate(self, query: str, context_chunks: list[dict]) -> str:
        context = "\n\n---\n\n".join(
            f"[Source: {c['id']}]\n{c['text']}" for c in context_chunks
        )
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=(
                "You are Meridian Analytics's AI support assistant. "
                "Answer questions using ONLY the provided context from our knowledge base. "
                "Be concise and helpful. Cite sources inline like [source]. "
                "If the context doesn't cover the question, say so honestly."
            ),
            messages=[
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ],
        )
        return response.content[0].text


rag = RAGPipeline()


@app.on_event("startup")
def startup():
    docs = load_and_chunk_documents()
    rag.index(docs)
    print(f"Indexed {len(docs)} chunks from {len(set(c['source'] for c in docs))} documents")


class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
async def chat(req: ChatRequest):
    retrieved = rag.retrieve(req.message, top_k=5)
    answer = rag.generate(req.message, retrieved)
    return {
        "answer": answer,
        "chunks": [{"source": c["id"], "score": c["score"]} for c in retrieved],
    }


@app.get("/api/stats")
async def stats():
    sources = sorted(set(c["source"] for c in rag.chunks))
    return {
        "total_chunks": len(rag.chunks),
        "total_documents": len(sources),
        "documents": [
            {"name": s, "chunks": sum(1 for c in rag.chunks if c["source"] == s)}
            for s in sources
        ],
    }


@app.get("/")
async def serve_frontend():
    return FileResponse(ROOT_DIR / "rag_chatbot_showcase.html")
