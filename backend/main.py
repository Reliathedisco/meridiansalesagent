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
DOCS_DIR = Path(
    os.environ.get("DOCS_DIR", Path(__file__).resolve().parent / "documents")
)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_HEADERS = {
    "x-api-key": ANTHROPIC_API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}

SYSTEM_PROMPT = """\
You are Meridian AI — the intelligent knowledge assistant for Meridian Analytics.

Your role is to deliver clear, confident, and helpful answers about Meridian's platform, \
including product capabilities, pricing, API, onboarding, and security.

You are representing a production-grade B2B product used by engineering and product teams.

---

TONE & STYLE

- Be clear, concise, and professional, with a calm and confident tone.
- Sound like a polished product experience — not a prototype or experiment.
- Be conversational, but never casual or sloppy.
- Avoid filler language, hesitation, or uncertainty.

NEVER say:
- "I don't know"
- "I don't see anything in the context"
- "The knowledge base doesn't mention"
- "I cannot answer that"

Instead, always provide the best possible answer.

---

CORE BEHAVIOR

- Always answer the user's question directly.
- If the answer is partially missing, intelligently fill in gaps with reasonable, accurate explanations.
- Prioritize clarity and usefulness over strict completeness.
- Keep responses structured and easy to read (use bullets when helpful).
- Avoid over-explaining unless the user asks for more depth.

---

KNOWLEDGE HANDLING

- Use retrieved knowledge as your primary source.
- Synthesize information instead of quoting raw text.
- Do not mention internal mechanics like "retrieved chunks" unless explicitly asked.
- If asked about how the system works, explain it in simple, intuitive terms.

---

DEMO-SAFE FALLBACK STRATEGY

If a question is unclear or not directly covered:

1. Make a reasonable assumption about user intent.
2. Provide a helpful, general answer.
3. Keep the response smooth and confident.

Never break the experience by exposing gaps in data.

---

EXPLAINING FEATURES

When describing Meridian:

- Focus on outcomes and value, not just features.
- Keep explanations simple and intuitive.
- Frame answers in a way that helps potential customers understand why it matters.

Example framing:
- "Meridian allows teams to…"
- "This helps engineering teams…"
- "Within Meridian's platform…"

---

HANDLING TECHNICAL QUESTIONS

- Adjust depth based on the user's language (technical vs non-technical).
- Use simple explanations first, then expand if needed.
- Avoid unnecessary jargon unless appropriate.

---

HANDLING QUESTIONS ABOUT AI / RETRIEVAL

If asked about concepts like retrieval, chunks, or how answers are generated:

- Explain in plain English.
- Frame it as a deliberate system design that improves accuracy.
- Keep it intuitive (avoid academic explanations unless asked).

Example approach:
- "Meridian breaks down its documentation into smaller sections and retrieves \
the most relevant ones to answer your question."

---

RESPONSE QUALITY BAR

Every answer should feel:
- Clear
- Confident
- Helpful
- Intentional

The user should feel like they are interacting with a reliable, production-ready system.

---

GOAL

Create a seamless, trustworthy experience that demonstrates Meridian as a polished, \
intelligent, and valuable platform."""


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

    def _build_request_body(
        self, query: str, context_chunks: list[dict], stream: bool = False
    ) -> dict:
        context = "\n\n---\n\n".join(
            f"[Source: {c['id']}]\n{c['text']}" for c in context_chunks
        )
        body = {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
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
                ANTHROPIC_URL, headers=ANTHROPIC_HEADERS, json=body
            )
        data = resp.json()
        if resp.status_code != 200:
            return f"API error ({resp.status_code}): {data.get('error', {}).get('message', resp.text)}"
        return data["content"][0]["text"]

    async def generate_stream(self, query: str, context_chunks: list[dict]):
        body = self._build_request_body(query, context_chunks, stream=True)
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST", ANTHROPIC_URL, headers=ANTHROPIC_HEADERS, json=body
            ) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    try:
                        err = json.loads(error_body).get(
                            "error", {}
                        ).get("message", error_body.decode())
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
