from typing import Dict
from ..models.llm_client import LLMClient
from ..graph.state import ResearchState

class ValidationAgent:
    """
    Validates facts and checks for hallucinations/inconsistencies.
    Uses Qwen-Turbo for a second opinion.
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def __call__(self, state: ResearchState) -> Dict:
        """Validate research findings"""
        
        signal = state['signal']
        research_summary = f"""
        Signal: {signal['signal_type']}
        Deep Research: {state.get('level4_synthesis')}
        Industry: {state.get('industry_context')}
        """
        
        prompt = f"""You are a fact-checker. Review this investment research for internal consistency and logical flaws.
        
        {research_summary}
        
        1. Are there contradictions?
        2. Does the conclusion follow from the evidence?
        3. Are the risks adequately covered?
        
        Output:
        VERIFIED: [YES/NO]
        NOTES: [Brief notes on validity]
        """
        
        messages = [{"role": "user", "content": prompt}]
        # Use Qwen-2.5-72B via OpenRouter for validation
        response = self.llm.call_qwen(messages, model="qwen/qwen-2.5-72b-instruct", temperature=0.1)
        
        verified = "VERIFIED: YES" in response.upper()
        
        current_path = state.get('research_path', [])
        return {
            "facts_verified": verified,
            "validation_notes": response,
            "research_path": current_path + ["validation"]
        }
