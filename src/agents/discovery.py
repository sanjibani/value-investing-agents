from typing import Dict
from ..models.llm_client import LLMClient
from ..graph.state import ResearchState

class DiscoveryAgent:
    """
    Scans signals and determines if they warrant deep research
    Uses Qwen-Flash for fast, cheap filtering
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def __call__(self, state: ResearchState) -> Dict:
        """Process signal and decide if interesting"""
        
        signal = state['signal']
        
        prompt = self._build_discovery_prompt(signal)
        
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        # Use Qwen-2.5-72B via OpenRouter for high quality discovery
        response = self.llm.call_qwen(messages, model="qwen/qwen-2.5-72b-instruct", temperature=0.3)
        
        # Parse response
        is_interesting = "INTERESTING: YES" in response.upper()
        
        # Update state
        return {
            "is_interesting": is_interesting,
            "initial_assessment": response,
            "research_path": ["discovery"] # LangGraph appends to list? No, this overrides if not using reducer. 
            # But State definition has Annotated[List, ...]? Wait state definitions in typeddict are just types.
            # In LangGraph, returning a dict updates the state. 
            # For lists, we need to handle appending if we want history. 
            # The state definition had `research_path: List[str]`. 
            # If we return {"research_path": ["discovery"]}, it might overwrite.
            # We should probably append in the state update or use a reducer.
            # For simplicity let's assume LangGraph merges dicts. 
            # Actually, standard TypedDict state -> overwrite.
            # We should read the current state if we want to append?
            # Or just return the list we want to SET.
            # But `__call__` receives state.
        }
        # Correct approach:
        current_path = state.get('research_path', [])
        new_path = current_path + ["discovery"]
        
        return {
            "is_interesting": is_interesting,
            "initial_assessment": response,
            "research_path": new_path
        }

    
    def _get_system_prompt(self) -> str:
        return """You are a discovery agent for a value investing research system focused on special situations in Indian markets.

Your job is to quickly assess signals and determine if they warrant deeper research. Look for:

1. **Insider Activity**:
   - Promoter/director buying (especially above market price)
   - Large percentage changes in holdings
   - Multiple insiders buying simultaneously
   - Buying during market weakness

2. **Special Situations**:
   - Merger/demerger announcements with interesting terms
   - Buybacks at premium valuations
   - Delisting offers
   - Resolution plans for distressed companies
   - Asset monetization

3. **Corporate Actions**:
   - Unusual board meeting purposes
   - Rights issues with strong promoter participation
   - Bulk deals by credible institutions

4. **Red Flags to Ignore**:
   - Small insider sales (<₹1 lakh)
   - Routine compliance filings
   - Penny stocks (market cap <₹100 cr)
   - Promoter pledging (negative signal)

Output format:
INTERESTING: [YES/NO]
REASON: [1-2 sentences why this is/isn't interesting]
INITIAL_SCORE: [1-10]"""
    
    def _build_discovery_prompt(self, signal: Dict) -> str:
        signal_type = signal.get('signal_type')
        data = signal.get('data', {})
        
        if signal_type == "insider_trading":
            return f"""Insider Trading Signal:

Company: {data.get('company')} ({data.get('symbol')})
Person: {data.get('person')}
Category: {data.get('category')}
Transaction: {data.get('transaction_type')}
Securities Acquired: {data.get('securities_acquired', 0):,}
Holding Before: {data.get('percentage_before', 0):.2f}%
Holding After: {data.get('percentage_after', 0):.2f}%
Change: {data.get('percentage_after', 0) - data.get('percentage_before', 0):.2f}%

Assess if this is interesting."""
        
        elif signal_type == "merger_arb":
            return f"""Merger/Amalgamation Signal:

Company: {data.get('company')} ({data.get('symbol')})
Announcement: {data.get('subject')}

Assess if this presents an interesting merger arbitrage or special situation opportunity."""
        
        else:
            return f"""Signal Type: {signal_type}

Company: {data.get('company')} ({data.get('symbol')})
Details: {data.get('subject', 'N/A')}

Assess if this is an interesting special situation."""
