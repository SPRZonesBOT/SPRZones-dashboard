import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from typing import Dict, Any
import warnings
warnings.filterwarnings('ignore')

try:
    import arch
    ARCH_AVAILABLE = True
except ImportError:
    ARCH_AVAILABLE = False
    print("⚠️ Bear Agent: 'arch' package not installed. GARCH features will be limited.")

from .base_agent import BaseAgent

class GRUModel(nn.Module):
    def __init__(self, input_size: int = 15, hidden_size: int = 64, 
                 num_layers: int = 2, output_size: int = 3):
        super().__init__()
        self.gru = nn.GRU(input_size, hidden_size, num_layers, batch_first=True)
        self.dropout = nn.Dropout(0.2)
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        gru_out, _ = self.gru(x)
        return self.fc(self.dropout(gru_out[:, -1, :]))


class BearAgent(BaseAgent):
    def __init__(self, model_path: str = None):
        self.volatility_features = [
            'returns', 'high_low_ratio', 'volume_ratio',
            'atr', 'bb_width', 'keltner_width',
            'rvi', 'cvi', 'vix_fear_index'
        ]
        super().__init__("Bear", model_path)
        self.load_model()
    
    def load_model(self):
        """Create new GRU model with random weights (skip file loading)"""
        print("ℹ️ Bear Agent: Creating new GRU model with random weights.")
        self.model = GRUModel(input_size=len(self.volatility_features))
        self.model.eval()
        print("✅ Bear Agent: Ready with untrained GRU model.")
    
    def _fit_garch(self, returns: pd.Series) -> Dict:
        if not ARCH_AVAILABLE or len(returns) < 30:
            return {"garch_volatility": [0.02] * 5, "persistence": 0.98, "tail_risk": 0.15}
        
        try:
            clean_returns = returns.dropna().values * 100
            if len(clean_returns) < 30:
                return {"garch_volatility": [0.02] * 5, "persistence": 0.98, "tail_risk": 0.15}
            
            model = arch.arch_model(clean_returns, vol='GARCH', p=1, q=1)
            res = model.fit(disp='off')
            
            forecast = res.forecast(horizon=5)
            conditional_vol = np.sqrt(forecast.variance.values[-1, :])
            
            return {
                "garch_volatility": conditional_vol.tolist(),
                "persistence": min(1.0, res.params.get('omega', 0.01) + 
                                  res.params.get('alpha[1]', 0.05) + 
                                  res.params.get('beta[1]', 0.9)),
                "tail_risk": min(0.5, res.params.get('omega', 0.01) / 
                                (1 - res.params.get('beta[1]', 0.9) + 1e-8))
            }
        except Exception as e:
            return {"garch_volatility": [0.02] * 5, "persistence": 0.98, "tail_risk": 0.15}
    
    def _detect_anomalies(self, data: pd.DataFrame) -> Dict:
        try:
            returns = data['close'].pct_change().dropna()
            z_scores = np.abs((returns - returns.mean()) / (returns.std() + 1e-8))
            anomalies = z_scores > 2.5
            
            if 'volume' in data.columns:
                vol_ma = data['volume'].rolling(20).mean()
                vol_std = data['volume'].rolling(20).std()
                vol_z = np.abs((data['volume'] - vol_ma) / (vol_std + 1e-8))
                vol_spikes = vol_z > 2.0
                volume_spikes = sum(vol_spikes[-20:])
            else:
                volume_spikes = 0
            
            max_drawdown = (data['close'].max() - data['close'].min()) / (data['close'].max() + 1e-8) * 100
            
            return {
                "price_anomalies": int(sum(anomalies[-20:])),
                "volume_spikes": int(volume_spikes),
                "max_drawdown": float(max_drawdown)
            }
        except Exception as e:
            return {"price_anomalies": 0, "volume_spikes": 0, "max_drawdown": 5.0}
    
    def predict(self, data: pd.DataFrame) -> Dict[str, Any]:
        try:
            returns = data['close'].pct_change().dropna()
            
            features = []
            available_cols = [col for col in self.volatility_features if col in data.columns]
            
            if not available_cols:
                features = np.random.randn(100, len(self.volatility_features))
            else:
                feature_data = data[available_cols].values[-100:]
                if feature_data.shape[1] < len(self.volatility_features):
                    padding = np.random.randn(feature_data.shape[0], 
                                             len(self.volatility_features) - feature_data.shape[1])
                    feature_data = np.hstack([feature_data, padding])
                features = feature_data
            
            features = (features - features.mean(axis=0)) / (features.std(axis=0) + 1e-8)
            X_tensor = torch.FloatTensor(features).unsqueeze(0)
            
            with torch.no_grad():
                predictions = self.model(X_tensor).numpy()[0]
            
            garch = self._fit_garch(returns)
            anomalies = self._detect_anomalies(data)
            
            vol_score = 0.4 * np.mean(predictions) + 0.3 * np.mean(garch['garch_volatility']) + 0.3 * (anomalies['max_drawdown'] / 100)
            vol_score = min(1.0, max(0.0, vol_score * 5))
            
            return {
                "volatility_score": float(vol_score),
                "garch_forecast": garch['garch_volatility'],
                "persistence": garch['persistence'],
                "tail_risk": garch['tail_risk'],
                "anomalies": anomalies,
                "downside_probability": min(0.9, 0.3 + 0.5 * vol_score + 0.2 * (1 - garch['persistence']))
            }
        except Exception as e:
            return {
                "volatility_score": 0.3,
                "garch_forecast": [0.02] * 5,
                "persistence": 0.98,
                "tail_risk": 0.15,
                "anomalies": {"price_anomalies": 0, "volume_spikes": 0, "max_drawdown": 5.0},
                "downside_probability": 0.35
            }
    
    def get_signal(self, prediction: Dict) -> Dict:
        vol_score = prediction.get("volatility_score", 0.3)
        downside = prediction.get("downside_probability", 0.35)
        tail_risk = prediction.get("tail_risk", 0.15)
        
        if vol_score > 0.7 or downside > 0.6:
            signal = "SELL" if tail_risk > 0.2 else "HOLD"
            confidence = min(90, 60 + 30 * (vol_score + downside) / 2)
        elif vol_score > 0.4:
            signal = "HOLD"
            confidence = 65
        else:
            signal = "BUY"
            confidence = 70
        
        return {
            "agent": self.name,
            "signal": signal,
            "confidence": round(confidence, 1),
            "volatility_score": round(vol_score * 100, 1),
            "downside_risk": round(downside * 100, 1),
            "tail_risk": round(tail_risk * 100, 1),
            "anomalies": prediction.get("anomalies", {"price_anomalies": 0, "volume_spikes": 0, "max_drawdown": 5.0})
        }
