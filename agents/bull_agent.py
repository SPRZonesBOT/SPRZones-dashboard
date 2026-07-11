import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from typing import Dict, Any
from .base_agent import BaseAgent

class LSTMPredictor(nn.Module):
    """LSTM for trend and momentum forecasting"""
    
    def __init__(self, input_size: int = 20, hidden_size: int = 128, 
                 num_layers: int = 3, output_size: int = 5):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.dropout = nn.Dropout(0.3)
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        return self.fc(self.dropout(lstm_out[:, -1, :]))


class BullAgent(BaseAgent):
    """Trend & Momentum Forecasting Agent"""
    
    def __init__(self, model_path: str = "models/bull_lstm.pth"):
        # Define feature_cols BEFORE calling parent __init__
        self.feature_cols = [
            'open', 'high', 'low', 'close', 'volume',
            'rsi', 'macd', 'macd_signal', 'bb_upper', 'bb_lower',
            'ema_9', 'ema_21', 'sma_50', 'sma_200',
            'volume_change', 'vwap'
        ]
        # Now call parent __init__
        super().__init__("Bull", model_path)
        # Explicitly load model after all attributes are set
        self.load_model()
    
    def load_model(self):
        """Load LSTM model with error handling for PyTorch 2.6+"""
        self.model = LSTMPredictor(input_size=len(self.feature_cols))
        if self.model_path:
            try:
                state_dict = torch.load(self.model_path, map_location='cpu', weights_only=False)
                self.model.load_state_dict(state_dict)
                print(f"✅ Bull Agent: Model loaded from {self.model_path}")
            except FileNotFoundError:
                print(f"⚠️ Bull Agent: Model file {self.model_path} not found. Using untrained model.")
            except Exception as e:
                print(f"⚠️ Bull Agent: Model file corrupted ({e}). Using untrained model.")
                # Reinitialize with random weights
                self.model = LSTMPredictor(input_size=len(self.feature_cols))
        else:
            print("ℹ️ Bull Agent: No model path provided. Using untrained model.")
        self.model.eval()
    
    def predict(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Forecast trend and momentum for next 5 days"""
        available_cols = [col for col in self.feature_cols if col in data.columns]
        if not available_cols:
            available_cols = ['close', 'volume']
            print(f"⚠️ Bull Agent: Using fallback columns: {available_cols}")
        
        features = data[available_cols].values[-100:]
        
        if len(features) < 10:
            print("⚠️ Bull Agent: Insufficient data for prediction. Using placeholder.")
            return {
                "forecast": [0.0, 0.0, 0.0, 0.0, 0.0],
                "trend_direction": "neutral",
                "momentum_score": 0.0,
                "breakout_probability": 0.5
            }
        
        features = (features - features.mean(axis=0)) / (features.std(axis=0) + 1e-8)
        X = torch.FloatTensor(features).unsqueeze(0)
        
        with torch.no_grad():
            predictions = self.model(X).numpy()[0]
        
        return {
            "forecast": predictions.tolist(),
            "trend_direction": "bullish" if predictions[-1] > predictions[0] else "bearish",
            "momentum_score": float(predictions[-1] / (predictions[0] + 1e-8) - 1),
            "breakout_probability": self._calculate_breakout_probability(data, predictions)
        }
    
    def _calculate_breakout_probability(self, data: pd.DataFrame, forecast: np.ndarray) -> float:
        if len(data) < 20:
            return 0.5
        
        try:
            if 'high' in data.columns and 'low' in data.columns:
                recent_high = data['high'].rolling(20).max().iloc[-1]
                recent_low = data['low'].rolling(20).min().iloc[-1]
            else:
                recent_high = data['close'].max()
                recent_low = data['close'].min()
            
            current_price = data['close'].iloc[-1]
            range_position = (current_price - recent_low) / (recent_high - recent_low + 1e-8)
            momentum_factor = 0.5 + 0.3 * (forecast[-1] > forecast[0])
            breakout_score = 0.3 * range_position + 0.3 * momentum_factor + 0.4 * (range_position > 0.7)
            return min(1.0, max(0.0, breakout_score))
        except Exception as e:
            print(f"⚠️ Bull Agent: Error calculating breakout probability: {e}")
            return 0.5
    
    def get_signal(self, prediction: Dict) -> Dict:
        momentum = prediction["momentum_score"]
        breakout_prob = prediction["breakout_probability"]
        
        if momentum > 0.02 and breakout_prob > 0.6:
            signal = "BUY"
            confidence = min(95, 70 + 20 * breakout_prob)
        elif momentum > 0.01 and breakout_prob > 0.4:
            signal = "BUY"
            confidence = 60 + 20 * breakout_prob
        elif momentum < -0.02:
            signal = "SELL"
            confidence = 75
        elif momentum < -0.01:
            signal = "SELL"
            confidence = 55
        else:
            signal = "HOLD"
            confidence = 50
        
        return {
            "agent": self.name,
            "signal": signal,
            "confidence": round(confidence, 1),
            "momentum": round(momentum * 100, 2),
            "breakout_prob": round(breakout_prob * 100, 1),
            "forecast": prediction["forecast"],
            "trend": prediction["trend_direction"]
        }
