import numpy as np
from sklearn.linear_model import LogisticRegression
from typing import Dict, List
import pickle

class RewardModel:
    """
    Simple reward model that learns from human feedback
    Predicts if an insight will be rated highly (4-5 stars)
    """
    
    def __init__(self, postgres_manager):
        self.postgres = postgres_manager
        self.model = LogisticRegression()
        self.is_trained = False
        self.feature_names = [
            'initial_score',
            'has_promoter_activity',
            'has_fundamental_confluence',
            'has_historical_precedent',
            'signal_priority',
            'fact_count',
            'analysis_length'
        ]
    
    def extract_features(self, insight: Dict) -> np.ndarray:
        """Extract features from insight for prediction"""
        features = []
        
        # Feature 1: Initial interestingness score
        features.append(insight.get('interestingness_score', 5.0))
        
        # Feature 2: Has promoter activity (binary)
        signal_type = insight.get('signal_type', '')
        features.append(1.0 if 'promoter' in signal_type.lower() else 0.0)
        
        # Feature 3: Has fundamental confluence (mentions both fundamentals and signal)
        analysis = insight.get('analysis', '').lower()
        has_confluence = 'fundamental' in analysis and 'signal' in analysis
        features.append(1.0 if has_confluence else 0.0)
        
        # Feature 4: Mentions historical precedent
        has_historical = any(word in analysis for word in ['past', 'historical', 'previously', 'track record'])
        features.append(1.0 if has_historical else 0.0)
        
        # Feature 5: Signal priority
        features.append(insight.get('signal', {}).get('priority', 5.0))
        
        # Feature 6: Number of evidence facts
        evidence = insight.get('evidence', [])
        features.append(float(len(evidence)))
        
        # Feature 7: Analysis length (proxy for depth)
        features.append(float(len(insight.get('analysis', ''))) / 1000.0)
        
        return np.array(features).reshape(1, -1)
    
    def train(self, min_samples: int = 20):
        """Train reward model on feedback data"""
        # Get training data from database
        # Note: Added fetch='all' to execute call based on PostgresManager implementation
        training_data = self.postgres.execute("""
            SELECT 
                i.interestingness_score,
                i.signal_type,
                i.analysis,
                i.evidence,
                i.metadata,
                f.star_rating,
                s.priority
            FROM insights i
            JOIN feedback f ON i.id = f.insight_id
            LEFT JOIN signals s ON i.metadata->>'signal_id' = s.id::text
            WHERE f.star_rating IS NOT NULL
        """, fetch='all')
        
        if not training_data or len(training_data) < min_samples:
            print(f"Not enough training data ({len(training_data) if training_data else 0}/{min_samples})")
            return False
        
        # Prepare features and labels
        X = []
        y = []
        
        for row in training_data:
            insight = {
                'interestingness_score': row[0],
                'signal_type': row[1],
                'analysis': row[2],
                'evidence': row[3],
                'metadata': row[4],
                'signal': {'priority': row[6] if row[6] is not None else 5}
            }
            
            features = self.extract_features(insight)[0]
            X.append(features)
            
            # Label: 1 if rated 4-5 stars, 0 otherwise
            label = 1 if row[5] >= 4 else 0
            y.append(label)
        
        X = np.array(X)
        y = np.array(y)
        
        # Train model
        self.model.fit(X, y)
        self.is_trained = True
        
        print(f"Reward model trained on {len(training_data)} samples")
        try:
            print(f"Feature importance: {dict(zip(self.feature_names, self.model.coef_[0]))}")
        except:
            pass
        
        return True
    
    def predict_quality(self, insight: Dict) -> float:
        """Predict probability that insight will be rated highly"""
        if not self.is_trained:
            # If not trained, return original score
            return insight.get('interestingness_score', 5.0) / 10.0
        
        features = self.extract_features(insight)
        probability = self.model.predict_proba(features)[0][1]
        
        return probability
    
    def save(self, path: str):
        """Save trained model to disk"""
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'is_trained': self.is_trained,
                'feature_names': self.feature_names
            }, f)
    
    def load(self, path: str):
        """Load trained model from disk"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.is_trained = data['is_trained']
            self.feature_names = data['feature_names']
