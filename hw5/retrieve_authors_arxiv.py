#!/usr/bin/env python3
"""
Alternative script to retrieve authors for papers using the arXiv API.
This script is specifically designed for arXiv preprints and papers.
"""

import json
import requests
import time
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ArxivAuthorRetriever:
    """Class to retrieve author information using arXiv API."""
    
    def __init__(self):
        """Initialize the ArxivAuthorRetriever."""
        self.base_url = "http://export.arxiv.org/api/query"
        self.headers = {
            'User-Agent': 'AuthorRetriever/1.0 (contact: your-email@example.com)'
        }
    
    def search_paper_by_arxiv_id(self, arxiv_id: str) -> Optional[Dict]:
        """
        Search for a paper by arXiv ID using arXiv API.
        
        Args:
            arxiv_id: The arXiv ID (e.g., "2408.02999" or "2408.02999v1")
            
        Returns:
            Paper data if found, None otherwise
        """
        # Clean the arXiv ID (remove version suffix if present)
        clean_id = re.sub(r'v\d+$', '', arxiv_id.strip())
        
        # Search parameters for arXiv ID
        params = {
            'id_list': clean_id,
            'start': 0,
            'max_results': 1
        }
        
        try:
            response = requests.get(self.base_url, params=params, headers=self.headers)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # Extract entries
            entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
            
            if entries:
                # Extract paper data from the first (and should be only) entry
                paper_data = self._extract_paper_data(entries[0])
                logger.info(f"Found paper by arXiv ID: {paper_data.get('title', 'Unknown')}")
                return paper_data
            else:
                logger.warning(f"No results found for arXiv ID: {arxiv_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching for paper by arXiv ID '{arxiv_id}': {e}")
            return None

    def search_paper_by_title(self, title: str) -> Optional[Dict]:
        """
        Search for a paper by title using arXiv API.
        
        Args:
            title: The paper title to search for
            
        Returns:
            Paper data if found, None otherwise
        """
        # Clean the title for better search results
        clean_title = self._clean_title(title)
        
        # Search parameters
        params = {
            'search_query': f'ti:"{clean_title}"',
            'start': 0,
            'max_results': 5,
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }
        
        try:
            response = requests.get(self.base_url, params=params, headers=self.headers)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # Extract entries
            entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
            
            if entries:
                # Find the best match
                best_match = self._find_best_title_match(title, entries)
                if best_match:
                    logger.info(f"Found paper by title: {best_match.get('title', 'Unknown')}")
                    return best_match
                else:
                    logger.warning(f"No good title match found for: {title}")
                    return None
            else:
                logger.warning(f"No results found for: {title}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching for paper '{title}': {e}")
            return None

    def search_paper_smart(self, title: str, arxiv_id: Optional[str] = None) -> Optional[Dict]:
        """
        Smart search that tries arXiv ID first, then falls back to title search.
        
        Args:
            title: The paper title to search for
            arxiv_id: Optional arXiv ID to try first
            
        Returns:
            Paper data if found, None otherwise
        """
        # First, try to search by arXiv ID if available
        if arxiv_id:
            logger.info(f"Trying arXiv ID search first: {arxiv_id}")
            paper_data = self.search_paper_by_arxiv_id(arxiv_id)
            if paper_data:
                return paper_data
            else:
                logger.info(f"arXiv ID search failed, falling back to title search")
        
        # Fall back to title search
        logger.info(f"Searching by title: {title[:100]}...")
        return self.search_paper_by_title(title)
    
    def _clean_title(self, title: str) -> str:
        """
        Clean the title for better search results.
        
        Args:
            title: Raw title string
            
        Returns:
            Cleaned title string
        """
        # Remove special characters and normalize
        clean = re.sub(r'[^\w\s\-]', ' ', title)
        # Remove extra whitespace
        clean = ' '.join(clean.split())
        # Truncate if too long
        if len(clean) > 200:
            clean = clean[:200]
        return clean
    
    def _find_best_title_match(self, original_title: str, entries: List) -> Optional[Dict]:
        """
        Find the best matching paper from search results.
        
        Args:
            original_title: Original paper title
            entries: List of entry elements from arXiv API
            
        Returns:
            Best matching paper or None
        """
        if not entries:
            return None
        
        # Simple similarity scoring based on word overlap
        original_words = set(original_title.lower().split())
        
        best_score = 0
        best_match = None
        
        for entry in entries:
            # Extract title from entry
            title_elem = entry.find('.//{http://www.w3.org/2005/Atom}title')
            if title_elem is not None:
                candidate_title = title_elem.text.strip()
                candidate_words = set(candidate_title.lower().split())
                
                # Calculate Jaccard similarity
                intersection = len(original_words.intersection(candidate_words))
                union = len(original_words.union(candidate_words))
                
                if union > 0:
                    similarity = intersection / union
                    if similarity > best_score:
                        best_score = similarity
                        best_match = self._extract_paper_data(entry)
        
        # Only return if similarity is above threshold
        if best_score > 0.3:  # Adjustable threshold
            return best_match
        
        return None
    
    def _extract_paper_data(self, entry) -> Dict:
        """
        Extract paper data from arXiv API entry.
        
        Args:
            entry: XML entry element
            
        Returns:
            Dictionary containing paper data
        """
        paper_data = {}
        
        # Extract title
        title_elem = entry.find('.//{http://www.w3.org/2005/Atom}title')
        if title_elem is not None:
            paper_data['title'] = title_elem.text.strip()
        
        # Extract authors
        authors = []
        author_elems = entry.findall('.//{http://www.w3.org/2005/Atom}author')
        for author_elem in author_elems:
            name_elem = author_elem.find('.//{http://www.w3.org/2005/Atom}name')
            if name_elem is not None:
                authors.append(name_elem.text.strip())
        
        paper_data['authors'] = authors
        
        # Extract abstract
        summary_elem = entry.find('.//{http://www.w3.org/2005/Atom}summary')
        if summary_elem is not None:
            paper_data['abstract'] = summary_elem.text.strip()
        
        # Extract arXiv ID
        id_elem = entry.find('.//{http://www.w3.org/2005/Atom}id')
        if id_elem is not None:
            paper_data['arxiv_id'] = id_elem.text.strip()
        
        # Extract published date
        published_elem = entry.find('.//{http://www.w3.org/2005/Atom}published')
        if published_elem is not None:
            paper_data['published'] = published_elem.text.strip()
        
        return paper_data
    
    def extract_authors(self, paper_data: Dict) -> List[str]:
        """
        Extract author names from paper data.
        
        Args:
            paper_data: Paper data from API response
            
        Returns:
            List of author names
        """
        return paper_data.get('authors', [])
    
    def extract_arxiv_id_from_paper(self, paper_data: Dict) -> Optional[str]:
        """
        Extract arXiv ID from paper data if available.
        
        Args:
            paper_data: Paper data from the papers.json file
            
        Returns:
            arXiv ID if found, None otherwise
        """
        # Check if there's a direct arxiv_id field
        if 'arxiv_id' in paper_data:
            return paper_data['arxiv_id']
        
        # Check if there's an arxiv_id in the text content
        text = paper_data.get('text', '')
        if text:
            # Look for arXiv ID patterns in the text
            arxiv_patterns = [
                r'arxiv\.org/abs/(\d+\.\d+)',  # arxiv.org/abs/2408.02999
                r'arxiv\.org/pdf/(\d+\.\d+)',  # arxiv.org/pdf/2408.02999
                r'arXiv:(\d+\.\d+)',           # arXiv:2408.02999
                r'(\d{4}\.\d{4,5})',          # 2408.02999
            ]
            
            for pattern in arxiv_patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1)
        
        # Check if there's a pdf_link that contains arXiv ID
        pdf_link = paper_data.get('pdf_link', '')
        if pdf_link:
            # Extract arXiv ID from PDF link
            arxiv_match = re.search(r'arxiv\.org/.*?/(\d+\.\d+)', pdf_link)
            if arxiv_match:
                return arxiv_match.group(1)
        
        return None

