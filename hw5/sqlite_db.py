import sqlite3
import json
import os

class DocumentDatabase:
    def __init__(self, db_path: str = "arxiv_documents.db"):
        self.db_path = db_path

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create documents table for metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id INTEGER PRIMARY KEY,
                title TEXT,
                authors TEXT,
                year INTEGER
            )
        """)
        
        # Create doc_chunks table to link chunks to documents and store chunk text
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id INTEGER PRIMARY KEY,
                doc_id INTEGER,
                chunk_text TEXT,
                FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
            )
        """)
        
        # Create FTS5 virtual table for full-text search on chunks
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS doc_chunks_fts USING fts5(
                chunk_text
            )
        """)
        
        # Create triggers to keep FTS5 table in sync with chunks table
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
                INSERT INTO doc_chunks_fts(rowid, chunk_text) VALUES (new.chunk_id, new.chunk_text);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
                INSERT INTO doc_chunks_fts(doc_chunks_fts, rowid, chunk_text) VALUES('delete', old.chunk_id, old.chunk_text);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
                INSERT INTO doc_chunks_fts(doc_chunks_fts, rowid, chunk_text) VALUES('delete', old.chunk_id, old.chunk_text);
                INSERT INTO doc_chunks_fts(rowid, chunk_text) VALUES (new.chunk_id, new.chunk_text);
            END
        """)
        
        conn.commit()
        conn.close()
    
    def load_metadata_from_json(self, metadata_path: str = "papers.json"):
            
        with open(metadata_path, 'r') as f:
            metadata_dict = json.load(f)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for doc_id_str, doc in metadata_dict.items():
            try:
                doc_id = int(doc_id_str)
            except ValueError:
                continue  # Skip if doc_id is not a valid integer
            
            # Extract year from published attribute
            year = None
            if "published" in doc and doc["published"]:
                try:
                    # Parse the published date string to extract year
                    published_date = doc["published"]
                    # Handle different date formats (e.g., "2025-08-05T08:26:45Z", "2025-01-15", etc.)
                    if "T" in published_date:
                        # ISO format with time: "2025-08-05T08:26:45Z"
                        year = int(published_date.split("T")[0][:4])
                    elif "-" in published_date:
                        # Date format: "2025-01-15"
                        year = int(published_date.split("-")[0])
                    elif len(published_date) >= 4:
                        # Try to extract first 4 digits as year
                        year = int(published_date[:4])
                except (ValueError, IndexError):
                    year = None
            
            # Insert document metadata
            cursor.execute("""
                INSERT OR REPLACE INTO documents 
                (doc_id, title, authors, year)
                VALUES (?, ?, ?, ?)
            """, (
                doc_id,  # Use the actual doc_id from the JSON
                doc.get("title", ""),
                json.dumps(doc.get("authors", [])),  # Store authors as JSON array
                year
            ))
        
        conn.commit()
        conn.close()
    
    def load_chunks_from_json(self, chunks_path: str = "chunks.json"):
        """
        Load processed chunks into the database
        """
        if not os.path.exists(chunks_path):
            print(f"Chunks file not found: {chunks_path}")
            return
            
        with open(chunks_path, 'r') as f:
            chunks_data = json.load(f)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing chunks
        cursor.execute("DELETE FROM chunks")
        
        # Insert chunks
        for chunk_id, chunk_info in chunks_data.items():
            try:
                paper_id = int(chunk_info['paper_id'])
                chunk_text = chunk_info['chunk_text']
                
                cursor.execute("""
                    INSERT INTO chunks (chunk_id, doc_id, chunk_text)
                    VALUES (?, ?, ?)
                """, (
                    int(chunk_id),
                    paper_id,
                    chunk_text,
                ))
                
                # FTS5 insertion is handled automatically by triggers

            except (ValueError, KeyError) as e:
                print(f"Error processing chunk {chunk_id}: {e}")
                continue
        
        conn.commit()
        conn.close()
    

    def get_chunk_by_id(self, chunk_id: int):
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT chunks.chunk_text, documents.doc_id, chunks.chunk_id, documents.title, documents.authors, documents.year
            FROM chunks 
            JOIN documents ON chunks.doc_id = documents.doc_id
            WHERE chunks.chunk_id = ?
        """, (chunk_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            chunk_text, doc_id, chunk_id, title, authors, year = result
            metadata = {
                'paper_id': str(doc_id),
                'chunk_id': chunk_id,
                'title': title,
                'authors': json.loads(authors) if authors else [],
                'year': year
            }
            return chunk_text, metadata
        
        return "", {}
    
    def get_document_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chunks")
        chunk_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as chunk_count FROM chunks GROUP BY doc_id")
        counts = cursor.fetchall()
        avg_chunks = sum(c[0] for c in counts) / len(counts) if counts else 0
        
        conn.close()
        
        return {
            'documents': doc_count,
            'chunks': chunk_count,
            'avg_chunks_per_doc': avg_chunks
        }

def setup_database():
    """Setup database with existing data"""
    db = DocumentDatabase()
    
    # Load metadata and chunks
    db.load_metadata_from_json()
    db.load_chunks_from_json()
    
    # Print stats
    stats = db.get_document_stats()
    print(stats)
    
    return db

if __name__ == "__main__":
    setup_database()