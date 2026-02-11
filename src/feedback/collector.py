from flask import Flask, render_template, request, jsonify
from typing import List, Dict
import os

class FeedbackCollector:
    """Simple web interface for collecting feedback"""
    
    def __init__(self, postgres_manager):
        self.postgres = postgres_manager
        # Ensure templates can be found. Assuming running from project root.
        template_dir = os.path.abspath(os.path.join(os.getcwd(), 'templates'))
        self.app = Flask(__name__, template_folder=template_dir)
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.route('/')
        def index():
            """Show today's insights for review"""
            insights = self._get_todays_insights()
            return render_template('feedback.html', insights=insights)
        
        @self.app.route('/submit_feedback', methods=['POST'])
        def submit_feedback():
            """Receive and store feedback"""
            data = request.json
            
            insight_id = data['insight_id']
            star_rating = data['star_rating']
            tags = data.get('tags', [])
            comment = data.get('comment', '')
            
            # Store in database
            self.postgres.execute("""
                INSERT INTO feedback (insight_id, star_rating, tags, comment)
                VALUES (%s, %s, %s, %s)
            """, (insight_id, star_rating, tags, comment))
            
            return jsonify({'status': 'success'})
    
    def _get_todays_insights(self) -> List[Dict]:
        """Get insights shown today"""
        # Note: Using fetch='all' as per PostgresManager implementation
        results = self.postgres.execute("""
            SELECT 
                id, 
                signal_type,
                company_name,
                headline,
                evidence,
                analysis,
                interestingness_score
            FROM insights
            WHERE DATE(created_at) = CURRENT_DATE
            AND shown_to_user = TRUE
            ORDER BY interestingness_score DESC
        """, fetch='all')
        
        insights = []
        if results:
            for row in results:
                insights.append({
                    'id': row[0],
                    'signal_type': row[1],
                    'company': row[2],
                    'headline': row[3],
                    'evidence': row[4],
                    'analysis': row[5],
                    'score': row[6]
                })
        
        return insights
    
    def run(self, host='0.0.0.0', port=5000):
        """Start feedback web server"""
        self.app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    # Standalone run for testing (requires initialized postgres manager)
    # This block is mainly for testing if the script is run directly
    pass