def load_papers(file_path: str) -> Dict:
    """
    Load papers from JSON file.
    
    Args:
        file_path: Path to papers.json file
        
    Returns:
        Dictionary containing papers data
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading papers file: {e}")
        return {}

def save_papers_with_authors(papers: Dict, output_path: str):
    """
    Save papers with updated author information.
    
    Args:
        papers: Papers data with updated authors
        output_path: Output file path
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(papers, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved updated papers to {output_path}")
    except Exception as e:
        logger.error(f"Error saving papers: {e}")

def main():
    """Main function to retrieve authors for all papers."""
    
    # Configuration
    input_file = "papers.json"
    output_file = "papers_with_authors_arxiv.json"
    
    # Initialize retriever
    retriever = ArxivAuthorRetriever()
    
    # Load papers
    logger.info(f"Loading papers from {input_file}")
    papers = load_papers(input_file)
    
    if not papers:
        logger.error("No papers loaded. Exiting.")
        return
    
    logger.info(f"Loaded {len(papers)} papers")
    
    # Process each paper
    updated_count = 0
    arxiv_id_success_count = 0
    title_search_success_count = 0
    total_papers = len(papers)
    
    for paper_id, paper_data in papers.items():
        title = paper_data.get('title', '')
        
        if not title:
            logger.warning(f"Paper {paper_id} has no title, skipping")
            continue
        
        # Check if authors are already populated
        current_authors = paper_data.get('authors', [])
        if current_authors and len(current_authors) > 0:
            logger.info(f"Paper {paper_id} already has authors, skipping")
            continue
        
        logger.info(f"Processing paper {paper_id}: {title[:100]}...")
        
        # Try to extract arXiv ID from the paper data
        arxiv_id = retriever.extract_arxiv_id_from_paper(paper_data)
        if arxiv_id:
            logger.info(f"Found arXiv ID: {arxiv_id}")
        
        # Use smart search: try arXiv ID first, then fall back to title search
        paper_info = retriever.search_paper_smart(title, arxiv_id)
        
        if paper_info:
            # Extract authors
            authors = retriever.extract_authors(paper_info)
            
            if authors:
                # Update paper data
                papers[paper_id]['authors'] = authors
                updated_count += 1
                logger.info(f"Found {len(authors)} authors for paper {paper_id}")
                
                # Log which method was successful
                if arxiv_id and paper_info.get('arxiv_id'):
                    logger.info(f"  Successfully retrieved via arXiv ID: {arxiv_id}")
                    arxiv_id_success_count += 1
                else:
                    logger.info(f"  Retrieved via title search fallback")
                    title_search_success_count += 1
            else:
                logger.warning(f"No authors found for paper {paper_id}")
        else:
            logger.warning(f"Could not find paper {paper_id} in arXiv (tried both arXiv ID and title search)")
        
        # Rate limiting - be respectful to the API
        time.sleep(3)  # 3 second delay between requests (arXiv recommendation)
        
        # Progress update
        if (int(paper_id) + 1) % 10 == 0:
            logger.info(f"Processed {int(paper_id) + 1}/{total_papers} papers")
    
    # Save updated papers
    logger.info(f"Retrieved authors for {updated_count} papers")
    save_papers_with_authors(papers, output_file)
    
    # Summary
    logger.info("=== SUMMARY ===")
    logger.info(f"Total papers processed: {total_papers}")
    logger.info(f"Papers with authors updated: {updated_count}")
    logger.info(f"  - Found via arXiv ID: {arxiv_id_success_count}")
    logger.info(f"  - Found via title search: {title_search_success_count}")
    logger.info(f"Papers still missing authors: {total_papers - updated_count}")

if __name__ == "__main__":
    main()
