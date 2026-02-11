import psycopg2
from typing import List, Dict, Tuple
import numpy as np

class VectorStore:
    """Manages vector similarity search in PostgreSQL with pgvector"""
    
    def __init__(self, connection_params: Dict):
        self.conn_params = connection_params
    
    def store_insight_embedding(self, insight_id: int, embedding: np.ndarray):
        """Store insight embedding"""
        with psycopg2.connect(**self.conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE insights 
                    SET embedding = %s 
                    WHERE id = %s
                """, (embedding.tolist(), insight_id))
                conn.commit()
    
    def find_similar_insights(
        self, 
        query_embedding: np.ndarray, 
        limit: int = 5,
        min_similarity: float = 0.7
    ) -> List[Tuple[int, float, Dict]]:
        """
        Find similar insights using cosine similarity
        
        Args:
            query_embedding: Query vector
            limit: Max results
            min_similarity: Minimum similarity threshold (0-1)
            
        Returns:
            List of (insight_id, similarity_score, insight_data)
        """
        with psycopg2.connect(**self.conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        id,
                        1 - (embedding <=> %s::vector) as similarity,
                        headline,
                        analysis,
                        interestingness_score,
                        created_at
                    FROM insights
                    WHERE 1 - (embedding <=> %s::vector) > %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (
                    query_embedding.tolist(),
                    query_embedding.tolist(),
                    min_similarity,
                    query_embedding.tolist(),
                    limit
                ))
                
                results = []
                for row in cur.fetchall():
                    results.append((
                        row[0],  # id
                        row[1],  # similarity
                        {
                            'headline': row[2],
                            'analysis': row[3],
                            'score': row[4],
                            'created_at': row[5]
                        }
                    ))
                
                return results
    
    def get_feedback_patterns(self, signal_type: str = None) -> List[Dict]:
        """
        Get insights that received high feedback
        
        Args:
            signal_type: Optional filter by signal type
            
        Returns:
            List of high-rated insights with feedback
        """
        with psycopg2.connect(**self.conn_params) as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT 
                        i.id,
                        i.signal_type,
                        i.headline,
                        i.analysis,
                        i.interestingness_score,
                        AVG(f.star_rating) as avg_rating,
                        COUNT(f.id) as feedback_count,
                        array_agg(DISTINCT unnest(f.tags)) as common_tags
                    FROM insights i
                    JOIN feedback f ON i.id = f.insight_id
                    WHERE f.star_rating >= 4
                """
                
                params = []
                if signal_type:
                    query += " AND i.signal_type = %s"
                    params.append(signal_type)
                
                query += """
                    GROUP BY i.id, i.signal_type, i.headline, i.analysis, i.interestingness_score
                    HAVING COUNT(f.id) > 0
                    ORDER BY AVG(f.star_rating) DESC, COUNT(f.id) DESC
                    LIMIT 20
                """
                
                cur.execute(query, tuple(params))
                
                results = []
                for row in cur.fetchall():
                    results.append({
                        'insight_id': row[0],
                        'signal_type': row[1],
                        'headline': row[2],
                        'analysis': row[3],
                        'original_score': row[4],
                        'avg_rating': float(row[5]),
                        'feedback_count': row[6],
                        'tags': row[7] if row[7] else []
                    })
                
                return results
