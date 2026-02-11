import os
from typing import List, Dict, Optional
import requests
import json
import hashlib
from tenacity import retry, stop_after_attempt, wait_exponential

class LLMClient:
    """Unified client for DeepSeek and Qwen APIs with caching and retry logic"""
    
    def __init__(self, cache_manager):
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.cache = cache_manager
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def call_deepseek(
        self, 
        messages: List[Dict],
        model: str = "deepseek/deepseek-chat", # OpenRouter ID for V3
        temperature: float = 0.3,
        max_tokens: int = 4000,
        use_cache: bool = True
    ) -> str:
        """
        Call DeepSeek via OpenRouter
        """
        # Check cache
        if use_cache:
            cache_key = self._generate_cache_key(model, messages, temperature)
            cached = self.cache.get(cache_key)
            if cached:
                return cached
        
        # Use OpenRouter API Key
        api_key = self.openrouter_key
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost:3000",
            "X-Title": "Value Investing Agent"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            output = result['choices'][0]['message']['content']
            
            # Cache the response
            if use_cache:
                self.cache.set(cache_key, output, ttl=86400)  # 24 hours
            
            return output
        except Exception as e:
            print(f"OpenRouter/DeepSeek API error: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def call_qwen(
        self,
        messages: List[Dict],
        model: str = "qwen/qwen-2.5-72b-instruct", # Default to OpenRouter ID
        temperature: float = 0.3,
        use_cache: bool = True
    ) -> str:
        """
        Call Qwen via OpenRouter
        
        Why OpenRouter?
        1. Solves the 'Region not supported' issue (e.g. India)
        2. Routes to US-based providers (Fireworks, Together) for better privacy
        3. Pricing is competitive ($0.35/M input approx)
        """
        # Check cache
        if use_cache:
            cache_key = self._generate_cache_key(model, messages, temperature)
            cached = self.cache.get(cache_key)
            if cached:
                return cached
        
        # Use OpenRouter API Key
        api_key = self.openrouter_key
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost:3000", # OpenRouter requires this
            "X-Title": "Value Investing Agent"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            output = result['choices'][0]['message']['content']
            
            if use_cache and output:
                self.cache.set(cache_key, output, ttl=86400)
            
            return output
        except Exception as e:
            print(f"OpenRouter/Qwen API error: {e}")
            # Fallback to DeepSeek if OpenRouter fails (redundancy)
            print("Falling back to DeepSeek V3...")
            return self.call_deepseek(messages, temperature=temperature, use_cache=use_cache)
    
    def _generate_cache_key(self, model: str, messages: List[Dict], temperature: float) -> str:
        """Generate cache key from request parameters"""
        content = json.dumps({
            "model": model,
            "messages": messages,
            "temperature": temperature
        }, sort_keys=True)
        
        return f"llm:{hashlib.sha256(content.encode()).hexdigest()}"
