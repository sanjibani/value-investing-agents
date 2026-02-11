from typing import Dict, Optional
from ..models.llm_client import LLMClient
from ..graph.state import ResearchState
from ..scrapers.data_collector import DataCollector

class DeepResearchAgent:
    """
    Performs 4-level deep research on interesting signals
    Uses DeepSeek V3 for complex reasoning
    """
    
    def __init__(self, llm_client: LLMClient, data_collector: DataCollector):
        self.llm = llm_client
        self.data = data_collector
    
    def __call__(self, state: ResearchState) -> Dict:
        """Execute multi-level research"""
        
        if not state.get('is_interesting'):
            return {"research_path": state.get('research_path', []) + ["deep_research_skipped"]}
        
        signal = state['signal']
        symbol = signal['data'].get('symbol')
        
        # Level 1: Basic Context
        level1_context = self._research_level1(signal, symbol)
        
        # Level 2: Historical Patterns
        level2_historical = self._research_level2(signal, symbol)
        
        # Level 3: Fundamental Analysis
        level3_fundamentals = self._research_level3(signal, symbol)
        
        # Level 4: Synthesis
        level4_synthesis = self._research_level4(state, level1_context, level2_historical, level3_fundamentals)
        
        current_path = state.get('research_path', [])
        return {
            "level1_context": level1_context,
            "level2_historical": level2_historical,
            "level3_fundamentals": level3_fundamentals,
            "level4_synthesis": level4_synthesis,
            "research_path": current_path + ["deep_research"]
        }
    
    def _research_level1(self, signal: Dict, symbol: str) -> str:
        """Level 1: Company basics and immediate context"""
        
        # Get fundamental data
        enriched = self.data.enrich_signal_with_fundamentals(signal)
        fundamentals = enriched.get('fundamentals', {})
        
        prompt = f"""You are researching {symbol}. Provide basic context:

Signal: {signal['signal_type']}
Company: {signal['data'].get('company')}

Fundamentals:
- Market Cap: {fundamentals.get('market_cap', 'N/A')}
- Sector: {fundamentals.get('sector', 'N/A')}
- Current Price: {fundamentals.get('current_price', 'N/A')}
- PE Ratio: {fundamentals.get('pe_ratio', 'N/A')}
- Promoter Holding: {fundamentals.get('promoter_holding', 'N/A')}

Provide:
1. What does this company do? (1-2 sentences)
2. What is the current business environment for this sector?
3. Is this a quality business based on available metrics?

Keep it factual and concise (max 200 words)."""
        
        messages = [
            {"role": "system", "content": "You are a financial analyst researching Indian companies."},
            {"role": "user", "content": prompt}
        ]
        
        return self.llm.call_deepseek(messages, temperature=0.2, max_tokens=500)
    
    def _research_level2(self, signal: Dict, symbol: str) -> str:
        """Level 2: Historical patterns and track record"""
        
        # TODO: Query database for past signals on this company
        
        prompt = f"""Analyze historical patterns for {symbol}:

Current Signal: {signal['signal_type']}
Details: {signal['data']}

Research questions:
1. Has this promoter/management shown good capital allocation in the past?
2. Have similar insider transactions preceded stock movements?
3. What is the company's track record with corporate actions?
4. Any past controversies or red flags?

Provide evidence-based analysis. If data is limited, acknowledge it."""
        
        messages = [
            {"role": "system", "content": "You are analyzing historical patterns. Be skeptical and demand evidence."},
            {"role": "user", "content": prompt}
        ]
        
        return self.llm.call_deepseek(messages, temperature=0.3, max_tokens=700)
    
    def _research_level3(self, signal: Dict, symbol: str) -> str:
        """Level 3: Fundamental deep dive"""
        
        enriched = self.data.enrich_signal_with_fundamentals(signal)
        fundamentals = enriched.get('fundamentals', {})
        
        prompt = f"""Fundamental analysis of {symbol}:

Financials:
- ROE: {fundamentals.get('roe', 'N/A')}
- ROCE: {fundamentals.get('roce', 'N/A')}
- Debt/Equity: {fundamentals.get('debt_to_equity', 'N/A')}
- Sales Growth (3Y): {fundamentals.get('sales_growth_3yr', 'N/A')}
- Profit Growth (3Y): {fundamentals.get('profit_growth_3yr', 'N/A')}
- Pledged %: {fundamentals.get('pledged_percentage', 'N/A')}

Given the signal ({signal['signal_type']}), analyze:
1. Are fundamentals improving or deteriorating?
2. Is valuation reasonable for the business quality?
3. Any balance sheet concerns?
4. Does this signal align with fundamental trajectory?

Provide specific numbers and insights."""
        
        messages = [
            {"role": "system", "content": "You are a fundamental analyst. Focus on facts and numbers."},
            {"role": "user", "content": prompt}
        ]
        
        return self.llm.call_deepseek(messages, temperature=0.2, max_tokens=800)
    
    def _research_level4(self, state: ResearchState, c1, c2, c3) -> str:
        """Level 4: Synthesize context"""
        signal = state['signal']
        
        prompt = f"""Synthesize the research into key insights:

SIGNAL: {signal['signal_type']}

CONTEXT: {c1}

HISTORICAL: {c2}

FUNDAMENTALS: {c3}

Provide:
1. **Core Thesis** (2-3 sentences): Why is this interesting?
2. **Key Evidence** (3-4 bullet points): Most compelling facts
3. **Risks/Concerns** (2-3 points): What could go wrong?
4. **Uniqueness** (1-2 sentences): Why would someone find this valuable?

Be specific and cite facts."""
        
        messages = [
            {"role": "system", "content": "You are synthesizing deep research into actionable insights for value investors."},
            {"role": "user", "content": prompt}
        ]
        
        return self.llm.call_deepseek(messages, temperature=0.4, max_tokens=1000)
