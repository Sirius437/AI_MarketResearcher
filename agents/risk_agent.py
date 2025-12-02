"""Risk assessment agent for cryptocurrency trading."""

import logging
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from datetime import datetime

from .base_agent import BaseAgent
from config.settings import MarketResearcherConfig, RISK_PARAMETERS

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    """Agent specialized in risk management and portfolio assessment."""
    
    def __init__(self, llm_client, prompt_manager, config: MarketResearcherConfig):
        """Initialize risk analysis agent."""
        super().__init__(llm_client, prompt_manager, config, "Risk Analyst")
        self.risk_params = RISK_PARAMETERS
        
    def get_agent_type(self) -> str:
        """Return the agent type identifier."""
        return "risk"
    
    def analyze(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform risk analysis for the given symbol and position."""
        try:
            if not self._validate_analysis_data(data):
                return {
                    "success": False,
                    "error": "Invalid input data",
                    "agent": self.agent_name
                }
            
            # Extract position and portfolio data
            position_data = self._extract_position_data(data)
            portfolio_data = self._extract_portfolio_data(data)
            
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(symbol, position_data, portfolio_data)
            
            # Assess portfolio impact
            portfolio_impact = self._assess_portfolio_impact(position_data, portfolio_data)
            
            # Create analysis prompt
            messages = self.prompt_manager.create_risk_assessment_prompt(
                symbol=symbol,
                position_data=position_data,
                portfolio_data={**portfolio_data, **portfolio_impact, **risk_metrics}
            )
            
            # Execute LLM analysis
            llm_result = self._execute_llm_analysis(messages)
            
            if llm_result["success"]:
                # Use raw LLM response content for analysis
                raw_content = llm_result["raw_response"]
                
                # Extract risk signals from raw content
                risk_signals = self._extract_risk_signals(raw_content)
                
                # Calculate overall risk score
                risk_score = self._calculate_risk_score(risk_signals, position_data)
                
                # Extract confidence score from raw content
                confidence = self._extract_confidence_score(raw_content)
                
                analysis_result = {
                    "success": True,
                    "agent": self.agent_name,
                    "symbol": symbol,
                    "analysis": raw_content,
                    "summary": raw_content[:300] + "..." if len(raw_content) > 300 else raw_content,
                    "risk_signals": risk_signals,
                    "risk_score": risk_score,
                    "confidence": confidence,
                    # Remove recommendation - Trading Agent handles all trading decisions
                    "timestamp": llm_result["timestamp"]
                }
                
                # Store analysis
                self._store_analysis(analysis_result)
                
                return analysis_result
            else:
                return llm_result
                
        except Exception as e:
            logger.error(f"Error in risk analysis for {symbol}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.agent_name,
                "symbol": symbol
            }
    
    def _extract_position_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract position-related data from input."""
        try:
            position_data = {
                "action": data.get("action", "hold"),
                "position_size": data.get("position_size", 0),
                "entry_price": data.get("entry_price", data.get("current_price", 0)),
                "stop_loss": data.get("stop_loss", 0),
                "take_profit": data.get("take_profit", 0),
                "current_price": data.get("current_price", data.get("price", 0)),
                "volatility": data.get("volatility", data.get("volatility_30d", 0)),
                "btc_correlation": data.get("btc_correlation", 0),
                "liquidity_score": data.get("liquidity_score", 50),
                "market_cap": data.get("market_cap", 0)
            }
            
            # Calculate position value
            if position_data["position_size"] and position_data["current_price"]:
                position_data["position_value"] = position_data["position_size"] * position_data["current_price"]
            else:
                position_data["position_value"] = 0
            
            return position_data
            
        except Exception as e:
            logger.error(f"Error extracting position data: {e}")
            return {"action": "hold", "position_size": 0}
    
    def _extract_portfolio_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract portfolio-related data from input."""
        try:
            portfolio_data = {
                "total_value": data.get("portfolio_value", self.config.initial_balance),
                "available_cash": data.get("available_cash", self.config.initial_balance * 0.2),
                "existing_positions": data.get("existing_positions", []),
                "beta": data.get("portfolio_beta", 1.0)
            }
            
            # Calculate portfolio utilization
            if portfolio_data["total_value"] > 0:
                utilized_value = portfolio_data["total_value"] - portfolio_data["available_cash"]
                portfolio_data["utilization_ratio"] = utilized_value / portfolio_data["total_value"]
            else:
                portfolio_data["utilization_ratio"] = 0
            
            return portfolio_data
            
        except Exception as e:
            logger.error(f"Error extracting portfolio data: {e}")
            return {"total_value": self.config.initial_balance}
    
    def _calculate_risk_metrics(
        self, 
        symbol: str, 
        position_data: Dict[str, Any], 
        portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics."""
        try:
            metrics = {}
            
            # Position size risk
            position_value = position_data.get("position_value", 0)
            portfolio_value = portfolio_data.get("total_value", 1)
            
            if portfolio_value > 0:
                metrics["position_size_ratio"] = position_value / portfolio_value
            else:
                metrics["position_size_ratio"] = 0
            
            # Volatility risk
            volatility = position_data.get("volatility", 0)
            if volatility > 0.5:
                metrics["volatility_risk"] = "high"
            elif volatility > 0.3:
                metrics["volatility_risk"] = "medium"
            else:
                metrics["volatility_risk"] = "low"
            
            # Liquidity risk
            liquidity_score = position_data.get("liquidity_score", 50)
            if liquidity_score < 30:
                metrics["liquidity_risk"] = "high"
            elif liquidity_score < 60:
                metrics["liquidity_risk"] = "medium"
            else:
                metrics["liquidity_risk"] = "low"
            
            # Correlation risk
            btc_correlation = abs(position_data.get("btc_correlation", 0))
            if btc_correlation > 0.8:
                metrics["correlation_risk"] = "high"
            elif btc_correlation > 0.6:
                metrics["correlation_risk"] = "medium"
            else:
                metrics["correlation_risk"] = "low"
            
            # Stop loss risk
            entry_price = position_data.get("entry_price", 0)
            stop_loss = position_data.get("stop_loss", 0)
            
            if entry_price > 0 and stop_loss > 0:
                stop_loss_distance = abs(entry_price - stop_loss) / entry_price
                metrics["stop_loss_distance"] = stop_loss_distance
                
                if stop_loss_distance > 0.1:
                    metrics["stop_loss_risk"] = "high"
                elif stop_loss_distance > 0.05:
                    metrics["stop_loss_risk"] = "medium"
                else:
                    metrics["stop_loss_risk"] = "low"
            else:
                metrics["stop_loss_risk"] = "very_high"  # No stop loss
            
            # Risk/Reward ratio
            take_profit = position_data.get("take_profit", 0)
            if entry_price > 0 and stop_loss > 0 and take_profit > 0:
                risk = abs(entry_price - stop_loss)
                reward = abs(take_profit - entry_price)
                if risk > 0:
                    metrics["risk_reward_ratio"] = reward / risk
                else:
                    metrics["risk_reward_ratio"] = 0
            else:
                metrics["risk_reward_ratio"] = 0
            
            # Portfolio concentration risk
            existing_positions = portfolio_data.get("existing_positions", [])
            if len(existing_positions) < 3:
                metrics["concentration_risk"] = "high"
            elif len(existing_positions) < 6:
                metrics["concentration_risk"] = "medium"
            else:
                metrics["concentration_risk"] = "low"
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {"volatility_risk": "unknown"}
    
    def _assess_portfolio_impact(
        self, 
        position_data: Dict[str, Any], 
        portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess the impact of the position on the overall portfolio."""
        try:
            impact = {}
            
            position_value = position_data.get("position_value", 0)
            portfolio_value = portfolio_data.get("total_value", 1)
            
            # Portfolio weight impact
            if portfolio_value > 0:
                new_weight = position_value / portfolio_value
                impact["portfolio_weight"] = new_weight
                
                if new_weight > self.config.max_position_size:
                    impact["weight_warning"] = f"Position exceeds maximum size ({self.config.max_position_size:.1%})"
                
            # Diversification impact
            existing_positions = portfolio_data.get("existing_positions", [])
            impact["diversification_level"] = len(existing_positions)
            
            # Cash utilization
            available_cash = portfolio_data.get("available_cash", 0)
            if position_value > available_cash:
                impact["cash_warning"] = "Insufficient cash for position"
            
            # Portfolio beta impact
            position_beta = 1.0  # Assume crypto positions have beta of 1
            portfolio_beta = portfolio_data.get("beta", 1.0)
            
            if portfolio_value > 0:
                new_portfolio_beta = ((portfolio_value - position_value) * portfolio_beta + 
                                    position_value * position_beta) / portfolio_value
                impact["new_portfolio_beta"] = new_portfolio_beta
            
            return impact
            
        except Exception as e:
            logger.error(f"Error assessing portfolio impact: {e}")
            return {}
    
    def _extract_risk_signals(self, analysis: str) -> Dict[str, Any]:
        """Extract risk signals from LLM analysis."""
        try:
            full_text = analysis.lower() if isinstance(analysis, str) else str(analysis).lower()
            
            signals = {
                "risk_level": "medium",
                "position_sizing": "appropriate",
                "risk_factors": [],
                "mitigation_needed": False
            }
            
            # Extract risk level
            if any(phrase in full_text for phrase in ["very high", "extremely high"]):
                signals["risk_level"] = "very_high"
            elif "high" in full_text and "risk" in full_text:
                signals["risk_level"] = "high"
            elif "low" in full_text and "risk" in full_text:
                signals["risk_level"] = "low"
            elif any(phrase in full_text for phrase in ["very low", "minimal"]):
                signals["risk_level"] = "very_low"
            
            # Extract position sizing recommendation
            if any(phrase in full_text for phrase in ["reduce position", "smaller position"]):
                signals["position_sizing"] = "reduce"
            elif any(phrase in full_text for phrase in ["increase position", "larger position"]):
                signals["position_sizing"] = "increase"
            elif any(phrase in full_text for phrase in ["avoid", "do not"]):
                signals["position_sizing"] = "avoid"
            
            # Check for mitigation needs
            mitigation_keywords = ["mitigation", "hedge", "reduce risk", "stop loss", "diversify"]
            if any(keyword in full_text for keyword in mitigation_keywords):
                signals["mitigation_needed"] = True
            
            return signals
            
        except Exception as e:
            logger.error(f"Error extracting risk signals: {e}")
            return {"risk_level": "medium"}
    
    def _calculate_risk_score(
        self, 
        risk_metrics: Dict[str, Any], 
        risk_signals: Dict[str, Any]
    ) -> float:
        """Calculate overall risk score (0-100, higher = more risky)."""
        try:
            score = 30  # Low risk starting point
            
            # Position size risk
            position_ratio = risk_metrics.get("position_size_ratio", 0)
            if position_ratio > 0.2:
                score += 25
            elif position_ratio > 0.1:
                score += 15
            elif position_ratio > 0.05:
                score += 10
            
            # Volatility risk
            vol_risk = risk_metrics.get("volatility_risk", "low")
            vol_scores = {"high": 20, "medium": 10, "low": 0}
            score += vol_scores.get(vol_risk, 10)
            
            # Liquidity risk
            liq_risk = risk_metrics.get("liquidity_risk", "low")
            liq_scores = {"high": 15, "medium": 8, "low": 0}
            score += liq_scores.get(liq_risk, 8)
            
            # Stop loss risk
            sl_risk = risk_metrics.get("stop_loss_risk", "medium")
            sl_scores = {"very_high": 25, "high": 15, "medium": 5, "low": 0}
            score += sl_scores.get(sl_risk, 10)
            
            # Risk/Reward ratio
            rr_ratio = risk_metrics.get("risk_reward_ratio", 0)
            if rr_ratio < 1:
                score += 15  # Poor risk/reward
            elif rr_ratio < 2:
                score += 5
            else:
                score -= 5   # Good risk/reward
            
            # Concentration risk
            conc_risk = risk_metrics.get("concentration_risk", "medium")
            conc_scores = {"high": 15, "medium": 8, "low": 0}
            score += conc_scores.get(conc_risk, 8)
            
            # LLM risk assessment
            llm_risk = risk_signals.get("risk_level", "medium")
            llm_scores = {"very_high": 20, "high": 15, "medium": 5, "low": 0, "very_low": -5}
            score += llm_scores.get(llm_risk, 5)
            
            # Ensure score is within bounds
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 50  # Default medium risk
    
    def calculate_position_size(
        self, 
        symbol: str, 
        entry_price: float, 
        stop_loss: float, 
        portfolio_value: float,
        risk_per_trade: float = None
    ) -> Dict[str, Any]:
        """Calculate optimal position size based on risk parameters."""
        try:
            if risk_per_trade is None:
                risk_per_trade = self.config.risk_tolerance
            
            if entry_price <= 0 or stop_loss <= 0 or portfolio_value <= 0:
                return {"error": "Invalid input parameters"}
            
            # Calculate risk per unit
            risk_per_unit = abs(entry_price - stop_loss)
            
            # Calculate maximum risk amount
            max_risk_amount = portfolio_value * risk_per_trade
            
            # Calculate position size
            position_size = max_risk_amount / risk_per_unit
            
            # Apply maximum position size constraint
            max_position_value = portfolio_value * self.config.max_position_size
            max_position_size = max_position_value / entry_price
            
            # Use the smaller of the two
            final_position_size = min(position_size, max_position_size)
            
            return {
                "recommended_position_size": final_position_size,
                "position_value": final_position_size * entry_price,
                "risk_amount": final_position_size * risk_per_unit,
                "risk_percentage": (final_position_size * risk_per_unit) / portfolio_value,
                "position_percentage": (final_position_size * entry_price) / portfolio_value,
                "method": "risk_based_sizing"
            }
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return {"error": str(e)}
    
    def _store_analysis(self, analysis_result: Dict[str, Any]):
        """Store analysis result in history."""
        try:
            self.last_analysis = analysis_result
            self.analysis_history.append(analysis_result)
            self.confidence_scores.append(analysis_result.get("confidence", 0.5))
            
            # Keep only recent history
            max_history = 50
            if len(self.analysis_history) > max_history:
                self.analysis_history = self.analysis_history[-max_history:]
                self.confidence_scores = self.confidence_scores[-max_history:]
                
        except Exception as e:
            logger.error(f"Error storing analysis: {e}")
    
    def get_risk_summary(self, symbol: str) -> Dict[str, Any]:
        """Get summary of recent risk analysis."""
        try:
            if not self.last_analysis:
                return {"error": "No recent analysis available"}
            
            return {
                "symbol": symbol,
                "last_analysis": self.last_analysis.get("timestamp"),
                "risk_score": self.last_analysis.get("risk_score", 0),
                # Remove recommendation reference - Trading Agent handles all trading decisions
                "key_risks": {
                    "risk_level": self.last_analysis.get("risk_signals", {}).get("risk_level"),
                    "volatility_risk": self.last_analysis.get("risk_metrics", {}).get("volatility_risk"),
                    "liquidity_risk": self.last_analysis.get("risk_metrics", {}).get("liquidity_risk"),
                    "stop_loss_risk": self.last_analysis.get("risk_metrics", {}).get("stop_loss_risk")
                },
                "confidence": self.last_analysis.get("confidence", 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting risk summary: {e}")
            return {"error": str(e)}
