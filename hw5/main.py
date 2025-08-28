from fastapi import FastAPI
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer
import faiss
import json
import gc
from search import hybrid_search

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global model, faiss_index, papers_metadata, chunks_metadata
    model = SentenceTransformer('all-MiniLM-L6-v2', device='cuda')
    faiss_index = faiss.read_index("embeddings.index")
    
    # load metadata
    with open("papers.json", "r") as f:
        papers_metadata = json.load(f)
    
    with open("chunks.json", "r") as f:
        chunks_metadata = json.load(f)

    yield
    # Shutdown (if needed)
    del model, faiss_index, papers_metadata, chunks_metadata
    gc.collect()


app = FastAPI(lifespan=lifespan)


@app.get("/hybrid_search")
async def hybrid_search(query: str, k: int = 3):
    # 1. Compute query embedding for FAISS
    # 2. Get top-k from FAISS and top-k from SQLite FTS/BM25
    # 3. Merge scores (as above) and select final top-k documents
    results = hybrid_search(model, faiss_index, papers_metadata, chunks_metadata, query, k)

    return {"results": results}

