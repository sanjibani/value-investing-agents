from langgraph.graph import StateGraph, END
from ..graph.state import ResearchState
from ..agents.discovery import DiscoveryAgent
from ..agents.deep_research import DeepResearchAgent
from ..agents.context import ContextAgent
from ..agents.validation import ValidationAgent
from ..agents.synthesis import SynthesisAgent
from typing import Dict, Optional

class ResearchWorkflow:
    """LangGraph workflow orchestrating multi-agent research"""
    
    def __init__(self, llm_client, data_collector, postgres_manager):
        # Initialize agents
        self.discovery = DiscoveryAgent(llm_client)
        self.deep_research = DeepResearchAgent(llm_client, data_collector)
        self.context = ContextAgent(llm_client)
        self.validation = ValidationAgent(llm_client)
        self.synthesis = SynthesisAgent(llm_client, postgres_manager)
        
        # Build graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the agent workflow graph"""
        
        workflow = StateGraph(ResearchState)
        
        # Add nodes (agents)
        workflow.add_node("discovery", self.discovery)
        workflow.add_node("deep_research", self.deep_research)
        workflow.add_node("context", self.context)
        workflow.add_node("validation", self.validation)
        workflow.add_node("synthesis", self.synthesis)
        
        # Define edges (workflow)
        workflow.set_entry_point("discovery")
        
        # Conditional routing after discovery
        workflow.add_conditional_edges(
            "discovery",
            self._should_continue_research,
            {
                "continue": "deep_research",
                "stop": END
            }
        )
        
        # Linear flow after deep research
        workflow.add_edge("deep_research", "context")
        workflow.add_edge("context", "validation")
        workflow.add_edge("validation", "synthesis")
        workflow.add_edge("synthesis", END)
        
        return workflow.compile()
    
    def _should_continue_research(self, state: ResearchState) -> str:
        """Decide if signal warrants deep research"""
        return "continue" if state.get('is_interesting') else "stop"
    
    def research_signal(self, signal: Dict) -> Optional[Dict]:
        """
        Run research workflow on a single signal
        
        Args:
            signal: Raw signal dictionary
            
        Returns:
            Final insight if interesting enough, None otherwise
        """
        initial_state = ResearchState(
            signal=signal,
            is_interesting=False,
            research_path=[],
            errors=[],
            messages=[]
        )
        
        # Run the graph
        try:
            final_state = self.graph.invoke(initial_state)
            
            # Return insight if it passes threshold
            if final_state.get('passes_threshold'):
                return final_state.get('final_insight')
        except Exception as e:
            print(f"Error executing workflow for signal {signal.get('signal_type')}: {e}")
            return None
        
        return None
