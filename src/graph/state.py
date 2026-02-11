from typing import TypedDict, List, Dict, Optional, Annotated
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

class ResearchState(TypedDict):
    """State passed between agents in the research workflow"""
    
    # Input
    signal: Dict  # Raw signal from data collector
    
    # Discovery Agent outputs
    is_interesting: bool
    initial_assessment: str
    
    # Deep Research Agent outputs
    level1_context: Optional[str]  # Company basics, industry
    level2_historical: Optional[str]  # Past patterns, track record
    level3_fundamentals: Optional[str]  # Financial analysis
    level4_synthesis: Optional[str]  # What makes this interesting
    
    # Context Agent outputs
    industry_context: Optional[str]
    peer_comparison: Optional[str]
    macro_factors: Optional[str]
    
    # Validation Agent outputs
    facts_verified: bool
    validation_notes: str
    
    # Synthesis Agent outputs
    final_insight: Optional[Dict]  # {headline, evidence, analysis, score}
    
    # Quality Filter
    passes_threshold: bool
    interestingness_score: float
    
    # Metadata
    research_path: List[str]  # Track which agents were called
    errors: List[str]
    
    # LangGraph messages (for LLM conversations)
    messages: Annotated[List[BaseMessage], add_messages]
