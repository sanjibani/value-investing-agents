from typing import Dict
from ..models.llm_client import LLMClient
from ..graph.state import ResearchState

class ContextAgent:
    """
    Adds broader market and industry context to the research
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def __call__(self, state: ResearchState) -> Dict:
        """Analyze industry and macro context"""
        
        signal = state['signal']
        symbol = signal['data'].get('symbol')
        
        # We use DeepSeek for this broad analysis
        industry_context = self._analyze_industry(signal, state['level1_context'])
        peer_comparison = self._compare_peers(signal, state['level3_fundamentals'])
        
        current_path = state.get('research_path', [])
        return {
            "industry_context": industry_context,
            "peer_comparison": peer_comparison,
            "research_path": current_path + ["context"]
        }
    
    def _analyze_industry(self, signal: Dict, level1_context: str) -> str:
        prompt = f"""Analyze the industry context for {signal['data'].get('company')}.
        
        Context so far:
        {level1_context}
        
        1. What are the key tailwinds/headwinds for this industry in India?
        2. Are there regulatory changes impacting this sector?
        3. Is this sector currently in favor or out of favor?
        
        Provide concise industry insights."""
        
        messages = [{"role": "user", "content": prompt}]
        return self.llm.call_deepseek(messages, temperature=0.3)
        
    def _compare_peers(self, signal: Dict, level3_fundamentals: str) -> str:
        prompt = f"""Compare {signal['data'].get('company')} with its key listed peers in India.
        
        Fundamentals:
        {level3_fundamentals}
        
        1. Who are the main competitors?
        2. How does this company compare on valuation and growth?
        3. Is it a leader or follower?
        
        Provide a brief peer comparison."""
        
        messages = [{"role": "user", "content": prompt}]
        return self.llm.call_deepseek(messages, temperature=0.3)
