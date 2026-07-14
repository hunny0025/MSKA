"""
Maruti FAQ Chatbot - Backend (FastAPI)
----------------------------------------
Semantic FAQ matching using SentenceTransformers (all-MiniLM-L6-v2) for robust paraphrase handling.
"""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, util

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(title="Maruti FAQ Chatbot API")

# Allow the frontend (served from file:// or any localhost port) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Load Model & FAQ data at startup
# ---------------------------------------------------------------------------
# Load semantic embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

FAQ_PATH = Path(__file__).parent / "faqs.json"
with open(FAQ_PATH, "r", encoding="utf-8") as f:
    FAQS = json.load(f)

# Pre-compute embeddings for all FAQ questions
FAQ_QUESTIONS = [faq["question"] for faq in FAQS]
FAQ_EMBEDDINGS = model.encode(FAQ_QUESTIONS, convert_to_tensor=True)

CONFIDENCE_THRESHOLD = 0.45  # below this -> fallback response
FALLBACK_ANSWER = (
    "Sorry, I couldn't find a confident match for that. "
    "Please rephrase your question or contact Maruti Suzuki customer care at 1800-102-1800."
)


def find_best_match(user_query: str):
    query_embedding = model.encode(user_query, convert_to_tensor=True)
    similarities = util.cos_sim(query_embedding, FAQ_EMBEDDINGS)[0]
    best_idx = similarities.argmax().item()
    best_score = similarities[best_idx].item()
    return FAQS[best_idx], best_score


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    answer: str
    matched_question: str | None = None
    confidence: float


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "Maruti FAQ Chatbot API is running."}


@app.get("/faqs")
def list_faqs():
    """Return all FAQ questions - useful for showing suggested chips on the frontend."""
    return {"faqs": [faq["question"] for faq in FAQS]}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    query = req.query.strip()
    if not query:
        return ChatResponse(answer="Please type a question.", confidence=0.0)

    best_faq, best_score = find_best_match(query)

    if best_faq is None or best_score < CONFIDENCE_THRESHOLD:
        return ChatResponse(answer=FALLBACK_ANSWER, confidence=round(best_score, 2))

    return ChatResponse(
        answer=best_faq["answer"],
        matched_question=best_faq["question"],
        confidence=round(best_score, 2),
    )
