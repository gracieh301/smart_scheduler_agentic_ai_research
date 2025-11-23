"""
RAG (Retrieval-Augmented Generation) pipeline for syllabus PDFs.
Uses ChromaDB for vector storage and sentence-transformers for embeddings.
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

# ChromaDB configuration
# UPDATE THIS: Set CHROMA_PERSIST_DIR to customize where vector DB is stored
CHROMA_PERSIST_DIR = os.getenv(
    "CHROMA_PERSIST_DIR",
    str(Path(__file__).parent.parent / "chroma_db")
)
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "study_planner_rag")

# Embedding model configuration
# UPDATE THIS: Set EMBEDDING_MODEL to use a different model
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

_chroma_client = None
_collection = None
_embedding_model = None


def get_embedding_model():
    """
    Get or load the sentence transformer model for embeddings.
    
    Returns:
        SentenceTransformer model instance
    """
    global _embedding_model
    
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        raise ImportError(
            "sentence-transformers package required. Install with: pip install sentence-transformers"
        )
    
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    
    return _embedding_model


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors (each is a list of floats)
    """
    if not texts:
        return []
    
    # Filter out empty texts
    non_empty_texts = [text for text in texts if text and text.strip()]
    if not non_empty_texts:
        return []
    
    model = get_embedding_model()
    # Show progress bar for large batches
    show_progress = len(non_empty_texts) > 10
    embeddings = model.encode(non_empty_texts, show_progress_bar=show_progress, batch_size=32)
    
    # Convert to list of lists (handle both numpy arrays and lists)
    if hasattr(embeddings, 'tolist'):
        return embeddings.tolist()
    elif isinstance(embeddings, list):
        return embeddings
    else:
        # Fallback: convert to list
        return [list(emb) for emb in embeddings]


def get_chroma_client():
    """
    Get or create ChromaDB client.
    
    Returns:
        ChromaDB PersistentClient instance
    """
    global _chroma_client
    
    if not CHROMA_AVAILABLE:
        raise ImportError(
            "chromadb package required. Install with: pip install chromadb"
        )
    
    if _chroma_client is None:
        # Create persistent directory if it doesn't exist
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        
        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
    
    return _chroma_client


def get_collection():
    """
    Get or create the collection for RAG documents.
    
    Returns:
        ChromaDB collection instance
    """
    global _collection
    
    if _collection is None:
        client = get_chroma_client()
        
        try:
            _collection = client.get_collection(name=COLLECTION_NAME)
        except Exception:
            # Collection doesn't exist, create it
            _collection = client.create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "RAG collection for Study Plan Generator"}
            )
    
    return _collection


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Split text into chunks for embedding.
    
    Tries to break at sentence boundaries for better semantic coherence.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum characters per chunk
        chunk_overlap: Overlap between chunks (for context preservation)
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            for punct in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                last_punct = text.rfind(punct, start, end)
                if last_punct != -1:
                    end = last_punct + len(punct)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start forward with overlap
        start = end - chunk_overlap
        if start >= len(text):
            break
    
    return chunks


