import redis
import json
import logging
from typing import Any, Optional, Dict

class CacheManager:
    """Manages Redis caching"""
    
    def __init__(self, connection_params: Dict):
        self.redis = redis.Redis(**connection_params, decode_responses=True)
        self.logger = logging.getLogger(__name__)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            self.logger.error(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL (seconds)"""
        try:
            self.redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            self.logger.error(f"Redis set error: {e}")
