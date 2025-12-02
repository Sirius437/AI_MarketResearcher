"""Portfolio management for cryptocurrency trading."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
from pathlib import Path

from config.settings import MarketResearcherConfig
from .risk_calculator import RiskCalculator

logger = logging.getLogger(__name__)


class PortfolioManager:
    """Manage cryptocurrency trading portfolio."""
    
    def __init__(self, config: MarketResearcherConfig):
        """Initialize portfolio manager."""
        self.config = config
        self.risk_calculator = RiskCalculator(config)
        
        # Portfolio state
        self.positions = {}
        self.cash_balance = config.initial_balance
        self.total_value = config.initial_balance
        self.base_currency = config.base_currency
    
    async def initialize(self):
        """Initialize portfolio manager and load existing data."""
        try:
            # Load existing portfolio data if available
            self._load_portfolio()
            logger.info("Portfolio manager initialized successfully")
        except Exception as e:
            logger.warning(f"Could not load existing portfolio data: {e}")
            # Continue with default initialization
        
        # Performance tracking
        self.trade_history = []
        self.performance_history = []
        self.daily_returns = []
        
        # Portfolio file path
        self.portfolio_file = Path(self.config.data_cache_dir) / "portfolio.json"
        self.portfolio_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing portfolio if available
        self._load_portfolio()
        
        logger.info(f"Portfolio manager initialized with {self.cash_balance} {self.base_currency}")
    
    def get_positions(self) -> Dict[str, Any]:
        """Get all current positions."""
        try:
            self._update_portfolio_value()
            return {
                "success": True,
                "positions": self.positions,
                "positions_count": len(self.positions),
                "total_value": self.total_value,
                "cash_balance": self.cash_balance
            }
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {"success": False, "error": str(e)}
    
    
    def get_cash_balance(self) -> float:
        """Get current cash balance."""
        return self.cash_balance
    
    def adjust_cash_balance(self, amount: float, reason: str = "Manual adjustment") -> Dict[str, Any]:
        """Adjust cash balance by specified amount."""
        try:
            if amount == 0:
                return {"success": False, "error": "Amount cannot be zero"}
            
            old_balance = self.cash_balance
            self.cash_balance += amount
            
            # Prevent negative cash balance
            if self.cash_balance < 0:
                self.cash_balance = old_balance
                return {"success": False, "error": "Adjustment would result in negative cash balance"}
            
            # Update total portfolio value
            self._update_portfolio_value()
            
            # Record the adjustment
            adjustment_record = {
                "timestamp": datetime.now().isoformat(),
                "type": "cash_adjustment",
                "amount": amount,
                "old_balance": old_balance,
                "new_balance": self.cash_balance,
                "reason": reason
            }
            
            # Add to trade history for tracking
            if not hasattr(self, 'cash_adjustments'):
                self.cash_adjustments = []
            self.cash_adjustments.append(adjustment_record)
            
            # Save portfolio
            self._save_portfolio()
            
            return {
                "success": True,
                "old_balance": old_balance,
                "new_balance": self.cash_balance,
                "adjustment": amount,
                "reason": reason,
                "message": f"Cash balance adjusted by ${amount:.2f}"
            }
            
        except Exception as e:
            logger.error(f"Error adjusting cash balance: {e}")
            return {"success": False, "error": str(e)}
    
    def analyze_risk(self) -> Dict[str, Any]:
        """Analyze portfolio risk metrics."""
        try:
            if not self.positions:
                return {
                    "success": True,
                    "message": "No positions to analyze",
                    "risk_metrics": {
                        "portfolio_risk": 0.0,
                        "concentration_risk": 0.0,
                        "volatility_risk": "Low",
                        "diversification_score": 0.0
                    }
                }
            
            # Calculate position weights
            total_position_value = sum(
                pos["quantity"] * pos["current_price"] 
                for pos in self.positions.values()
            )
            
            if total_position_value == 0:
                return {
                    "success": True,
                    "message": "No significant position values to analyze",
                    "risk_metrics": {
                        "portfolio_risk": 0.0,
                        "concentration_risk": 0.0,
                        "volatility_risk": "Low",
                        "diversification_score": 0.0
                    }
                }
            
            position_weights = {}
            for symbol, position in self.positions.items():
                position_value = position["quantity"] * position["current_price"]
                weight = position_value / total_position_value
                position_weights[symbol] = weight
            
            # Concentration risk (max single position weight)
            max_weight = max(position_weights.values()) if position_weights else 0
            concentration_risk = max_weight * 100
            
            # Diversification score (inverse of concentration)
            num_positions = len(self.positions)
            diversification_score = min(100, (num_positions / 10) * 100)
            
            # Portfolio risk assessment
            if concentration_risk > 50:
                risk_level = "High"
            elif concentration_risk > 25:
                risk_level = "Medium"
            else:
                risk_level = "Low"
            
            # Volatility assessment based on crypto types
            high_vol_assets = ['BTC', 'ETH', 'BNB']
            high_vol_exposure = sum(
                weight for symbol, weight in position_weights.items()
                if any(asset in symbol for asset in high_vol_assets)
            )
            
            if high_vol_exposure > 0.7:
                volatility_risk = "High"
            elif high_vol_exposure > 0.4:
                volatility_risk = "Medium"
            else:
                volatility_risk = "Low"
            
            return {
                "success": True,
                "risk_metrics": {
                    "portfolio_risk": risk_level,
                    "concentration_risk": round(concentration_risk, 2),
                    "volatility_risk": volatility_risk,
                    "diversification_score": round(diversification_score, 2),
                    "num_positions": num_positions,
                    "largest_position": max(position_weights.keys(), key=position_weights.get) if position_weights else None,
                    "largest_position_weight": round(max_weight * 100, 2) if position_weights else 0
                },
                "position_weights": {k: round(v * 100, 2) for k, v in position_weights.items()},
                "recommendations": self._get_risk_recommendations(concentration_risk, diversification_score, volatility_risk)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio risk: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_risk_recommendations(self, concentration_risk: float, diversification_score: float, volatility_risk: str) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []
        
        if concentration_risk > 50:
            recommendations.append("Consider reducing concentration in largest position")
        
        if diversification_score < 50:
            recommendations.append("Consider adding more positions to improve diversification")
        
        if volatility_risk == "High":
            recommendations.append("High volatility exposure - consider adding stable assets")
        
        if len(recommendations) == 0:
            recommendations.append("Portfolio risk profile appears balanced")
        
        return recommendations
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get portfolio performance metrics."""
        try:
            if not self.positions:
                return {
                    "success": True,
                    "message": "No positions to analyze performance",
                    "metrics": {
                        "total_return": 0.0,
                        "total_return_pct": 0.0,
                        "unrealized_pnl": 0.0,
                        "portfolio_value": self.cash_balance,
                        "invested_amount": 0.0,
                        "cash_balance": self.cash_balance
                    }
                }
            
            # Calculate performance metrics
            total_invested = 0.0
            current_value = 0.0
            total_pnl = 0.0
            
            position_performance = {}
            
            for symbol, position in self.positions.items():
                quantity = position["quantity"]
                avg_price = position["avg_price"]
                current_price = position["current_price"]
                
                invested_amount = quantity * avg_price
                position_value = quantity * current_price
                position_pnl = position_value - invested_amount
                position_pnl_pct = (position_pnl / invested_amount * 100) if invested_amount > 0 else 0
                
                total_invested += invested_amount
                current_value += position_value
                total_pnl += position_pnl
                
                position_performance[symbol] = {
                    "invested": round(invested_amount, 2),
                    "current_value": round(position_value, 2),
                    "pnl": round(position_pnl, 2),
                    "pnl_pct": round(position_pnl_pct, 2),
                    "quantity": quantity,
                    "avg_price": avg_price,
                    "current_price": current_price
                }
            
            # Overall portfolio metrics
            total_return_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0
            total_portfolio_value = current_value + self.cash_balance
            
            # Performance categorization
            if total_return_pct > 10:
                performance_rating = "Excellent"
            elif total_return_pct > 5:
                performance_rating = "Good"
            elif total_return_pct > 0:
                performance_rating = "Positive"
            elif total_return_pct > -5:
                performance_rating = "Slight Loss"
            else:
                performance_rating = "Poor"
            
            # Best and worst performers
            best_performer = max(position_performance.items(), key=lambda x: x[1]["pnl_pct"]) if position_performance else None
            worst_performer = min(position_performance.items(), key=lambda x: x[1]["pnl_pct"]) if position_performance else None
            
            return {
                "success": True,
                "metrics": {
                    "total_return": round(total_pnl, 2),
                    "total_return_pct": round(total_return_pct, 2),
                    "unrealized_pnl": round(total_pnl, 2),
                    "portfolio_value": round(total_portfolio_value, 2),
                    "position_value": round(current_value, 2),
                    "invested_amount": round(total_invested, 2),
                    "cash_balance": round(self.cash_balance, 2),
                    "performance_rating": performance_rating,
                    "num_positions": len(self.positions),
                    "best_performer": best_performer[0] if best_performer else None,
                    "best_performer_pnl": best_performer[1]["pnl_pct"] if best_performer else 0,
                    "worst_performer": worst_performer[0] if worst_performer else None,
                    "worst_performer_pnl": worst_performer[1]["pnl_pct"] if worst_performer else 0
                },
                "position_performance": position_performance,
                "summary": {
                    "profitable_positions": len([p for p in position_performance.values() if p["pnl"] > 0]),
                    "losing_positions": len([p for p in position_performance.values() if p["pnl"] < 0]),
                    "breakeven_positions": len([p for p in position_performance.values() if p["pnl"] == 0])
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {"success": False, "error": str(e)}
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary."""
        try:
            self._update_portfolio_value()
            
            # Calculate position values
            position_values = {}
            total_position_value = 0
            
            for symbol, position in self.positions.items():
                current_value = position["quantity"] * position.get("current_price", position["avg_price"])
                position_values[symbol] = current_value
                total_position_value += current_value
            
            # Calculate allocation percentages
            allocations = {}
            if self.total_value > 0:
                allocations = {
                    symbol: (value / self.total_value) * 100 
                    for symbol, value in position_values.items()
                }
                allocations["cash"] = (self.cash_balance / self.total_value) * 100
            
            # Calculate P&L
            total_invested = sum(
                pos["quantity"] * pos["avg_price"] 
                for pos in self.positions.values()
            )
            unrealized_pnl = total_position_value - total_invested
            
            return {
                "total_value": self.total_value,
                "cash_balance": self.cash_balance,
                "invested_value": total_position_value,
                "positions_count": len(self.positions),
                "allocations": allocations,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": (unrealized_pnl / total_invested * 100) if total_invested > 0 else 0,
                "positions": self._format_positions_summary(),
                "performance": self._calculate_performance_metrics(),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {"error": str(e)}
    
    def add_position(
        self, 
        symbol: str, 
        quantity: float, 
        price: float, 
        side: str = "long",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add or update a position in the portfolio."""
        try:
            if quantity <= 0 or price <= 0:
                return {"success": False, "error": "Invalid quantity or price"}
            
            position_value = quantity * price
            
            # Check if we have enough cash for new position
            if side == "long" and position_value > self.cash_balance:
                return {
                    "success": False, 
                    "error": f"Insufficient cash. Required: {position_value}, Available: {self.cash_balance}"
                }
            
            # Update or create position
            if symbol in self.positions:
                # Update existing position
                existing = self.positions[symbol]
                
                if existing["side"] == side:
                    # Same side - average the price
                    total_quantity = existing["quantity"] + quantity
                    total_value = (existing["quantity"] * existing["avg_price"]) + (quantity * price)
                    new_avg_price = total_value / total_quantity
                    
                    self.positions[symbol].update({
                        "quantity": total_quantity,
                        "avg_price": new_avg_price,
                        "last_updated": datetime.now().isoformat()
                    })
                else:
                    # Opposite side - reduce or flip position
                    if quantity >= existing["quantity"]:
                        # Flip or close position
                        remaining_quantity = quantity - existing["quantity"]
                        if remaining_quantity > 0:
                            self.positions[symbol] = {
                                "symbol": symbol,
                                "quantity": remaining_quantity,
                                "avg_price": price,
                                "side": side,
                                "entry_date": datetime.now().isoformat(),
                                "last_updated": datetime.now().isoformat(),
                                "metadata": metadata or {}
                            }
                        else:
                            # Close position completely
                            del self.positions[symbol]
                    else:
                        # Reduce existing position
                        self.positions[symbol]["quantity"] -= quantity
                        self.positions[symbol]["last_updated"] = datetime.now().isoformat()
            else:
                # New position
                self.positions[symbol] = {
                    "symbol": symbol,
                    "quantity": quantity,
                    "avg_price": price,
                    "side": side,
                    "entry_date": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "current_price": price,
                    "metadata": metadata or {}
                }
            
            # Update cash balance
            if side == "long":
                self.cash_balance -= position_value
            else:
                self.cash_balance += position_value  # For short positions (if supported)
            
            # Record trade
            self._record_trade(symbol, quantity, price, side, "add_position")
            
            # Save portfolio
            self._save_portfolio()
            
            return {
                "success": True,
                "message": f"Position updated for {symbol}",
                "position": self.positions.get(symbol, {}),
                "remaining_cash": self.cash_balance
            }
            
        except Exception as e:
            logger.error(f"Error adding position for {symbol}: {e}")
            return {"success": False, "error": str(e)}
    
    def close_position(
        self, 
        symbol: str, 
        quantity: Optional[float] = None, 
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Close a position partially or completely."""
        try:
            if symbol not in self.positions:
                return {"success": False, "error": f"No position found for {symbol}"}
            
            position = self.positions[symbol]
            close_quantity = quantity or position["quantity"]
            close_price = price or position.get("current_price", position["avg_price"])
            
            if close_quantity > position["quantity"]:
                return {"success": False, "error": "Cannot close more than current position"}
            
            # Calculate P&L
            entry_value = close_quantity * position["avg_price"]
            exit_value = close_quantity * close_price
            pnl = exit_value - entry_value if position["side"] == "long" else entry_value - exit_value
            pnl_pct = (pnl / entry_value) * 100 if entry_value > 0 else 0
            
            # Update cash balance
            self.cash_balance += exit_value
            
            # Update or remove position
            if close_quantity >= position["quantity"]:
                # Close completely
                del self.positions[symbol]
            else:
                # Partial close
                self.positions[symbol]["quantity"] -= close_quantity
                self.positions[symbol]["last_updated"] = datetime.now().isoformat()
            
            # Record trade
            self._record_trade(symbol, close_quantity, close_price, position["side"], "close_position", pnl)
            
            # Save portfolio
            self._save_portfolio()
            
            return {
                "success": True,
                "message": f"Position closed for {symbol}",
                "closed_quantity": close_quantity,
                "close_price": close_price,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "remaining_cash": self.cash_balance
            }
            
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
            return {"success": False, "error": str(e)}
    
    def update_position_prices(self, price_data: Dict[str, float]) -> Dict[str, Any]:
        """Update current prices for all positions."""
        try:
            updated_count = 0
            
            for symbol in self.positions:
                if symbol in price_data:
                    self.positions[symbol]["current_price"] = price_data[symbol]
                    self.positions[symbol]["last_updated"] = datetime.now().isoformat()
                    updated_count += 1
            
            # Update total portfolio value
            self._update_portfolio_value()
            
            # Record performance snapshot
            self._record_performance_snapshot()
            
            return {
                "success": True,
                "updated_positions": updated_count,
                "total_value": self.total_value
            }
            
        except Exception as e:
            logger.error(f"Error updating position prices: {e}")
            return {"success": False, "error": str(e)}
    
    def get_position_details(self, symbol: str) -> Dict[str, Any]:
        """Get detailed information about a specific position."""
        try:
            if symbol not in self.positions:
                return {"error": f"No position found for {symbol}"}
            
            position = self.positions[symbol]
            current_price = position.get("current_price", position["avg_price"])
            
            # Calculate metrics
            entry_value = position["quantity"] * position["avg_price"]
            current_value = position["quantity"] * current_price
            unrealized_pnl = current_value - entry_value
            unrealized_pnl_pct = (unrealized_pnl / entry_value) * 100 if entry_value > 0 else 0
            
            # Calculate holding period
            entry_date = datetime.fromisoformat(position["entry_date"])
            holding_days = (datetime.now() - entry_date).days
            
            return {
                "symbol": symbol,
                "quantity": position["quantity"],
                "avg_price": position["avg_price"],
                "current_price": current_price,
                "side": position["side"],
                "entry_value": entry_value,
                "current_value": current_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct,
                "holding_days": holding_days,
                "entry_date": position["entry_date"],
                "last_updated": position["last_updated"],
                "metadata": position.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Error getting position details for {symbol}: {e}")
            return {"error": str(e)}
    
    def calculate_position_size(
        self, 
        symbol: str, 
        entry_price: float, 
        stop_loss: float,
        risk_per_trade: Optional[float] = None
    ) -> Dict[str, Any]:
        """Calculate optimal position size based on risk management."""
        try:
            return self.risk_calculator.calculate_position_size(
                symbol=symbol,
                entry_price=entry_price,
                stop_loss=stop_loss,
                portfolio_value=self.total_value,
                available_cash=self.cash_balance,
                risk_per_trade=risk_per_trade
            )
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return {"error": str(e)}
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get portfolio risk metrics."""
        try:
            return self.risk_calculator.calculate_portfolio_risk(
                positions=self.positions,
                total_value=self.total_value,
                daily_returns=self.daily_returns
            )
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {"error": str(e)}
    
    def get_trade_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent trade history."""
        try:
            return self.trade_history[-limit:] if self.trade_history else []
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
            return []
    
    def get_performance_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate performance report for specified period."""
        try:
            if not self.performance_history:
                return {"error": "No performance history available"}
            
            # Filter performance data
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_performance = [
                p for p in self.performance_history 
                if datetime.fromisoformat(p["timestamp"]) >= cutoff_date
            ]
            
            if not recent_performance:
                return {"error": f"No performance data for last {days} days"}
            
            # Calculate metrics
            values = [p["total_value"] for p in recent_performance]
            returns = [(values[i] - values[i-1]) / values[i-1] for i in range(1, len(values))]
            
            total_return = (values[-1] - values[0]) / values[0] if values[0] > 0 else 0
            avg_daily_return = np.mean(returns) if returns else 0
            volatility = np.std(returns) if len(returns) > 1 else 0
            sharpe_ratio = avg_daily_return / volatility if volatility > 0 else 0
            
            # Max drawdown
            peak = values[0]
            max_drawdown = 0
            for value in values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            return {
                "period_days": days,
                "start_value": values[0],
                "end_value": values[-1],
                "total_return": total_return,
                "total_return_pct": total_return * 100,
                "avg_daily_return": avg_daily_return,
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "max_drawdown_pct": max_drawdown * 100,
                "total_trades": len([t for t in self.trade_history 
                                   if datetime.fromisoformat(t["timestamp"]) >= cutoff_date])
            }
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"error": str(e)}
    
    def rebalance_portfolio(self, target_allocations: Dict[str, float]) -> Dict[str, Any]:
        """Rebalance portfolio to target allocations."""
        try:
            self._update_portfolio_value()
            
            # Validate target allocations
            total_allocation = sum(target_allocations.values())
            if abs(total_allocation - 1.0) > 0.01:
                return {"success": False, "error": "Target allocations must sum to 1.0"}
            
            current_allocations = self._calculate_current_allocations()
            rebalance_trades = []
            
            for symbol, target_pct in target_allocations.items():
                current_pct = current_allocations.get(symbol, 0)
                difference = target_pct - current_pct
                
                if abs(difference) > 0.01:  # 1% threshold
                    target_value = self.total_value * target_pct
                    current_value = self.total_value * current_pct
                    trade_value = target_value - current_value
                    
                    rebalance_trades.append({
                        "symbol": symbol,
                        "current_allocation": current_pct,
                        "target_allocation": target_pct,
                        "trade_value": trade_value,
                        "action": "buy" if trade_value > 0 else "sell"
                    })
            
            return {
                "success": True,
                "rebalance_trades": rebalance_trades,
                "total_value": self.total_value,
                "message": f"Rebalancing requires {len(rebalance_trades)} trades"
            }
            
        except Exception as e:
            logger.error(f"Error rebalancing portfolio: {e}")
            return {"success": False, "error": str(e)}
    
    def _update_portfolio_value(self):
        """Update total portfolio value."""
        try:
            position_value = sum(
                pos["quantity"] * pos.get("current_price", pos["avg_price"])
                for pos in self.positions.values()
            )
            self.total_value = self.cash_balance + position_value
        except Exception as e:
            logger.error(f"Error updating portfolio value: {e}")
    
    def _format_positions_summary(self) -> List[Dict[str, Any]]:
        """Format positions for summary display."""
        try:
            summary = []
            for symbol, position in self.positions.items():
                current_price = position.get("current_price", position["avg_price"])
                entry_value = position["quantity"] * position["avg_price"]
                current_value = position["quantity"] * current_price
                pnl = current_value - entry_value
                pnl_pct = (pnl / entry_value) * 100 if entry_value > 0 else 0
                
                summary.append({
                    "symbol": symbol,
                    "quantity": position["quantity"],
                    "avg_price": position["avg_price"],
                    "current_price": current_price,
                    "value": current_value,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "allocation_pct": (current_value / self.total_value) * 100 if self.total_value > 0 else 0
                })
            
            return sorted(summary, key=lambda x: x["value"], reverse=True)
        except Exception as e:
            logger.error(f"Error formatting positions summary: {e}")
            return []
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate basic performance metrics."""
        try:
            if not self.daily_returns:
                return {"error": "No return data available"}
            
            returns = np.array(self.daily_returns)
            
            return {
                "total_return": (self.total_value / self.config.initial_balance - 1) * 100,
                "avg_daily_return": np.mean(returns) * 100,
                "volatility": np.std(returns) * 100,
                "sharpe_ratio": np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0,
                "max_return": np.max(returns) * 100 if len(returns) > 0 else 0,
                "min_return": np.min(returns) * 100 if len(returns) > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {"error": str(e)}
    
    def _calculate_current_allocations(self) -> Dict[str, float]:
        """Calculate current portfolio allocations."""
        try:
            allocations = {}
            if self.total_value > 0:
                for symbol, position in self.positions.items():
                    current_value = position["quantity"] * position.get("current_price", position["avg_price"])
                    allocations[symbol] = current_value / self.total_value
            return allocations
        except Exception as e:
            logger.error(f"Error calculating current allocations: {e}")
            return {}
    
    def _record_trade(
        self, 
        symbol: str, 
        quantity: float, 
        price: float, 
        side: str, 
        action: str,
        pnl: Optional[float] = None
    ):
        """Record a trade in history."""
        try:
            trade = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "side": side,
                "action": action,
                "value": quantity * price,
                "pnl": pnl
            }
            self.trade_history.append(trade)
            
            # Keep only recent trades
            max_trades = 1000
            if len(self.trade_history) > max_trades:
                self.trade_history = self.trade_history[-max_trades:]
                
        except Exception as e:
            logger.error(f"Error recording trade: {e}")
    
    def _record_performance_snapshot(self):
        """Record current portfolio performance."""
        try:
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "total_value": self.total_value,
                "cash_balance": self.cash_balance,
                "positions_count": len(self.positions)
            }
            self.performance_history.append(snapshot)
            
            # Calculate daily return if we have previous data
            if len(self.performance_history) >= 2:
                prev_value = self.performance_history[-2]["total_value"]
                if prev_value > 0:
                    daily_return = (self.total_value - prev_value) / prev_value
                    self.daily_returns.append(daily_return)
            
            # Keep only recent performance data
            max_history = 1000
            if len(self.performance_history) > max_history:
                self.performance_history = self.performance_history[-max_history:]
                self.daily_returns = self.daily_returns[-max_history:]
                
        except Exception as e:
            logger.error(f"Error recording performance snapshot: {e}")
    
    def _save_portfolio(self):
        """Save portfolio state to file."""
        try:
            portfolio_data = {
                "positions": self.positions,
                "cash_balance": self.cash_balance,
                "total_value": self.total_value,
                "trade_history": self.trade_history[-100:],  # Save recent trades only
                "performance_history": self.performance_history[-100:],
                "daily_returns": self.daily_returns[-100:],
                "last_saved": datetime.now().isoformat()
            }
            
            with open(self.portfolio_file, 'w') as f:
                json.dump(portfolio_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving portfolio: {e}")
    
    def _load_portfolio(self):
        """Load portfolio state from file."""
        try:
            if self.portfolio_file.exists():
                with open(self.portfolio_file, 'r') as f:
                    data = json.load(f)
                
                self.positions = data.get("positions", {})
                self.cash_balance = data.get("cash_balance", self.config.initial_balance)
                self.total_value = data.get("total_value", self.config.initial_balance)
                self.trade_history = data.get("trade_history", [])
                self.performance_history = data.get("performance_history", [])
                self.daily_returns = data.get("daily_returns", [])
                
                logger.info(f"Portfolio loaded from {self.portfolio_file}")
            else:
                logger.info("No existing portfolio file found, starting fresh")
                
        except Exception as e:
            logger.error(f"Error loading portfolio: {e}")
            # Continue with default values
    
    def reset_portfolio(self):
        """Reset portfolio to initial state."""
        try:
            self.positions.clear()
            self.cash_balance = self.config.initial_balance
            self.total_value = self.config.initial_balance
            self.trade_history.clear()
            self.performance_history.clear()
            self.daily_returns.clear()
            
            self._save_portfolio()
            logger.info("Portfolio reset to initial state")
            
        except Exception as e:
            logger.error(f"Error resetting portfolio: {e}")
    
    def export_portfolio_data(self, filepath: str) -> Dict[str, Any]:
        """Export portfolio data to file."""
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "portfolio_summary": self.get_portfolio_summary(),
                "positions": self.positions,
                "trade_history": self.trade_history,
                "performance_history": self.performance_history,
                "configuration": {
                    "initial_balance": self.config.initial_balance,
                    "base_currency": self.base_currency,
                    "risk_tolerance": self.config.risk_tolerance
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return {"success": True, "message": f"Portfolio data exported to {filepath}"}
            
        except Exception as e:
            logger.error(f"Error exporting portfolio data: {e}")
            return {"success": False, "error": str(e)}