def load_and_embed_syllabus(
    syllabus_text: str,
    user_id: str,
    course_name: str,
    syllabus_id: Optional[int] = None
) -> List[str]:
    """
    Load syllabus text, chunk it, and store embeddings in vector DB.
    
    This is the main function called when a syllabus is uploaded.
    
    Args:
        syllabus_text: Extracted text from syllabus PDF
        user_id: User identifier
        course_name: Name of the course
        syllabus_id: Optional database syllabus ID
        
    Returns:
        List of document IDs that were stored
    """
    try:
        collection = get_collection()
        print("✓ ChromaDB collection retrieved")
    except Exception as e:
        raise Exception(f"Failed to get ChromaDB collection: {str(e)}")
    
    # Validate input
    if not syllabus_text or not syllabus_text.strip():
        raise Exception("Syllabus text is empty or None")
    
    # Chunk the text
    try:
        print(f"Chunking syllabus text ({len(syllabus_text)} characters)...")
        chunks = chunk_text(syllabus_text, chunk_size=500, chunk_overlap=50)
        # Filter out empty chunks
        chunks = [chunk for chunk in chunks if chunk and chunk.strip()]
        if not chunks:
            raise Exception("No valid chunks created from syllabus text")
        print(f"Created {len(chunks)} chunks")
    except Exception as e:
        raise Exception(f"Failed to chunk text: {str(e)}")
    
    # Generate embeddings (this can take a while for large documents)
    try:
        print(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = generate_embeddings(chunks)
        print(f"Generated {len(embeddings)} embeddings")
        if not embeddings:
            raise Exception("No embeddings generated")
        if len(embeddings) != len(chunks):
            raise Exception(f"Embedding count mismatch: {len(embeddings)} embeddings for {len(chunks)} chunks")
    except Exception as e:
        raise Exception(f"Failed to generate embeddings: {str(e)}")
    
    # Create metadata for each chunk
    # Note: chunks and embeddings are already filtered (no empty chunks)
    try:
        doc_id_base = f"syllabus_{user_id}_{syllabus_id}" if syllabus_id else f"syllabus_{user_id}"
        
        chunk_ids = []
        chunk_metadatas = []
        
        # Create IDs and metadata for all chunks (they're already filtered)
        for chunk_idx, chunk in enumerate(chunks):
            chunk_id = f"{doc_id_base}_chunk_{chunk_idx}"
            chunk_ids.append(chunk_id)
            
            # ChromaDB doesn't like None values, so use empty string instead
            chunk_metadata = {
                "user_id": str(user_id),
                "document_type": "syllabus",
                "course_name": str(course_name) if course_name else "",
                "syllabus_id": str(syllabus_id) if syllabus_id else "",
                "chunk_index": chunk_idx,
                "total_chunks": len(chunks)
            }
            chunk_metadatas.append(chunk_metadata)
        
        print(f"Prepared {len(chunk_ids)} chunk IDs and metadata")
    except Exception as e:
        raise Exception(f"Failed to prepare chunk metadata: {str(e)}")
    
    # Add to collection
    try:
        if not chunk_ids:
            print("Warning: No chunks to add to vector database")
            return []
        
        print(f"Adding {len(chunk_ids)} chunks to vector database...")
        
        # Ensure all data types are correct for ChromaDB
        # ChromaDB expects: ids (list of str), embeddings (list of list of float), 
        # documents (list of str), metadatas (list of dict)
        
        # Validate data types
        assert len(chunk_ids) == len(embeddings) == len(chunks) == len(chunk_metadatas), \
            f"Data length mismatch: ids={len(chunk_ids)}, embeddings={len(embeddings)}, chunks={len(chunks)}, metadatas={len(chunk_metadatas)}"
        
        # Ensure embeddings are lists of floats
        embeddings_clean = []
        for emb in embeddings:
            if isinstance(emb, list):
                embeddings_clean.append([float(x) for x in emb])
            else:
                embeddings_clean.append([float(x) for x in list(emb)])
        
        collection.add(
            ids=chunk_ids,
            embeddings=embeddings_clean,
            documents=chunks,
            metadatas=chunk_metadatas
        )
        print("Successfully added all chunks to vector database")
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        raise Exception(f"Failed to add chunks to ChromaDB collection: {str(e)}\nDetails: {error_details}")
    
    return chunk_ids


def retrieve_relevant_chunks(
    query: str,
    user_id: Optional[str] = None,
    n_results: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant chunks from vector DB using semantic search.
    
    This is the main retrieval function used by agents to get syllabus content.
    
    Args:
        query: Search query/question
        user_id: Optional user ID to filter results
        n_results: Number of results to return
        
    Returns:
        List of dictionaries with 'text', 'metadata', and 'distance' keys
    """
    if not query or not query.strip():
        return []
    
    try:
        collection = get_collection()
    except Exception as e:
        print(f"Error getting ChromaDB collection: {e}")
        return []
    
    try:
        # Generate query embedding
        query_embeddings = generate_embeddings([query])
        if not query_embeddings:
            return []
        query_embedding = query_embeddings[0]
    except Exception as e:
        print(f"Error generating query embedding: {e}")
        return []
    
    # Build where clause for filtering
    where_clause = None
    if user_id:
        where_clause = {"user_id": str(user_id)}  # Ensure user_id is string
    
    # Search
    try:
        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": n_results
        }
        if where_clause:
            query_params["where"] = where_clause
        
        results = collection.query(**query_params)
    except Exception as e:
        print(f"Error querying ChromaDB: {e}")
        return []
    
    # Format results
    formatted_results = []
    try:
        if results.get("ids") and len(results["ids"]) > 0 and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i] if results.get("documents") and results["documents"][0] else "",
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") and results["metadatas"][0] else {},
                    "distance": results["distances"][0][i] if results.get("distances") and results["distances"] and len(results["distances"][0]) > i else None
                })
    except Exception as e:
        print(f"Error formatting results: {e}")
        return []
    
    return formatted_results

