
import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from search import fts5_search, faiss_search, hybrid_search
import time
from typing import List, Dict, Tuple, Any
from collections import defaultdict

class SearchEvaluator:
    def __init__(self, model_path: str = 'all-MiniLM-L6-v2', 
                 faiss_index_path: str = "embeddings.index",
                 papers_path: str = "papers.json",
                 chunks_path: str = "chunks.json"):
        self.chunks_path = chunks_path
        """Initialize the search evaluator with model and data"""
        print("Loading model and data...")
        
        # Load the sentence transformer model
        self.model = SentenceTransformer(model_path, device='cpu')  # Use CPU for evaluation
        
        # Load FAISS index
        self.faiss_index = faiss.read_index(faiss_index_path)
        
        # Load metadata
        with open(papers_path, "r") as f:
            self.papers_metadata = json.load(f)
        
        with open(chunks_path, "r") as f:
            self.chunks_metadata = json.load(f)
        
        print("✓ Model and data loaded successfully")
    
    def get_ground_truth(self, query: str, k: int = 3) -> List[str]:
        """
        Get ground truth chunk idsfor a query by searching through chunks.json
        """
        with open(self.chunks_path, "r") as f:
            chunks = json.load(f)
        
        # search through chunks.json for query
        ground_truth = []
        for chunk_id, chunk in self.chunks_metadata.items():
            if query in chunk["chunk_text"]:
                ground_truth.append(chunk_id)
       

        return ground_truth
    
    def evaluate_vector_search(self, query: str, k: int = 3) -> Tuple[List[str], List[float], float]:
        """Evaluate vector-only search using FAISS"""
        try:
            start_time = time.time()
            chunk_ids, distances = faiss_search(self.model, self.faiss_index, 
                                              self.papers_metadata, self.chunks_metadata, query, k)
            search_time = time.time() - start_time
            
            # Convert distances to similarity scores
            scores = [1.0 / (1.0 + dist) for dist in distances]
            
            return chunk_ids, scores, search_time
        except Exception as e:
            print(f"Warning: Vector search failed for query '{query}': {e}")
            return [], [], 0.0
    
    def evaluate_keyword_search(self, query: str, k: int = 3) -> Tuple[List[str], List[float], float]:
        """Evaluate keyword-only search using FTS5"""
        try:
            start_time = time.time()
            key_scores = fts5_search(query, k)
            search_time = time.time() - start_time
            
            # Sort by score and get top k
            sorted_results = sorted(key_scores.items(), key=lambda x: x[1], reverse=True)
            chunk_ids = [chunk_id for chunk_id, _ in sorted_results[:k]]
            scores = [score for _, score in sorted_results[:k]]
            
            return chunk_ids, scores, search_time
        except Exception as e:
            print(f"Warning: Keyword search failed for query '{query}': {e}")
            return [], [], 0.0
    
    def evaluate_hybrid_search(self, query: str, k: int = 3) -> Tuple[List[str], List[float], float]:
        """Evaluate hybrid search combining vector and keyword approaches"""
        try:
            start_time = time.time()
            results = hybrid_search(self.model, self.faiss_index, 
                                  self.papers_metadata, self.chunks_metadata, query, k)
            search_time = time.time() - start_time
            
            chunk_ids = [result["chunk_id"] for result in results]
            scores = [result["hybrid_score"] for result in results]
            
            return chunk_ids, scores, search_time
        except Exception as e:
            print(f"Warning: Hybrid search failed for query '{query}': {e}")
            return [], [], 0.0
    
    def calculate_metrics(self, retrieved_ids: List[str], ground_truth: List[str], k: int) -> Dict[str, float]:
        """Calculate evaluation metrics"""
        if not ground_truth:
            return {"recall": 0.0, "precision": 0.0, "hit_rate": 0.0}
        
        # Calculate intersection
        intersection = set(retrieved_ids[:k]) & set(ground_truth)
        
        # Recall@k: fraction of relevant documents that were retrieved
        recall = len(intersection) / len(ground_truth) if ground_truth else 0.0
        
        # Precision@k: fraction of retrieved documents that are relevant
        precision = len(intersection) / min(k, len(retrieved_ids)) if retrieved_ids else 0.0
        
        # Hit rate@k: whether at least one relevant document was retrieved
        hit_rate = 1.0 if intersection else 0.0
        
        return {
            "recall": recall,
            "precision": precision,
            "hit_rate": hit_rate
        }
    
    def run_evaluation(self, queries: List[str], k: int = 3) -> Dict[str, Any]:
        """Run comprehensive evaluation on all search methods"""
        print(f"\n🔍 Running evaluation on {len(queries)} queries with k={k}")
        print("=" * 80)
        
        results = {
            "vector_search": {"metrics": [], "times": [], "queries": []},
            "keyword_search": {"metrics": [], "times": [], "queries": []},
            "hybrid_search": {"metrics": [], "times": [], "queries": []}
        }
        
        for i, query in enumerate(queries, 1):
            print(f"\nQuery {i}/{len(queries)}: '{query}'")
            print("-" * 50)
            
            # Get ground truth for this query
            ground_truth = self.get_ground_truth(query, k)
            
            # Evaluate vector search
            vec_ids, vec_scores, vec_time = self.evaluate_vector_search(query, k)
            vec_metrics = self.calculate_metrics(vec_ids, ground_truth, k)
            results["vector_search"]["metrics"].append(vec_metrics)
            results["vector_search"]["times"].append(vec_time)
            results["vector_search"]["queries"].append({
                "query": query,
                "retrieved_ids": vec_ids,
                "scores": vec_scores
            })
            
            # Evaluate keyword search
            key_ids, key_scores, key_time = self.evaluate_keyword_search(query, k)
            key_metrics = self.calculate_metrics(key_ids, ground_truth, k)
            results["keyword_search"]["metrics"].append(key_metrics)
            results["keyword_search"]["times"].append(key_time)
            results["keyword_search"]["queries"].append({
                "query": query,
                "retrieved_ids": key_ids,
                "scores": key_scores
            })
            
            # Evaluate hybrid search
            hybrid_ids, hybrid_scores, hybrid_time = self.evaluate_hybrid_search(query, k)
            hybrid_metrics = self.calculate_metrics(hybrid_ids, ground_truth, k)
            results["hybrid_search"]["metrics"].append(hybrid_metrics)
            results["hybrid_search"]["times"].append(hybrid_time)
            results["hybrid_search"]["queries"].append({
                "query": query,
                "retrieved_ids": hybrid_ids,
                "scores": hybrid_scores
            })
            
            # Print results for this query
            print(f"Vector Search:   Recall@{k}: {vec_metrics['recall']:.3f}, "
                  f"Precision@{k}: {vec_metrics['precision']:.3f}, "
                  f"Hit Rate@{k}: {vec_metrics['hit_rate']:.3f}, "
                  f"Time: {vec_time:.3f}s")
            print(f"Keyword Search:  Recall@{k}: {key_metrics['recall']:.3f}, "
                  f"Precision@{k}: {key_metrics['precision']:.3f}, "
                  f"Hit Rate@{k}: {key_metrics['hit_rate']:.3f}, "
                  f"Time: {key_time:.3f}s")
            print(f"Hybrid Search:   Recall@{k}: {hybrid_metrics['recall']:.3f}, "
                  f"Precision@{k}: {hybrid_metrics['precision']:.3f}, "
                  f"Hit Rate@{k}: {hybrid_metrics['hit_rate']:.3f}, "
                  f"Time: {hybrid_time:.3f}s")
        
        return results
    
    def calculate_average_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate average metrics across all queries"""
        summary = {}
        
        for method in ["vector_search", "keyword_search", "hybrid_search"]:
            metrics = results[method]["metrics"]
            times = results[method]["times"]
            
            if metrics:
                avg_recall = np.mean([m["recall"] for m in metrics])
                avg_precision = np.mean([m["precision"] for m in metrics])
                avg_hit_rate = np.mean([m["hit_rate"] for m in metrics])
                avg_time = np.mean(times)
                
                summary[method] = {
                    "avg_recall": avg_recall,
                    "avg_precision": avg_precision,
                    "avg_hit_rate": avg_hit_rate,
                    "avg_time": avg_time,
                    "total_queries": len(metrics)
                }
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print a formatted summary of the evaluation results"""
        print("\n" + "=" * 80)
        print("📊 EVALUATION SUMMARY")
        print("=" * 80)
        
        for method, metrics in summary.items():
            method_name = method.replace("_", " ").title()
            print(f"\n{method_name}:")
            print(f"  Average Recall@{3}:     {metrics['avg_recall']:.3f}")
            print(f"  Average Precision@{3}:  {metrics['avg_precision']:.3f}")
            print(f"  Average Hit Rate@{3}:   {metrics['avg_hit_rate']:.3f}")
            print(f"  Average Search Time:    {metrics['avg_time']:.3f}s")
            print(f"  Total Queries:          {metrics['total_queries']}")
        
        # Find best performing method for each metric
        print(f"\n🏆 BEST PERFORMING METHODS:")
        best_recall = max(summary.items(), key=lambda x: x[1]['avg_recall'])
        best_precision = max(summary.items(), key=lambda x: x[1]['avg_precision'])
        best_hit_rate = max(summary.items(), key=lambda x: x[1]['avg_hit_rate'])
        fastest = min(summary.items(), key=lambda x: x[1]['avg_time'])
        
        print(f"  Best Recall@{3}:     {best_recall[0].replace('_', ' ').title()} ({best_recall[1]['avg_recall']:.3f})")
        print(f"  Best Precision@{3}:  {best_precision[0].replace('_', ' ').title()} ({best_precision[1]['avg_precision']:.3f})")
        print(f"  Best Hit Rate@{3}:   {best_hit_rate[0].replace('_', ' ').title()} ({best_hit_rate[1]['avg_hit_rate']:.3f})")
        print(f"  Fastest:             {fastest[0].replace('_', ' ').title()} ({fastest[1]['avg_time']:.3f}s)")


def main():
    """Main evaluation function"""
    # Define evaluation queries covering different topics and complexity levels
    evaluation_queries = [
        "machine learning",
        "neural network",
        "LLM",
        "chain of thought",
        "multimodal model",
        "transformer",
        "attention mechanism",
        "robotics",
        "DeepSeek",
        "GPT"
    ]
    
    print("🚀 Starting Search Evaluation")
    print("=" * 80)
    
    try:
        # Initialize evaluator
        evaluator = SearchEvaluator()
        
        # Run evaluation
        results = evaluator.run_evaluation(evaluation_queries, k=3)
        
        # Calculate summary statistics
        summary = evaluator.calculate_average_metrics(results)
        
        # Print summary
        evaluator.print_summary(summary)
        
        # Save detailed results to file
        output_file = "search_evaluation_results.json"
        with open(output_file, 'w') as f:
            json.dump({
                "summary": summary,
                "detailed_results": results,
                "queries": evaluation_queries,
                "evaluation_params": {"k": 3, "total_queries": len(evaluation_queries)}
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        print("\n✅ Evaluation completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

