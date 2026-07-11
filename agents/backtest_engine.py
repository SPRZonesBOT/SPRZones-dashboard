import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class BacktestEngine:
    """Historical replay and performance metrics"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        
    def run_backtest(self, data: pd.DataFrame, signals: pd.Series, 
                     stop_loss: float = 0.02, take_profit: float = 0.05) -> Dict:
        """Run backtest on historical data with signals"""
        self.capital = self.initial_capital
        self.trades = []
        self.equity_curve = []
        
        for i in range(1, len(data)):
            if signals.iloc[i] == 1 and 'position' not in self.positions:
                self._enter_position(data.iloc[i], stop_loss, take_profit)
            elif signals.iloc[i] == -1 and 'position' in self.positions:
                self._exit_position(data.iloc[i])
            
            self.equity_curve.append({
                'date': data.index[i],
                'equity': self.capital
            })
            
        equity_df = pd.DataFrame(self.equity_curve)
        
        return self._calculate_metrics(equity_df)
    
    def _enter_position(self, bar, stop_loss: float, take_profit: float):
        """Enter a position"""
        price = bar['close']
        self.positions = {
            'entry_price': price,
            'stop_loss': price * (1 - stop_loss),
            'take_profit': price * (1 + take_profit),
            'position_size': self.capital * 0.8  # 80% of capital
        }
    
    def _exit_position(self, bar):
        """Exit a position"""
        exit_price = bar['close']
        entry = self.positions['entry_price']
        size = self.positions['position_size']
        
        pnl = (exit_price - entry) / entry * size
        self.capital += pnl
        
        self.trades.append({
            'entry_date': None,
            'exit_date': bar.name if hasattr(bar, 'name') else None,
            'entry_price': entry,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_pct': (exit_price - entry) / entry * 100
        })
        
        del self.positions
    
    def _calculate_metrics(self, equity_df: pd.DataFrame) -> Dict:
        """Calculate performance metrics"""
        returns = equity_df['equity'].pct_change().dropna()
        
        # Basic metrics
        total_return = (equity_df['equity'].iloc[-1] - self.initial_capital) / self.initial_capital * 100
        
        # Risk metrics
        vol = returns.std() * np.sqrt(252)
        sharpe = (returns.mean() * 252) / vol if vol > 0 else 0
        
        # Drawdown
        peak = equity_df['equity'].expanding().max()
        drawdown = (equity_df['equity'] - peak) / peak
        max_drawdown = drawdown.min() * 100
        
        # Sortino
        downside_returns = returns[returns < 0]
        downside_vol = downside_returns.std() * np.sqrt(252)
        sortino = (returns.mean() * 252) / downside_vol if downside_vol > 0 else 0
        
        # Win rate
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        win_rate = len(winning_trades) / len(self.trades) * 100 if self.trades else 0
        
        # Profit factor
        gross_profit = sum(t['pnl'] for t in self.trades if t['pnl'] > 0)
        gross_loss = abs(sum(t['pnl'] for t in self.trades if t['pnl'] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return {
            "total_return": round(total_return, 2),
            "sharpe_ratio": round(sharpe, 3),
            "sortino_ratio": round(sortino, 3),
            "max_drawdown": round(max_drawdown, 2),
            "win_rate": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2),
            "total_trades": len(self.trades),
            "equity_curve": equity_df.to_dict('records'),
            "trades": self.trades,
            "cagr": round((1 + total_return / 100) ** (252 / len(equity_df)) - 1, 4)
        }
