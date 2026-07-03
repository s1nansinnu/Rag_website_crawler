"""
FastAPI File with cors, routers and startup hooks
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from config import FAISS_INDEX_DIR

app = FastAPI(
    title="Website Crawler RAG Chatbot",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event() -> None:
    """
    Load Environment variable and ensure the FAISS index directory exists"""
    load_dotenv()
    FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Website Crawler RAG Chatbot is running."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)