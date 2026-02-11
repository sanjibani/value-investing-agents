import psycopg2
from psycopg2.extras import Json
import logging
from typing import List, Dict, Any, Optional

class PostgresManager:
    """Manages PostgreSQL database interactions"""
    
    def __init__(self, connection_params: Dict):
        self.conn_params = connection_params
        self.logger = logging.getLogger(__name__)
    
    def get_connection(self):
        """Get a database connection"""
        try:
            return psycopg2.connect(**self.conn_params)
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise

    def execute(self, query: str, params: tuple = None, fetch: str = None) -> Any:
        """
        Execute a query
        
        Args:
            query: SQL query
            params: Query parameters
            fetch: 'all', 'one', or None
            
        Returns:
            Fetched results or None
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(query, params)
                conn.commit()
                
                if fetch == 'all':
                    return cur.fetchall()
                elif fetch == 'one':
                    return cur.fetchone()
                return None
        except Exception as e:
            self.logger.error(f"Database error executing query: {e}")
            if conn:
                conn.rollback()
            # Re-raise or handle based on preference. For now, we log and return None/Empty for read ops? 
            # Ideally we should re-raise to let caller handle critical failures.
            # But the user's code expects .fetchall() returns list.
            if fetch == 'all':
                return []
            return None
        finally:
            if conn:
                conn.close()

    def store_insight(self, insight: Dict) -> int:
        """Store a generated insight"""
        import json
        
        query = """
            INSERT INTO insights (
                signal_type, company_symbol, company_name, 
                headline, evidence, analysis, interestingness_score,
                metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        params = (
            insight.get('signal_type'),
            insight.get('company_symbol'),
            insight.get('company_name'),
            insight.get('headline'),
            json.dumps(insight.get('evidence', [])),
            insight.get('analysis'),
            insight.get('interestingness_score'),
            json.dumps(insight.get('metadata', {}))
        )
        
        result = self.execute(query, params, fetch='one')
        return result[0] if result else None

    def store_embedding(self, insight_id: int, embedding: Any):
        """Store embedding for an insight"""
        # embedding should be a list or numpy array
        if hasattr(embedding, 'tolist'):
            embedding = embedding.tolist()
            
        update_query = "UPDATE insights SET embedding = %s WHERE id = %s"
        self.execute(update_query, (embedding, insight_id))
