import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from .base_agent import BaseAgent

class CrossAttention(nn.Module):
    """Cross-attention transformer for portfolio weighting"""
    
    def __init__(self, num_agents: int = 4, d_model: int = 128, num_heads: int = 4):
        super().__init__()
        self.agent_embeddings = nn.Linear(10, d_model)  # Each agent's output vector
        self.cross_attn = nn.MultiheadAttention(d_model, num_heads, batch_first=True)
        self.fc = nn.Linear(d_model, 1)
        
    def forward(self, agent_outputs):
        # agent_outputs: (batch, num_agents, features)
        embeddings = self.agent_embeddings(agent_outputs)
        attn_out, _ = self.cross_attn(embeddings, embeddings, embeddings)
        weights = torch.softmax(self.fc(attn_out).squeeze(-1), dim=1)
        return weights


class ModeratorAgent(BaseAgent):
    """Portfolio Sizing & Decision Aggregation Agent"""
    
    def __init__(self, model_path: str = "models/moderator_transformer.pth"):
        super().__init__("Moderator", model_path)
        self.agent_outputs = {}
        
    def load_model(self):
        self.model = CrossAttention()
        if self.model_path:
            self.model.load_state_dict(torch.load(self.model_path))
        self.model.eval()
    
    def aggregate_agent_signals(self, agent_signals: List[Dict]) -> Dict[str, Any]:
        """Aggregate signals from all agents"""
        self.agent_outputs = {s['agent']: s for s in agent_signals}
        
        # Prepare input for cross-attention
        agent_features = []
        for signal in agent_signals:
            features = [
                signal.get('confidence', 50) / 100,
                signal.get('momentum', 0) / 100,
                signal.get('volatility_score', 0) / 100,
                signal.get('breakout_prob', 0) / 100,
                signal.get('downside_risk', 0) / 100,
                1 if signal['signal'] == 'BUY' else 0,
                1 if signal['signal'] == 'SELL' else 0,
                1 if signal['signal'] == 'HOLD' else 0,
                signal.get('trend', '') == 'bullish',
                signal.get('agent') == 'Bear'
            ]
            agent_features.append(features)
        
        X = torch.FloatTensor(np.array(agent_features)).unsqueeze(0)  # (1, num_agents, 10)
        
        with torch.no_grad():
            weights = self.model(X).numpy()[0]
        
        # Weighted decision
        signal_map = {'BUY': 1, 'HOLD': 0, 'SELL': -1}
        weighted_signal = sum(weights[i] * signal_map[self.agent_outputs[s['agent']]['signal']] 
                              for i, s in enumerate(agent_signals))
        
        if weighted_signal > 0.2:
            final_signal = "BUY"
        elif weighted_signal < -0.2:
            final_signal = "SELL"
        else:
            final_signal = "HOLD"
        
        confidence = abs(weighted_signal) * 100
        
        return {
            "final_signal": final_signal,
            "confidence": round(min(95, confidence), 1),
            "agent_weights": {list(self.agent_outputs.keys())[i]: round(weights[i] * 100, 1) 
                              for i in range(len(weights))},
            "consensus": round(weighted_signal * 100, 1),
            "detail": self.agent_outputs
        }
    
    def calculate_position_size(self, capital: float, risk_per_trade: float = 0.02) -> float:
        """Calculate position size based on risk"""
        max_loss = capital * risk_per_trade
        
        # Adjust based on volatility
        bear_agent = self.agent_outputs.get('Bear', {})
        vol_score = bear_agent.get('volatility_score', 50) / 100
        
        # Reduce position in high volatility
        volatility_adjustment = 1 - 0.5 * vol_score
        
        # Adjust based on confidence
        confidence = 0.7  # from moderator
        confidence_adjustment = 0.5 + 0.5 * (confidence / 100)
        
        position_size = max_loss * volatility_adjustment * confidence_adjustment
        
        return min(0.5 * capital, max(0.01 * capital, position_size))
    
    def get_signal(self, prediction: Dict) -> Dict:
        """Get final trading signal with position sizing"""
        return {
            "agent": self.name,
            "signal": prediction["final_signal"],
            "confidence": prediction["confidence"],
            "position_size": prediction.get("position_size", 0),
            "agent_weights": prediction.get("agent_weights", {}),
            "consensus": prediction.get("consensus", 0)
        }
    
    def predict(self, data: pd.DataFrame) -> Dict:
        """Override - handled via aggregation"""
        return self.agent_outputs
