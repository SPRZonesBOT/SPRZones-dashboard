import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from .base_agent import BaseAgent

class CrossAttention(nn.Module):
    def __init__(self, num_agents: int = 4, d_model: int = 128, num_heads: int = 4):
        super().__init__()
        self.agent_embeddings = nn.Linear(10, d_model)
        self.cross_attn = nn.MultiheadAttention(d_model, num_heads, batch_first=True)
        self.fc = nn.Linear(d_model, 1)
        
    def forward(self, agent_outputs):
        embeddings = self.agent_embeddings(agent_outputs)
        attn_out, _ = self.cross_attn(embeddings, embeddings, embeddings)
        weights = torch.softmax(self.fc(attn_out).squeeze(-1), dim=1)
        return weights


class ModeratorAgent(BaseAgent):
    def __init__(self, model_path: str = "models/moderator_transformer.pth"):
        super().__init__("Moderator", model_path)
        self.agent_outputs = {}
        self.load_model()
    
    def load_model(self):
        """Load Transformer model with error handling for PyTorch 2.6+"""
        self.model = CrossAttention()
        if self.model_path:
            try:
                # FIX: Use weights_only=False for PyTorch 2.6+
                state_dict = torch.load(self.model_path, map_location='cpu', weights_only=False)
                self.model.load_state_dict(state_dict)
                print(f"✅ Moderator Agent: Model loaded from {self.model_path}")
            except FileNotFoundError:
                print(f"⚠️ Moderator Agent: Model file {self.model_path} not found. Using untrained model.")
            except Exception as e:
                print(f"⚠️ Moderator Agent: Error loading model: {e}. Using untrained model.")
        else:
            print("ℹ️ Moderator Agent: No model path provided. Using untrained model.")
        self.model.eval()
    
    def aggregate_agent_signals(self, agent_signals: List[Dict]) -> Dict[str, Any]:
        self.agent_outputs = {s['agent']: s for s in agent_signals}
        
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
                1 if signal.get('trend', '') == 'bullish' else 0,
                1 if signal.get('agent') == 'Bear' else 0
            ]
            agent_features.append(features)
        
        X = torch.FloatTensor(np.array(agent_features)).unsqueeze(0)
        
        try:
            with torch.no_grad():
                weights = self.model(X).numpy()[0]
        except Exception as e:
            print(f"⚠️ Moderator Agent: Model error: {e}. Using equal weights.")
            weights = np.ones(len(agent_signals)) / len(agent_signals)
        
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
        max_loss = capital * risk_per_trade
        bear_agent = self.agent_outputs.get('Bear', {})
        vol_score = bear_agent.get('volatility_score', 50) / 100
        volatility_adjustment = 1 - 0.5 * vol_score
        confidence = self.agent_outputs.get('Moderator', {}).get('confidence', 70) / 100
        confidence_adjustment = 0.5 + 0.5 * confidence
        position_size = max_loss * volatility_adjustment * confidence_adjustment
        return min(0.5 * capital, max(0.01 * capital, position_size))
    
    def get_signal(self, prediction: Dict) -> Dict:
        return {
            "agent": self.name,
            "signal": prediction.get("final_signal", "HOLD"),
            "confidence": prediction.get("confidence", 50),
            "position_size": prediction.get("position_size", 0),
            "agent_weights": prediction.get("agent_weights", {}),
            "consensus": prediction.get("consensus", 0)
        }
    
    def predict(self, data: pd.DataFrame) -> Dict:
        return self.agent_outputs
