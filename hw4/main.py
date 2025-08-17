"""
FastAPI Service Module

Basic FastAPI service for document search.
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import os
from glob import glob
import json
import gc

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


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "RAG Search Service"}


@app.get("/search")
async def search(q: str):
    """
    Receive a query 'q', embed it, retrieve top-3 passages, and return them.
    """
    global model, faiss_index, papers_metadata, chunks_metadata
    
    if model is None:
        return {"error": "Model not initialized"}
    
    if faiss_index is None:
        return {"error": "FAISS index not available"}
    
    # Embed the query
    query_vector = model.encode([q])
    query_vector = query_vector.reshape(1, -1)
    # normalize query vector
    query_vector = query_vector / np.linalg.norm(query_vector, axis=1, keepdims=True)
    print(query_vector.shape)
    # Perform FAISS search
    k = 3
    distances, indices = faiss_index.search(query_vector, k)
    
    # Retrieve the corresponding chunks
    results = []
    for idx in indices[0]:
        results.append(chunks_metadata[str(idx)]["chunk_text"])
    
    return {"query": q, "results": results}

