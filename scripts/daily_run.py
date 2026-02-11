#!/usr/bin/env python3
"""
Daily execution script
Run this every morning to generate insights for the day
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.data_collector import DataCollector
from src.graph.workflow import ResearchWorkflow
from src.models.llm_client import LLMClient
from src.models.reward_model import RewardModel
from src.models.embeddings import EmbeddingManager
from src.memory.postgres_manager import PostgresManager
from src.memory.cache import CacheManager
from src.utils.config import Config
from src.utils.logger import setup_logger

import logging
from datetime import datetime

def main():
    """Main daily execution function"""
    
    # Setup
    logger = setup_logger()
    config = Config()
    
    logger.info("=" * 60)
    logger.info(f"DAILY RUN STARTED: {datetime.now()}")
    logger.info("=" * 60)
    
    # Initialize components
    logger.info("Initializing components...")
    postgres = PostgresManager(config.postgres_params)
    cache = CacheManager(config.redis_params)
    llm_client = LLMClient(cache)
    embeddings = EmbeddingManager()
    
    # Step 1: Collect signals
    logger.info("\n[1/6] Collecting signals from NSE/BSE...")
    data_collector = DataCollector(postgres, cache)
    signals = data_collector.collect_daily_signals()
    logger.info(f"   Found {len(signals)} signals")
    
    # Step 2: Research signals
    logger.info("\n[2/6] Researching signals with multi-agent system...")
    workflow = ResearchWorkflow(llm_client, data_collector, postgres)
    
    insights = []
    for i, signal in enumerate(signals, 1):
        logger.info(f"   Processing signal {i}/{len(signals)}: {signal.get('signal_type')}")
        
        insight = workflow.research_signal(signal)
        if insight:
            insights.append(insight)
            # Handle string conversion for score if needed
            score = insight.get('interestingness_score', 0)
            logger.info(f"      → Generated insight (score: {score})")
    
    logger.info(f"   Generated {len(insights)} insights from {len(signals)} signals")
    
    # Step 3: Generate embeddings
    logger.info("\n[3/6] Generating embeddings...")
    for insight in insights:
        embedding = embeddings.embed_insight(insight)
        insight['embedding'] = embedding
    
    # Step 4: Apply reward model filter
    logger.info("\n[4/6] Applying quality filter...")
    reward_model = RewardModel(postgres)
    reward_model.train()  # Train on latest feedback
    
    for insight in insights:
        predicted_quality = reward_model.predict_quality(insight)
        insight['predicted_quality'] = predicted_quality
    
    # Rank by predicted quality
    insights.sort(key=lambda x: x.get('predicted_quality', 0), reverse=True)
    
    # Step 5: Select top N insights
    top_n = config.DAILY_INSIGHT_COUNT  # Default: 5
    selected_insights = insights[:top_n]
    
    logger.info(f"   Selected top {len(selected_insights)} insights")
    
    # Step 6: Store and present
    logger.info("\n[5/6] Storing insights in database...")
    for insight in selected_insights:
        insight_id = postgres.store_insight(insight)
        if insight_id:
            postgres.store_embedding(insight_id, insight['embedding'])
            company = insight.get('company_name', 'Unknown')
            headline = insight.get('headline', 'No Headline')
            logger.info(f"   Stored insight {insight_id}: {company} - {headline[:50]}...")
    
    # Step 7: Generate email/notification
    logger.info("\n[6/6] Generating daily digest...")
    generate_email_digest(selected_insights)
    
    logger.info("\n" + "=" * 60)
    logger.info(f"DAILY RUN COMPLETED: {datetime.now()}")
    logger.info(f"Generated {len(selected_insights)} insights for review")
    logger.info("=" * 60)

def generate_email_digest(insights):
    """Generate and send/save daily email digest"""
    # Simple version: Write to HTML file
    html = f"""
    <html>
    <head><title>Daily Investment Ideas - {datetime.now().strftime('%B %d, %Y')}</title></head>
    <body style="font-family: Arial; max-width: 800px; margin: 20px auto;">
        <h1>Top 5 Investment Ideas - {datetime.now().strftime('%B %d, %Y')}</h1>
    """
    
    for i, insight in enumerate(insights, 1):
        score = insight.get('interestingness_score', 0)
        
        html += f"""
        <div style="border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 8px;">
            <h2>#{i}: {insight.get('headline')}</h2>
            <p><strong>Company:</strong> {insight.get('company_name')} ({insight.get('company_symbol')})</p>
            <p><strong>Type:</strong> {insight.get('signal_type')}</p>
            
            <h3>Key Evidence:</h3>
            <ul>
        """
        
        evidence = insight.get('evidence', [])
        # Handle evidence if it's a string (though it should be list per synthesis agent)
        if isinstance(evidence, str):
            try:
                evidence = json.loads(evidence)
            except:
                evidence = [evidence]
                
        for fact in evidence:
            html += f"<li>{fact}</li>"
        
        html += f"""
            </ul>
            
            <h3>Analysis:</h3>
            <p>{insight.get('analysis')}</p>
            
            <p><strong>Interestingness Score:</strong> {score:.1f}/10</p>
        </div>
        """
    
    html += """
        <hr>
        <p><a href="http://localhost:5000">Click here to rate these insights</a></p>
    </body>
    </html>
    """
    
    # Save to file
    filename = f"daily_digest_{datetime.now().strftime('%Y%m%d')}.html"
    output_path = f"/tmp/{filename}"
    try:
        with open(output_path, 'w') as f:
            f.write(html)
        
        print(f"\nDaily digest saved to: {output_path}")
    except Exception as e:
        print(f"Failed to save digest: {e}")
    
    # TODO: Send via email using smtplib or external service

if __name__ == "__main__":
    main()
