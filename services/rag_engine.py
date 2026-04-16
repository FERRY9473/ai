import os
import fitz  # PyMuPDF
import numpy as np
import faiss
import google.generativeai as genai
from config import GEMINI_API_KEY
import asyncio
import logging

# Configure Gemini for Embeddings
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class RAGEngine:
    def __init__(self, index_path="ai/database/faiss_index"):
        self.index_path = index_path
        self.dimension = 768  # Gemini embedding dimension
        self.index = None
        self.chunks = []
        self._load_index()

    def _load_index(self):
        """Load FAISS index from disk if it exists"""
        if os.path.exists(self.index_path + ".index"):
            try:
                self.index = faiss.read_index(self.index_path + ".index")
                # Load chunks from a separate file (mocked for simplicity here, 
                # in real world we'd save this to a json/pickle)
                import pickle
                if os.path.exists(self.index_path + "_chunks.pkl"):
                    with open(self.index_path + "_chunks.pkl", 'rb') as f:
                        self.chunks = pickle.load(f)
                logging.info("FAISS index loaded.")
            except Exception as e:
                logging.error(f"Error loading FAISS index: {e}")

    def _save_index(self):
        """Save FAISS index and chunks to disk"""
        if self.index:
            faiss.write_index(self.index, self.index_path + ".index")
            import pickle
            with open(self.index_path + "_chunks.pkl", 'wb') as f:
                pickle.dump(self.chunks, f)
            logging.info("FAISS index saved.")

    async def process_pdf(self, file_path):
        """Extract text from PDF, chunk it, and index it"""
        if not GEMINI_API_KEY:
            return "API Key Gemini tidak ditemukan."

        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()

            # Split text into chunks (approx 500 chars with overlap)
            chunk_size = 500
            overlap = 100
            new_chunks = []
            for i in range(0, len(text), chunk_size - overlap):
                chunk = text[i:i + chunk_size].strip()
                if chunk:
                    new_chunks.append(chunk)

            if not new_chunks:
                return "PDF tidak mengandung teks yang bisa dibaca."

            # Generate Embeddings for chunks
            # Using asyncio.to_thread for the blocking Gemini call
            embeddings = []
            for i in range(0, len(new_chunks), 100): # Process in batches of 100
                batch = new_chunks[i:i+100]
                response = await asyncio.to_thread(
                    genai.embed_content,
                    model="models/gemini-embedding-001",
                    content=batch,
                    task_type="retrieval_document"
                )
                embeddings.extend(response['embedding'])

            # Add to FAISS index
            embeddings_np = np.array(embeddings).astype('float32')
            if self.index is None:
                self.index = faiss.IndexFlatL2(self.dimension)
            
            self.index.add(embeddings_np)
            self.chunks.extend(new_chunks)
            
            # Save progress
            self._save_index()
            
            return f"Berhasil memproses PDF. {len(new_chunks)} potongan teks diindeks."

        except Exception as e:
            logging.error(f"Error processing PDF: {e}")
            return f"Gagal memproses PDF: {e}"

    def clear_index(self):
        """Clear the FAISS index and chunks"""
        self.index = None
        self.chunks = []
        if os.path.exists(self.index_path + ".index"):
            os.remove(self.index_path + ".index")
        if os.path.exists(self.index_path + "_chunks.pkl"):
            os.remove(self.index_path + "_chunks.pkl")
        logging.info("FAISS index cleared.")
        return "Indeks PDF berhasil dihapus."

    async def search(self, query, top_k=3):
        """Search for relevant chunks based on query"""
        if not GEMINI_API_KEY or self.index is None:
            return []

        try:
            # Generate embedding for query
            response = await asyncio.to_thread(
                genai.embed_content,
                model="models/gemini-embedding-001",
                content=query,
                task_type="retrieval_query"
            )
            query_embedding = np.array([response['embedding']]).astype('float32')

            # Search in FAISS
            distances, indices = self.index.search(query_embedding, top_k)
            
            results = []
            for idx in indices[0]:
                if idx != -1 and idx < len(self.chunks):
                    results.append(self.chunks[idx])
            
            return results
        except Exception as e:
            logging.error(f"Error searching RAG: {e}")
            return []

# Singleton instance
rag = RAGEngine()
