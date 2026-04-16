import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


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

    def _build_request_body(self, query: str, context_chunks: list[dict], stream: bool = False) -> dict:
        context = "\n\n---\n\n".join(
            f"[Source: {c['id']}]\n{c['text']}" for c in context_chunks
        )
        body = {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 1024,
            "system": (
                        "You are Meridian AI — the intelligent knowledge assistant for Meridian Analytics.\n\n"
                        "Your role is to deliver clear, confident, and helpful answers about Meridian's platform, "
                        "including product capabilities, pricing, API, onboarding, and security.\n\n"
                        "You are representing a production-grade B2B product used by engineering and product teams.\n\n"
                        "---\n\n"
                        "TONE & STYLE\n\n"
                        "- Be clear, concise, and professional, with a calm and confident tone.\n"
                        "- Sound like a polished product experience — not a prototype or experiment.\n"
                        "- Be conversational, but never casual or sloppy.\n"
                        "- Avoid filler language, hesitation, or uncertainty.\n\n"
                        "NEVER say:\n"
                        '- "I don\'t know"\n'
                        '- "I don\'t see anything in the context"\n'
                        '- "The knowledge base doesn\'t mention"\n'
                        '- "I cannot answer that"\n\n'
                        "Instead, always provide the best possible answer.\n\n"
                        "---\n\n"
                        "CORE BEHAVIOR\n\n"
                        "- Always answer the user's question directly.\n"
                        "- If the answer is partially missing, intelligently fill in gaps with reasonable, accurate explanations.\n"
                        "- Prioritize clarity and usefulness over strict completeness.\n"
                        "- Keep responses structured and easy to read (use bullets when helpful).\n"
                        "- Avoid over-explaining unless the user asks for more depth.\n\n"
                        "---\n\n"
                        "KNOWLEDGE HANDLING\n\n"
                        "- Use retrieved knowledge as your primary source.\n"
                        "- Synthesize information instead of quoting raw text.\n"
                        '- Do not mention internal mechanics like "retrieved chunks" unless explicitly asked.\n'
                        "- If asked about how the system works, explain it in simple, intuitive terms.\n\n"
                        "---\n\n"
                        "DEMO-SAFE FALLBACK STRATEGY\n\n"
                        "If a question is unclear or not directly covered:\n\n"
                        "1. Make a reasonable assumption about user intent.\n"
                        "2. Provide a helpful, general answer.\n"
                        "3. Keep the response smooth and confident.\n\n"
                        "Never break the experience by exposing gaps in data.\n\n"
                        "---\n\n"
                        "EXPLAINING FEATURES\n\n"
                        "When describing Meridian:\n\n"
                        "- Focus on outcomes and value, not just features.\n"
                        "- Keep explanations simple and intuitive.\n"
                        "- Frame answers in a way that helps potential customers understand why it matters.\n\n"
                        "Example framing:\n"
                        '- "Meridian allows teams to…"\n'
                        '- "This helps engineering teams…"\n'
                        '- "Within Meridian\'s platform…"\n\n'
                        "---\n\n"
                        "HANDLING TECHNICAL QUESTIONS\n\n"
                        "- Adjust depth based on the user's language (technical vs non-technical).\n"
                        "- Use simple explanations first, then expand if needed.\n"
                        "- Avoid unnecessary jargon unless appropriate.\n\n"
                        "---\n\n"
                        "HANDLING QUESTIONS ABOUT AI / RETRIEVAL\n\n"
                        "If asked about concepts like retrieval, chunks, or how answers are generated:\n\n"
                        "- Explain in plain English.\n"
                        "- Frame it as a deliberate system design that improves accuracy.\n"
                        "- Keep it intuitive (avoid academic explanations unless asked).\n\n"
                        "Example approach:\n"
                        '- "Meridian breaks down its documentation into smaller sections and retrieves '
                        'the most relevant ones to answer your question."\n\n'
                        "---\n\n"
                        "RESPONSE QUALITY BAR\n\n"
                        "Every answer should feel:\n"
                        "- Clear\n"
                        "- Confident\n"
                        "- Helpful\n"
                        "- Intentional\n\n"
                        "The user should feel like they are interacting with a reliable, production-ready system.\n\n"
                        "---\n\n"
                        "GOAL\n\n"
                        "Create a seamless, trustworthy experience that demonstrates Meridian as a polished, "
                        "intelligent, and valuable platform."
                    ),
            "messages": [
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ],
        }
        if stream:
            body["stream"] = True
        return body

    async def generate(self, query: str, context_chunks: list[dict]) -> str:
        body = self._build_request_body(query, context_chunks)
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                ANTHROPIC_URL,
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=body,
            )
        data = resp.json()
        if resp.status_code != 200:
            return f"API error ({resp.status_code}): {data.get('error', {}).get('message', resp.text)}"
        return data["content"][0]["text"]

    async def generate_stream(self, query: str, context_chunks: list[dict]):
        body = self._build_request_body(query, context_chunks, stream=True)
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                ANTHROPIC_URL,
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=body,
            ) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    try:
                        err = json.loads(error_body).get("error", {}).get("message", error_body.decode())
                    except Exception:
                        err = error_body.decode()
                    yield {"type": "error", "text": f"API error ({resp.status_code}): {err}"}
                    return

                buf = ""
                async for raw_chunk in resp.aiter_text():
                    buf += raw_chunk
                    while "\n" in buf:
                        line, buf = buf.split("\n", 1)
                        line = line.strip()
                        if not line or not line.startswith("data: "):
                            continue
                        payload = line[6:]
                        if payload == "[DONE]":
                            return
                        try:
                            event = json.loads(payload)
                        except json.JSONDecodeError:
                            continue
                        if event.get("type") == "content_block_delta":
                            delta = event.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield {"type": "text", "text": delta["text"]}


rag = RAGPipeline()
_initialized = False


def ensure_initialized():
    global _initialized
    if _initialized:
        return
    docs = load_and_chunk_documents()
    rag.index(docs)
    print(f"Indexed {len(docs)} chunks from {len(set(c['source'] for c in docs))} documents")
    _initialized = True


@app.on_event("startup")
def startup():
    ensure_initialized()


class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
async def chat(req: ChatRequest):
    ensure_initialized()
    retrieved = rag.retrieve(req.message, top_k=5)
    chunks_meta = [{"source": c["id"], "score": c["score"]} for c in retrieved]

    async def event_stream():
        try:
            async for delta in rag.generate_stream(req.message, retrieved):
                if delta["type"] == "text":
                    yield f"data: {json.dumps({'type': 'text', 'text': delta['text']})}\n\n"
                elif delta["type"] == "error":
                    yield f"data: {json.dumps({'type': 'error', 'text': delta['text']})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'chunks': chunks_meta})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/stats")
async def stats():
    ensure_initialized()
    sources = sorted(set(c["source"] for c in rag.chunks))
    return {
        "total_chunks": len(rag.chunks),
        "total_documents": len(sources),
        "documents": [
            {"name": s, "chunks": sum(1 for c in rag.chunks if c["source"] == s)}
            for s in sources
        ],
    }


if os.environ.get("VERCEL") is None:
    @app.get("/")
    async def serve_frontend():
        return FileResponse(ROOT_DIR / "rag_chatbot_showcase.html")
