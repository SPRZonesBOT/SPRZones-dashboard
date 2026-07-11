from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
import torch
import torch.nn as nn

class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, name: str, model_path: Optional[str] = None):
        self.name = name
        self.model_path = model_path
        self.model = None
        self.load_model()
        
    @abstractmethod
    def load_model(self):
        """Load the pre-trained model"""
        pass
    
    @abstractmethod
    def predict(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Run inference on data"""
        pass
    
    @abstractmethod
    def get_signal(self, prediction: Dict) -> Dict:
        """Convert prediction to Buy/Hold/Sell signal"""
        pass
    
    def preprocess(self, data: pd.DataFrame) -> np.ndarray:
        """Preprocess data before feeding to model"""
        # Normalization logic
        return data.values
