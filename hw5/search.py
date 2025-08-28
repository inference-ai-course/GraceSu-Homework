import sqlite3
import numpy as np

def hybrid_score(vec_score, key_score, alpha=0.6):
    # vec_score: normalized similarity from FAISS (0-1, higher is better)
    # key_score: normalized score from FTS5 (0-1, higher is better)
    return alpha * vec_score + (1 - alpha) * key_score


def fts5_search(query: str, k: int = 3):
    if query == "":
        return {}
    
    conn = sqlite3.connect("arxiv_documents.db")
    cursor = conn.cursor()
    
    # Use FTS5 MATCH with proper ranking
    cursor.execute("""
        SELECT 
            doc_chunks_fts.rowid as chunk_id,
            doc_chunks_fts.chunk_text,
            doc_chunks_fts.rank
        FROM doc_chunks_fts
        WHERE doc_chunks_fts MATCH ?
        ORDER BY doc_chunks_fts.rank
        LIMIT ?;
    """, (query, k))
    
    results = cursor.fetchall()
    conn.close()
    
    # Convert to dictionary mapping chunk_id to normalized score
    if not results:
        return {}
    
    # FTS5 rank is negative, so we convert to positive and normalize
    # Get the best rank (smallest negative number) for normalization
    best_rank = min(rank for _, _, rank in results)
    
    key_scores = {}
    for chunk_id, text, rank in results:
        # Normalize rank to 0-1 range (0 = worst, 1 = best)
        # Convert negative rank to positive and normalize
        normalized_score = (-rank) / (-best_rank) if best_rank != 0 else 0.0
        key_scores[str(chunk_id)] = normalized_score
    
    return key_scores


def faiss_search(model, faiss_index, papers_metadata, chunks_metadata, query: str, k: int = 3):
    """
    Receive a query 'q', embed it, retrieve top-k passages, and return chunk IDs and distances.
    """
    if model is None:
        return [], []
    
    if faiss_index is None:
        return [], []
    
    # Embed the query
    query_vector = model.encode([query])
    query_vector = query_vector.reshape(1, -1)
    # normalize query vector
    query_vector = query_vector / np.linalg.norm(query_vector, axis=1, keepdims=True)
    # Perform FAISS search
    distances, indices = faiss_index.search(query_vector, k)
    
    # Return chunk IDs and distances
    chunk_ids = []
    for idx in indices[0]:
        chunk_ids.append(str(idx))
    
    return chunk_ids, distances[0]


def hybrid_search(model, faiss_index, papers_metadata, chunks_metadata, query: str, k: int = 3):
    # 1. Compute query embedding for FAISS
    # 2. Get top-k from FAISS and top-k from SQLite FTS/BM25
    # 3. Merge scores (as above) and select final top-k documents
    vec_results, vec_distances = faiss_search(model, faiss_index, papers_metadata, chunks_metadata, query, k)
    key_results = fts5_search(query, k)

    # Create a dictionary to store combined scores for each document
    combined_scores = {}
    
    # Process FAISS results (vector similarity)
    for chunk_id, distance in zip(vec_results, vec_distances):
        # Convert distance to similarity score (1 - normalized distance)
        # FAISS returns L2 distances, so smaller is better
        vec_score = 1.0 / (1.0 + distance)
        combined_scores[chunk_id] = {"vec_score": vec_score, "key_score": 0.0}
    
    # Process FTS5 results (keyword matching)
    for chunk_id, key_score in key_results.items():
        if chunk_id in combined_scores:
            combined_scores[chunk_id]["key_score"] = key_score
        else:
            combined_scores[chunk_id] = {"vec_score": 0.0, "key_score": key_score}
    
    # Calculate hybrid scores and sort
    top_k_results = []
    for chunk_id, scores in combined_scores.items():
        hybrid_score_val = hybrid_score(scores["vec_score"], scores["key_score"], alpha=0.5)
        top_k_results.append((chunk_id, hybrid_score_val))
    
    # Sort by hybrid score (descending) and take top k
    top_k_results.sort(key=lambda x: x[1], reverse=True)
    top_k_results = top_k_results[:k]

    # return dict of results
    results = [{"chunk_id": chunk[0], "hybrid_score": chunk[1]} for chunk in top_k_results]

    return results
