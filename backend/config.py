"""
Application configuration from env file
"""
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY","")
MAX_PAGES: int = int(os.getenv("MAX_PAGES", "50"))
CRAWL_DELAY: float = float(os.getenv("CRAWL_DELAY", "1.0"))

CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))

EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-2")
LLM_MODEL: str = os.getenv("LLM_MODEL", "models/gemini-2.5-flash")
MAX_PAGES: int = int(os.getenv("MAX_PAGES", "10")) 

FAISS_INDEX_DIR: Path = Path(os.getenv("FAISS_INDEX_DIR",
                                       str(Path(__file__).resolve().parent / "data" / "faiss_indices"),
                                       ))