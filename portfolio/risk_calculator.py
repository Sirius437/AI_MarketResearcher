"""Risk calculation utilities for portfolio management."""

import logging
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from config.settings import MarketResearcherConfig, RISK_PARAMETERS

logger = logging.getLogger(__name__)


class RiskCalculator:
    """Calculate various risk metrics for cryptocurrency portfolio."""
    
    def __init__(self, config: MarketResearcherConfig):
        """Initialize risk calculator."""
        self.config = config
        self.risk_params = RISK_PARAMETERS
        
    def calculate_position_size(
        self, 
        symbol: str,
        entry_price: float,
        stop_loss: float,
        portfolio_value: float,
        available_cash: float,
        risk_per_trade: Optional[float] = None
    ) -> Dict[str, Any]:
        """Calculate optimal position size based on risk parameters."""
        try:
            if risk_per_trade is None:
                risk_per_trade = self.config.risk_tolerance
            
            # Validate inputs
            if entry_price <= 0 or stop_loss <= 0 or portfolio_value <= 0:
                return {"error": "Invalid input parameters"}
            
            # Calculate risk per unit
            risk_per_unit = abs(entry_price - stop_loss)
            if risk_per_unit <= 0:
                return {"error": "Stop loss must be different from entry price"}
            
            # Calculate maximum risk amount
            max_risk_amount = portfolio_value * risk_per_trade
            
            # Calculate position size based on risk
            risk_based_size = max_risk_amount / risk_per_unit
            risk_based_value = risk_based_size * entry_price
            
            # Apply position size constraints
            max_position_value = portfolio_value * self.config.max_position_size
            max_position_size = max_position_value / entry_price
            
            # Apply cash constraints
            cash_based_size = available_cash / entry_price
            
            # Use the most restrictive constraint
            final_position_size = min(risk_based_size, max_position_size, cash_based_size)
            final_position_value = final_position_size * entry_price
            
            # Calculate actual risk
            actual_risk_amount = final_position_size * risk_per_unit
            actual_risk_percentage = actual_risk_amount / portfolio_value if portfolio_value > 0 else 0
            
            # Calculate risk/reward ratio
            if entry_price != stop_loss:
                # Assume take profit at 2x risk distance
                take_profit = entry_price + (2 * (entry_price - stop_loss)) if entry_price > stop_loss else entry_price - (2 * (stop_loss - entry_price))
                reward_per_unit = abs(take_profit - entry_price)
                risk_reward_ratio = reward_per_unit / risk_per_unit if risk_per_unit > 0 else 0
            else:
                risk_reward_ratio = 0
            
            return {
                "symbol": symbol,
                "recommended_position_size": final_position_size,
                "position_value": final_position_value,
                "position_percentage": (final_position_value / portfolio_value) * 100,
                "risk_amount": actual_risk_amount,
                "risk_percentage": actual_risk_percentage * 100,
                "risk_reward_ratio": risk_reward_ratio,
                "constraints_applied": {
                    "risk_based": risk_based_size,
                    "max_position": max_position_size,
                    "cash_available": cash_based_size,
                    "limiting_factor": self._get_limiting_factor(risk_based_size, max_position_size, cash_based_size)
                },
                "entry_price": entry_price,
                "stop_loss": stop_loss
            }
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return {"error": str(e)}
    
    def calculate_portfolio_risk(
        self, 
        positions: Dict[str, Dict[str, Any]],
        total_value: float,
        daily_returns: List[float],
        correlation_matrix: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """Calculate comprehensive portfolio risk metrics."""
        try:
            if not positions:
                return {"error": "No positions in portfolio"}
            
            # Basic portfolio metrics
            position_count = len(positions)
            total_invested = sum(
                pos["quantity"] * pos.get("current_price", pos["avg_price"])
                for pos in positions.values()
            )
            
            # Concentration risk
            concentration_risk = self._calculate_concentration_risk(positions, total_value)
            
            # Volatility metrics
            volatility_metrics = self._calculate_volatility_metrics(daily_returns)
            
            # Value at Risk (VaR)
            var_metrics = self._calculate_var(daily_returns, total_value)
            
            # Drawdown metrics
            drawdown_metrics = self._calculate_drawdown_risk(daily_returns)
            
            # Liquidity risk
            liquidity_risk = self._assess_liquidity_risk(positions)
            
            # Overall risk score
            overall_risk_score = self._calculate_overall_risk_score(
                concentration_risk, volatility_metrics, var_metrics, liquidity_risk
            )
            
            return {
                "portfolio_value": total_value,
                "positions_count": position_count,
                "concentration_risk": concentration_risk,
                "volatility_metrics": volatility_metrics,
                "var_metrics": var_metrics,
                "drawdown_metrics": drawdown_metrics,
                "liquidity_risk": liquidity_risk,
                "overall_risk_score": overall_risk_score,
                "risk_level": self._categorize_risk_level(overall_risk_score),
                "recommendations": self._generate_risk_recommendations(overall_risk_score, concentration_risk)
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio risk: {e}")
            return {"error": str(e)}
    
    def calculate_correlation_risk(
        self, 
        positions: Dict[str, Dict[str, Any]],
        price_data: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """Calculate correlation risk between portfolio positions."""
        try:
            if len(positions) < 2:
                return {"correlation_risk": "low", "message": "Insufficient positions for correlation analysis"}
            
            symbols = list(positions.keys())
            correlations = {}
            
            # Calculate pairwise correlations
            for i, symbol1 in enumerate(symbols):
                for j, symbol2 in enumerate(symbols[i+1:], i+1):
                    if symbol1 in price_data and symbol2 in price_data:
                        prices1 = np.array(price_data[symbol1])
                        prices2 = np.array(price_data[symbol2])
                        
                        if len(prices1) > 1 and len(prices2) > 1:
                            returns1 = np.diff(prices1) / prices1[:-1]
                            returns2 = np.diff(prices2) / prices2[:-1]
                            
                            if len(returns1) == len(returns2):
                                correlation = np.corrcoef(returns1, returns2)[0, 1]
                                correlations[f"{symbol1}-{symbol2}"] = correlation
            
            if not correlations:
                return {"correlation_risk": "unknown", "message": "Unable to calculate correlations"}
            
            # Analyze correlation risk
            avg_correlation = np.mean(list(correlations.values()))
            max_correlation = max(correlations.values())
            high_correlations = [pair for pair, corr in correlations.items() if abs(corr) > 0.7]
            
            # Determine risk level
            if max_correlation > 0.8:
                risk_level = "high"
            elif avg_correlation > 0.6:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            return {
                "correlation_risk": risk_level,
                "average_correlation": avg_correlation,
                "maximum_correlation": max_correlation,
                "high_correlation_pairs": high_correlations,
                "all_correlations": correlations,
                "diversification_score": 1 - avg_correlation  # Higher is better
            }
            
        except Exception as e:
            logger.error(f"Error calculating correlation risk: {e}")
            return {"error": str(e)}
    
    def calculate_kelly_criterion(
        self, 
        win_rate: float, 
        avg_win: float, 
        avg_loss: float
    ) -> Dict[str, Any]:
        """Calculate optimal position size using Kelly Criterion."""
        try:
            if avg_loss <= 0:
                return {"error": "Average loss must be positive"}
            
            # Kelly formula: f = (bp - q) / b
            # where b = avg_win/avg_loss, p = win_rate, q = 1 - win_rate
            b = avg_win / avg_loss
            p = win_rate
            q = 1 - win_rate
            
            kelly_fraction = (b * p - q) / b
            
            # Apply fractional Kelly to reduce risk
            conservative_kelly = kelly_fraction * 0.25  # 25% of full Kelly
            
            # Ensure reasonable bounds
            recommended_fraction = max(0, min(conservative_kelly, 0.2))  # Cap at 20%
            
            return {
                "kelly_fraction": kelly_fraction,
                "conservative_kelly": conservative_kelly,
                "recommended_fraction": recommended_fraction,
                "win_rate": win_rate,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "win_loss_ratio": b
            }
            
        except Exception as e:
            logger.error(f"Error calculating Kelly criterion: {e}")
            return {"error": str(e)}
    
    def _calculate_concentration_risk(
        self, 
        positions: Dict[str, Dict[str, Any]], 
        total_value: float
    ) -> Dict[str, Any]:
        """Calculate portfolio concentration risk."""
        try:
            if total_value <= 0:
                return {"risk_level": "unknown"}
            
            # Calculate position weights
            weights = []
            for position in positions.values():
                position_value = position["quantity"] * position.get("current_price", position["avg_price"])
                weight = position_value / total_value
                weights.append(weight)
            
            # Herfindahl-Hirschman Index (HHI)
            hhi = sum(w**2 for w in weights)
            
            # Largest position weight
            max_weight = max(weights) if weights else 0
            
            # Determine risk level
            if max_weight > 0.5 or hhi > 0.4:
                risk_level = "high"
            elif max_weight > 0.3 or hhi > 0.25:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            return {
                "risk_level": risk_level,
                "hhi_index": hhi,
                "max_position_weight": max_weight,
                "position_weights": weights,
                "effective_positions": 1 / hhi if hhi > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating concentration risk: {e}")
            return {"risk_level": "unknown"}
    
    def _calculate_volatility_metrics(self, daily_returns: List[float]) -> Dict[str, Any]:
        """Calculate volatility-based risk metrics."""
        try:
            if not daily_returns or len(daily_returns) < 2:
                return {"volatility": 0, "risk_level": "unknown"}
            
            returns = np.array(daily_returns)
            
            # Basic volatility metrics
            daily_vol = np.std(returns)
            annualized_vol = daily_vol * np.sqrt(252)  # Assuming 252 trading days
            
            # Downside deviation (volatility of negative returns only)
            negative_returns = returns[returns < 0]
            downside_deviation = np.std(negative_returns) if len(negative_returns) > 0 else 0
            
            # Determine risk level based on annualized volatility
            if annualized_vol > 1.0:  # 100%+ annual volatility
                risk_level = "very_high"
            elif annualized_vol > 0.6:  # 60%+ annual volatility
                risk_level = "high"
            elif annualized_vol > 0.3:  # 30%+ annual volatility
                risk_level = "medium"
            else:
                risk_level = "low"
            
            return {
                "daily_volatility": daily_vol,
                "annualized_volatility": annualized_vol,
                "downside_deviation": downside_deviation,
                "risk_level": risk_level,
                "volatility_percentile": self._calculate_percentile(annualized_vol, [0.1, 0.3, 0.6, 1.0])
            }
            
        except Exception as e:
            logger.error(f"Error calculating volatility metrics: {e}")
            return {"volatility": 0, "risk_level": "unknown"}
    
    def _calculate_var(self, daily_returns: List[float], portfolio_value: float) -> Dict[str, Any]:
        """Calculate Value at Risk (VaR) metrics."""
        try:
            if not daily_returns or len(daily_returns) < 10:
                return {"var_95": 0, "var_99": 0}
            
            returns = np.array(daily_returns)
            
            # Historical VaR
            var_95 = np.percentile(returns, 5)  # 95% confidence
            var_99 = np.percentile(returns, 1)  # 99% confidence
            
            # Convert to dollar amounts
            var_95_dollar = abs(var_95 * portfolio_value)
            var_99_dollar = abs(var_99 * portfolio_value)
            
            # Expected Shortfall (Conditional VaR)
            es_95 = np.mean(returns[returns <= var_95]) if np.any(returns <= var_95) else var_95
            es_99 = np.mean(returns[returns <= var_99]) if np.any(returns <= var_99) else var_99
            
            return {
                "var_95_pct": var_95,
                "var_99_pct": var_99,
                "var_95_dollar": var_95_dollar,
                "var_99_dollar": var_99_dollar,
                "expected_shortfall_95": es_95,
                "expected_shortfall_99": es_99,
                "risk_level": "high" if var_95 < -0.1 else "medium" if var_95 < -0.05 else "low"
            }
            
        except Exception as e:
            logger.error(f"Error calculating VaR: {e}")
            return {"var_95": 0, "var_99": 0}
    
    def _calculate_drawdown_risk(self, daily_returns: List[float]) -> Dict[str, Any]:
        """Calculate drawdown risk metrics."""
        try:
            if not daily_returns:
                return {"max_drawdown": 0}
            
            # Calculate cumulative returns
            cumulative_returns = np.cumprod(1 + np.array(daily_returns))
            
            # Calculate drawdowns
            peak = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - peak) / peak
            
            max_drawdown = np.min(drawdown)
            current_drawdown = drawdown[-1] if len(drawdown) > 0 else 0
            
            # Calculate drawdown duration
            in_drawdown = drawdown < -0.01  # More than 1% drawdown
            if np.any(in_drawdown):
                # Find longest consecutive drawdown period
                drawdown_periods = []
                current_period = 0
                for is_dd in in_drawdown:
                    if is_dd:
                        current_period += 1
                    else:
                        if current_period > 0:
                            drawdown_periods.append(current_period)
                        current_period = 0
                if current_period > 0:
                    drawdown_periods.append(current_period)
                
                max_drawdown_duration = max(drawdown_periods) if drawdown_periods else 0
            else:
                max_drawdown_duration = 0
            
            # Risk level based on max drawdown
            if max_drawdown < -0.3:  # 30%+ drawdown
                risk_level = "high"
            elif max_drawdown < -0.15:  # 15%+ drawdown
                risk_level = "medium"
            else:
                risk_level = "low"
            
            return {
                "max_drawdown": max_drawdown,
                "current_drawdown": current_drawdown,
                "max_drawdown_duration": max_drawdown_duration,
                "risk_level": risk_level,
                "recovery_factor": abs(cumulative_returns[-1] - 1) / abs(max_drawdown) if max_drawdown < 0 else float('inf')
            }
            
        except Exception as e:
            logger.error(f"Error calculating drawdown risk: {e}")
            return {"max_drawdown": 0}
    
    def _assess_liquidity_risk(self, positions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Assess liquidity risk of portfolio positions."""
        try:
            if not positions:
                return {"risk_level": "unknown"}
            
            # This is a simplified liquidity assessment
            # In practice, you'd want to integrate with exchange data
            
            position_sizes = []
            for position in positions.values():
                position_value = position["quantity"] * position.get("current_price", position["avg_price"])
                position_sizes.append(position_value)
            
            avg_position_size = np.mean(position_sizes)
            
            # Simple heuristic: larger positions in crypto are generally less liquid
            if avg_position_size > 100000:  # $100k+ average position
                risk_level = "high"
            elif avg_position_size > 10000:  # $10k+ average position
                risk_level = "medium"
            else:
                risk_level = "low"
            
            return {
                "risk_level": risk_level,
                "average_position_size": avg_position_size,
                "largest_position": max(position_sizes) if position_sizes else 0,
                "liquidity_score": max(0, min(100, 100 - (avg_position_size / 1000)))  # Inverse relationship
            }
            
        except Exception as e:
            logger.error(f"Error assessing liquidity risk: {e}")
            return {"risk_level": "unknown"}
    
    def _calculate_overall_risk_score(
        self, 
        concentration_risk: Dict[str, Any],
        volatility_metrics: Dict[str, Any],
        var_metrics: Dict[str, Any],
        liquidity_risk: Dict[str, Any]
    ) -> float:
        """Calculate overall portfolio risk score (0-100)."""
        try:
            score = 0
            
            # Concentration risk (0-30 points)
            conc_risk = concentration_risk.get("risk_level", "medium")
            conc_scores = {"low": 5, "medium": 15, "high": 30}
            score += conc_scores.get(conc_risk, 15)
            
            # Volatility risk (0-25 points)
            vol_risk = volatility_metrics.get("risk_level", "medium")
            vol_scores = {"low": 5, "medium": 12, "high": 20, "very_high": 25}
            score += vol_scores.get(vol_risk, 12)
            
            # VaR risk (0-25 points)
            var_risk = var_metrics.get("risk_level", "medium")
            var_scores = {"low": 5, "medium": 12, "high": 25}
            score += var_scores.get(var_risk, 12)
            
            # Liquidity risk (0-20 points)
            liq_risk = liquidity_risk.get("risk_level", "medium")
            liq_scores = {"low": 3, "medium": 10, "high": 20}
            score += liq_scores.get(liq_risk, 10)
            
            return min(100, max(0, score))
            
        except Exception as e:
            logger.error(f"Error calculating overall risk score: {e}")
            return 50.0
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categorize risk level based on score."""
        if risk_score >= 70:
            return "high"
        elif risk_score >= 40:
            return "medium"
        else:
            return "low"
    
    def _generate_risk_recommendations(
        self, 
        risk_score: float, 
        concentration_risk: Dict[str, Any]
    ) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []
        
        try:
            if risk_score >= 70:
                recommendations.append("Consider reducing overall portfolio risk")
                recommendations.append("Implement stricter stop-loss orders")
            
            if concentration_risk.get("risk_level") == "high":
                recommendations.append("Diversify portfolio to reduce concentration risk")
                recommendations.append("Consider reducing largest position sizes")
            
            if concentration_risk.get("max_position_weight", 0) > 0.3:
                recommendations.append("No single position should exceed 30% of portfolio")
            
            recommendations.append("Review and update risk management rules regularly")
            recommendations.append("Monitor correlation between positions")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating risk recommendations: {e}")
            return ["Unable to generate recommendations"]
    
    def _get_limiting_factor(self, risk_based: float, max_position: float, cash_available: float) -> str:
        """Determine which constraint is most limiting."""
        min_size = min(risk_based, max_position, cash_available)
        
        if min_size == cash_available:
            return "cash_available"
        elif min_size == max_position:
            return "max_position_size"
        else:
            return "risk_management"
    
    def _calculate_percentile(self, value: float, thresholds: List[float]) -> int:
        """Calculate which percentile a value falls into."""
        for i, threshold in enumerate(thresholds):
            if value <= threshold:
                return (i + 1) * 25  # 25th, 50th, 75th, 100th percentile
        return 100
