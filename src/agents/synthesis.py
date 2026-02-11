from typing import Dict, List
from ..models.llm_client import LLMClient
from ..graph.state import ResearchState
import json

class SynthesisAgent:
    """
    Synthesizes all research into a final structured insight.
    """
    
    def __init__(self, llm_client: LLMClient, postgres_manager):
        self.llm = llm_client
        self.postgres = postgres_manager
    
    def __call__(self, state: ResearchState) -> Dict:
        """Generate final insight"""
        
        signal = state['signal']
        
        # Gather all context
        full_context = f"""
        Signal: {signal['signal_type']}
        Company: {signal['data'].get('company')} ({signal['data'].get('symbol')})
        
        Initial Assessment: {state.get('initial_assessment')}
        
        Deep Research:
        {state.get('level4_synthesis')}
        
        Industry Context:
        {state.get('industry_context')}
        
        Peer Comparison:
        {state.get('peer_comparison')}
        
        Validation Notes:
        {state.get('validation_notes')}
        """
        
        prompt = f"""Create a final investment insight based on the research.
        
        {full_context}
        
        Output valid JSON with the following structure:
        {{
            "headline": "Catchy but accurate headline (max 10 words)",
            "analysis": "Detailed 3-paragraph analysis for an investor",
            "evidence": ["Fact 1", "Fact 2", "Fact 3"],
            "interestingness_score": <float 1-10>,
            "metadata": {{"risk_level": "High/Medium/Low", "time_horizon": "Short/Medium/Long"}}
        }}
        """
        
        messages = [
            {"role": "system", "content": "You are an expert investment editor. Output JSON only."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.call_deepseek(messages, temperature=0.4, max_tokens=1500)
        
        # Clean response to get JSON
        # This is a bit naive, production needs robust JSON extraction
        try:
            # Try to find JSON block
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = response[start:end]
                insight_data = json.loads(json_str)
            else:
                raise ValueError("No JSON found")
                
            # Add required fields
            insight_data['signal_type'] = signal['signal_type']
            insight_data['company_symbol'] = signal['data'].get('symbol')
            insight_data['company_name'] = signal['data'].get('company')
            
            passes_threshold = insight_data['interestingness_score'] >= 7.0
            
            current_path = state.get('research_path', [])
            return {
                "final_insight": insight_data,
                "passes_threshold": passes_threshold,
                "interestingness_score": insight_data['interestingness_score'],
                "research_path": current_path + ["synthesis"]
            }
            
        except Exception as e:
            current_path = state.get('research_path', [])
            return {
                "errors": state.get('errors', []) + [f"Synthesis Error: {str(e)}"],
                "research_path": current_path + ["synthesis_failed"]
            }
