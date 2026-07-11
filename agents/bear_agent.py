import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from typing import Dict, Any
import arch
from .base_agent import BaseAgent

class GRUModel(nn.Module):
    """GRU for volatility pattern recognition"""
    
    def __init__(self, input_size: int = 15, hidden_size: int = 64, 
                 num_layers: int = 2, output_size: int = 3):
        super().__init__()
        self.gru = nn.GRU(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        gru_out, _ = self.gru(x)
        return self.fc(gru_out[:, -1, :])


class BearAgent(BaseAgent):
    """Volatility & Risk Detection Agent"""
    
    def __init__(self, model_path: str = "models/bear_gru.pth"):
        super().__init__("Bear", model_path)
        self.volatility_features = [
            'returns', 'high_low_ratio', 'volume_ratio',
            'atr', 'bb_width', 'keltner_width',
            'rvi', 'cvi', 'vix_fear_index'
        ]
        
    def load_model(self):
        self.model = GRUModel(input_size=len(self.volatility_features))
        if self.model_path:
            self.model.load_state_dict(torch.load(self.model_path))
        self.model.eval()
    
    def _fit_garch(self, returns: pd.Series) -> Dict:
        """Fit GARCH model for volatility forecasting"""
        try:
            model = arch.arch_model(returns * 100, vol='GARCH', p=1, q=1)
            res = model.fit(disp='off')
            
            forecast = res.forecast(horizon=5)
            conditional_vol = np.sqrt(forecast.variance.values[-1, :])
            
            return {
                "garch_volatility": conditional_vol.tolist(),
                "persistence": res.params['omega'] + res.params['alpha[1]'] + res.params['beta[1]'],
                "tail_risk": res.params['omega'] / (1 - res.params['beta[1]'])
            }
        except:
            return {"garch_volatility": [0.02] * 5, "persistence": 0.98, "tail_risk": 0.15}
    
    def _detect_anomalies(self, data: pd.DataFrame) -> Dict:
        """Detect market anomalies using statistical methods"""
        returns = data['close'].pct_change().dropna()
        
        # Z-score based detection
        z_scores = np.abs((returns - returns.mean()) / returns.std())
        anomalies = z_scores > 2.5
        
        # Volume spikes
        vol_z = np.abs((data['volume'] - data['volume'].rolling(20).mean()) / data['volume'].rolling(20).std())
        vol_spikes = vol_z > 2.0
        
        return {
            "price_anomalies": sum(anomalies[-20:]),
            "volume_spikes": sum(vol_spikes[-20:]),
            "max_drawdown": (data['close'].max() - data['close'].min()) / data['close'].max() * 100
        }
    
    def predict(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Predict volatility spikes and downside risk"""
        # Calculate returns
        returns = data['close'].pct_change().dropna()
        
        # Prepare volatility features
        features = []
        for col in self.volatility_features:
            if col in data.columns:
                features.append(data[col].values[-100:])
            else:
                features.append(np.random.randn(100))
        
        X = np.array(features).T
        X = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-8)
        X_tensor = torch.FloatTensor(X).unsqueeze(0)
        
        with torch.no_grad():
            predictions = self.model(X_tensor).numpy()[0]
        
        # GARCH volatility forecast
        garch = self._fit_garch(returns)
        
        # Anomaly detection
        anomalies = self._detect_anomalies(data)
        
        # Combine volatility signals
        volatility_score = 0.4 * np.mean(predictions) + 0.3 * np.mean(garch['garch_volatility']) + 0.3 * (anomalies['max_drawdown'] / 100)
        volatility_score = min(1.0, max(0.0, volatility_score * 5))
        
        return {
            "volatility_score": float(volatility_score),
            "garch_forecast": garch['garch_volatility'],
            "persistence": garch['persistence'],
            "tail_risk": garch['tail_risk'],
            "anomalies": anomalies,
            "downside_probability": min(0.9, 0.3 + 0.5 * volatility_score + 0.2 * (1 - garch['persistence']))
        }
    
    def get_signal(self, prediction: Dict) -> Dict:
        """Generate risk-based signal"""
        vol_score = prediction["volatility_score"]
        downside = prediction["downside_probability"]
        tail_risk = prediction["tail_risk"]
        
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
            "anomalies": prediction["anomalies"]
        }
