from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union

class EmbeddingManager:
    """Self-hosted embeddings using Sentence Transformers"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding model.
        Using MiniLM-L6-v2 (~80MB) for efficiency instead of BGE-Large (~1.5GB).
        """
        # Lazy load to avoid overhead on import if not used immediately?
        # But user script initializes it upfront.
        self.model = SentenceTransformer(model_name)
        # self.dimension = self.model.get_sentence_embedding_dimension()
    
    def embed_text(self, text: Union[str, List[str]]) -> np.ndarray:
        """Generate embeddings for text"""
        if isinstance(text, str):
            text = [text]
        
        embeddings = self.model.encode(
            text,
            normalize_embeddings=True,  # For cosine similarity
            show_progress_bar=False
        )
        
        return embeddings
    
    def embed_insight(self, insight: dict) -> np.ndarray:
        """Create embedding for an insight by combining relevant fields"""
        # Combine headline, analysis, and key evidence
        text = f"{insight.get('headline', '')} {insight.get('analysis', '')}"
        
        if 'evidence' in insight:
            evidence_texts = [e.get('fact', '') if isinstance(e, dict) else str(e) for e in insight['evidence']]
            text += " " + " ".join(evidence_texts)
        
        return self.embed_text(text)[0]
