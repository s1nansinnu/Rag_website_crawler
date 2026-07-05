# RAG-Powered Website Chatbot

A chatbot that ingests any URL, recursively scrapes linked pages, and answers questions using Retrieval-Augmented Generation (RAG) with Google Gemini.

---

## Problem Statement

Build a chatbot that:
- Ingests any given URL and recursively scrapes relevant content from linked pages
- Uses RAG to answer user questions accurately based on collected content
- Ensures minimal latency and robust handling of structured and unstructured data

---

## Solution Approach

1. **Crawling** — Playwright-based BFS crawler with httpx fallback for anti-bot bypass. Handles HTML, PDF, images (OCR), and plain text.
2. **Extraction** — BeautifulSoup for HTML, pdfplumber for PDFs, pytesseract for image OCR.
3. **Chunking** — RecursiveCharacterTextSplitter with sentence-aware separators to avoid mid-word cuts.
4. **Embedding** — Google Gemini `text-embedding-2` with parallel batch processing via `asyncio.gather`.
5. **Vector Store** — FAISS for fast similarity search with deduplication.
6. **Generation** — Gemini 2.5 Flash with streaming SSE tokens back to the frontend.

---

## Project Structure

```
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── api/
│   │   ├── routes_crawl.py
│   │   ├── routes_chat.py
│   │   └── schemas.py
│   ├── crawler/
│   │   ├── spider.py
│   │   └── extractor.py
│   └── rag/
│       ├── pipeline.py
│       └── prompts.py
│
└── frontend/
    ├── index.html
    ├── src/
    │   ├── App.jsx
    │   ├── components/
    │   │   ├── URLInput.jsx
    │   │   ├── CrawlProgress.jsx
    │   │   ├── ChatWindow.jsx
    │   │   ├── ChatInput.jsx
    │   │   ├── MessageBubble.jsx
    │   │   └── Sidebar.jsx
    │   └── hooks/
    │       ├── useCrawl.js
    │       └── useChat.js
    └── vite.config.js
```

---

## Dependencies / Prerequisites

- Python 3.10+
- Node.js 18+
- Google Gemini API key
- Tesseract OCR binary
  - Windows: https://github.com/UB-Mannheim/tesseract/wiki
  - Linux: `sudo apt install tesseract-ocr`

---

## Setup & Usage Instructions

### 1. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
playwright install chromium
```

Create `.env` in `backend/`:
```env
GOOGLE_API_KEY=your_key_here
MAX_PAGES=10
CRAWL_DELAY=1.0
CHUNK_SIZE=1500
CHUNK_OVERLAP=50
EMBEDDING_MODEL=models/text-embedding-004
LLM_MODEL=models/gemini-2.5-flash
FAISS_INDEX_DIR=./data/faiss_indices
```

Run:
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

### 3. Using the App
1. Enter a website URL
2. Set pages
3. Click **Crawl & Index Website**
4. Wait for crawling → chunking → embedding
5. Click **Start Chatting**
6. Ask questions about the website

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI + Python |
| Crawler | Playwright + httpx |
| Extraction | BeautifulSoup, pdfplumber, pytesseract |
| Embeddings | Google Gemini text-embedding-004 |
| Vector Store | FAISS |
| LLM | Google Gemini 2.5 Flash |
| Streaming | Server-Sent Events (SSE) |