"""Decision maker for final trading recommendations."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import numpy as np

from config.settings import MarketResearcherConfig, RISK_PARAMETERS

logger = logging.getLogger(__name__)


class DecisionMaker:
    """Makes final trading decisions based on multi-agent analysis."""
    
    def __init__(self, config: MarketResearcherConfig):
        """Initialize decision maker."""
        self.config = config
        self.risk_params = RISK_PARAMETERS
        
        # Decision weights for different agents - include trading agent
        self.agent_weights = {
            "technical": 0.25,
            "trading": 0.30,
            "sentiment": 0.15,
            "news": 0.20,
            "risk": 0.10
        }
        
        # Decision history
        self.decision_history = []
        
        logger.info("Decision maker initialized")
    
    def make_decision(
        self, 
        symbol: str, 
        agent_results: Dict[str, Dict[str, Any]],
        market_data: Dict[str, Any],
        portfolio_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make final trading decision based on agent analyses."""
        try:
            # Validate inputs
            if not self._validate_inputs(agent_results, market_data):
                return self._create_error_decision("Invalid input data")
            
            # Extract agent recommendations
            agent_recommendations = self._extract_agent_recommendations(agent_results)
            
            # Calculate weighted scores
            weighted_scores = self._calculate_weighted_scores(agent_recommendations)
            
            # Apply risk constraints
            risk_adjusted_decision = self._apply_risk_constraints(
                weighted_scores, agent_results.get("risk", {}), portfolio_context
            )
            
            # Generate position sizing
            position_details = self._calculate_position_details(
                symbol, risk_adjusted_decision, market_data, portfolio_context
            )
            
            # Create final decision
            final_decision = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "action": risk_adjusted_decision["action"],
                "confidence": risk_adjusted_decision["confidence"],
                "reasoning": risk_adjusted_decision["reasoning"],
                "agent_scores": weighted_scores,
                "agent_recommendations": agent_recommendations,
                "position_details": position_details,
                "risk_assessment": self._assess_decision_risk(risk_adjusted_decision, agent_results),
                "market_context": self._summarize_market_context(market_data)
            }
            
            # Store decision
            self._store_decision(final_decision)
            
            return final_decision
            
        except Exception as e:
            logger.error(f"Error making decision for {symbol}: {e}")
            return self._create_error_decision(str(e))
    
    def _validate_inputs(
        self, 
        agent_results: Dict[str, Dict[str, Any]], 
        market_data: Dict[str, Any]
    ) -> bool:
        """Validate input data for decision making."""
        try:
            # Check if we have at least one successful agent result
            successful_agents = [
                name for name, result in agent_results.items() 
                if result.get("success", False)
            ]
            
            if not successful_agents:
                logger.error("No successful agent results available")
                return False
            
            # Check essential market data
            required_fields = ["current_price", "symbol"]
            for field in required_fields:
                if field not in market_data:
                    logger.error(f"Missing required market data field: {field}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating inputs: {e}")
            return False
    
    def _extract_agent_recommendations(
        self, 
        agent_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Extract recommendations from each agent."""
        recommendations = {}
        
        for agent_name, result in agent_results.items():
            if not result.get("success", False):
                continue
            
            try:
                # Ensure result is a dictionary
                if not isinstance(result, dict):
                    logger.warning(f"Agent {agent_name} returned non-dict result: {type(result)}")
                    continue
                
                rec = result.get("recommendation", {})
                if not isinstance(rec, dict):
                    logger.warning(f"Agent {agent_name} recommendation is not a dict: {type(rec)}")
                    rec = {}
                
                if agent_name == "technical":
                    recommendations[agent_name] = {
                        "action": rec.get("action", "hold"),
                        "confidence": rec.get("confidence", 0.5),
                        "score": result.get("technical_score", 50),
                        "strength": rec.get("strength", "medium")
                    }
                
                elif agent_name == "sentiment":
                    recommendations[agent_name] = {
                        "action": rec.get("action", "hold"),
                        "confidence": rec.get("confidence", 0.5),
                        "score": result.get("sentiment_score", 50),
                        "rationale": rec.get("rationale", "")
                    }
                
                elif agent_name == "news":
                    recommendations[agent_name] = {
                        "action": rec.get("action", "hold"),
                        "confidence": rec.get("confidence", 0.5),
                        "score": result.get("news_score", 50),
                        "rationale": rec.get("rationale", "")
                    }
                
                elif agent_name == "risk":
                    rec = result.get("recommendation", {})
                    recommendations[agent_name] = {
                        "action": rec.get("action", "caution"),
                        "confidence": rec.get("confidence", 0.5),
                        "risk_score": result.get("risk_score", 50),
                        "position_multiplier": rec.get("position_size_multiplier", 1.0)
                    }
                
                elif agent_name == "trading":
                    # Handle simplified trading agent results
                    trading_strategy = result.get("trading_strategy", {})
                    if isinstance(trading_strategy, dict):
                        recommendations[agent_name] = {
                            "action": trading_strategy.get("recommendation", "hold").lower(),
                            "confidence": trading_strategy.get("signal_strength", 0.5),
                            "score": trading_strategy.get("signal_strength", 0.5) * 100,
                            "reasoning": trading_strategy.get("reasoning", ""),
                            "timing": trading_strategy.get("timing", ""),
                            "risk_level": trading_strategy.get("risk", {}).get("level", "medium")
                        }
                    else:
                        recommendations[agent_name] = {
                            "action": "hold",
                            "confidence": 0.5,
                            "score": 50,
                            "reasoning": "Unable to parse trading strategy"
                        }
                
            except Exception as e:
                logger.error(f"Error extracting {agent_name} recommendation: {e}")
        
        return recommendations
    
    def _calculate_weighted_scores(
        self, 
        agent_recommendations: Dict[str, Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate weighted scores from agent recommendations."""
        try:
            # Convert actions to numerical scores
            action_scores = {
                "strong_buy": 90,
                "buy": 70,
                "hold": 50,
                "sell": 30,
                "strong_sell": 10,
                "reject": 0,
                "accept": 70,
                "caution": 40,
                "favorable": 80
            }
            
            weighted_scores = {
                "technical_weighted": 0,
                "trading_weighted": 0,
                "sentiment_weighted": 0,
                "news_weighted": 0,
                "risk_weighted": 0,
                "overall_score": 0
            }
            
            total_weight = 0
            
            for agent_name, recommendation in agent_recommendations.items():
                if agent_name not in self.agent_weights:
                    continue
                
                weight = self.agent_weights[agent_name]
                
                # Get base score
                if agent_name == "risk":
                    # For risk, use inverted risk score
                    base_score = 100 - recommendation.get("risk_score", 50)
                else:
                    base_score = recommendation.get("score", 50)
                
                # Adjust by action
                action = recommendation.get("action", "hold")
                action_adjustment = action_scores.get(action, 50) - 50
                
                # Adjust by confidence
                confidence = recommendation.get("confidence", 0.5)
                adjusted_score = base_score + (action_adjustment * confidence)
                
                # Apply weight
                weighted_score = adjusted_score * weight
                weighted_scores[f"{agent_name}_weighted"] = weighted_score
                weighted_scores["overall_score"] += weighted_score
                total_weight += weight
            
            # Normalize overall score
            if total_weight > 0:
                weighted_scores["overall_score"] /= total_weight
            
            return weighted_scores
            
        except Exception as e:
            logger.error(f"Error calculating weighted scores: {e}")
            return {"overall_score": 50}
    
    def _apply_risk_constraints(
        self, 
        weighted_scores: Dict[str, float], 
        risk_result: Dict[str, Any],
        portfolio_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Apply risk management constraints to the decision."""
        try:
            overall_score = weighted_scores.get("overall_score", 50)
            
            # Base decision from score
            if overall_score >= 75:
                base_action = "strong_buy"
                base_confidence = 0.8
            elif overall_score >= 60:
                base_action = "buy"
                base_confidence = 0.7
            elif overall_score >= 40:
                base_action = "hold"
                base_confidence = 0.6
            elif overall_score >= 25:
                base_action = "sell"
                base_confidence = 0.5
            else:
                base_action = "strong_sell"
                base_confidence = 0.4
            
            # Apply risk constraints
            if risk_result.get("success", False):
                risk_recommendation = risk_result.get("recommendation", {})
                risk_action = risk_recommendation.get("action", "caution")
                
                # Risk override logic
                if risk_action == "reject":
                    return {
                        "action": "hold",
                        "confidence": 0.3,
                        "reasoning": "Position rejected due to high risk"
                    }
                elif risk_action == "reduce" and base_action in ["strong_buy", "buy"]:
                    return {
                        "action": "buy" if base_action == "strong_buy" else "hold",
                        "confidence": base_confidence * 0.7,
                        "reasoning": "Position size reduced due to risk concerns"
                    }
                elif risk_action == "caution":
                    return {
                        "action": base_action,
                        "confidence": base_confidence * 0.8,
                        "reasoning": "Proceeding with caution due to moderate risk"
                    }
            
            # Portfolio constraints
            if portfolio_context:
                portfolio_value = portfolio_context.get("total_value", self.config.initial_balance)
                available_cash = portfolio_context.get("available_cash", portfolio_value * 0.5)
                
                # Check cash availability
                if available_cash < portfolio_value * 0.1 and base_action in ["strong_buy", "buy"]:
                    return {
                        "action": "hold",
                        "confidence": 0.4,
                        "reasoning": "Insufficient cash available for new positions"
                    }
            
            return {
                "action": base_action,
                "confidence": base_confidence,
                "reasoning": f"Decision based on overall score: {overall_score:.1f}"
            }
            
        except Exception as e:
            logger.error(f"Error applying risk constraints: {e}")
            return {"action": "hold", "confidence": 0.3, "reasoning": "Risk constraint error"}
    
    def _calculate_position_details(
        self, 
        symbol: str, 
        decision: Dict[str, Any], 
        market_data: Dict[str, Any],
        portfolio_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculate specific position details."""
        try:
            current_price = market_data.get("current_price", 0)
            action = decision.get("action", "hold")
            
            if action == "hold" or current_price <= 0:
                return {
                    "position_size": 0,
                    "position_value": 0,
                    "entry_price": current_price,
                    "stop_loss": None,
                    "take_profit": None
                }
            
            # Calculate base position size
            portfolio_value = self.config.initial_balance
            if portfolio_context:
                portfolio_value = portfolio_context.get("total_value", self.config.initial_balance)
            
            # Position size based on action and confidence
            confidence = decision.get("confidence", 0.5)
            
            if action == "strong_buy":
                base_size_pct = 0.15 * confidence
            elif action == "buy":
                base_size_pct = 0.10 * confidence
            elif action == "strong_sell":
                base_size_pct = -0.15 * confidence
            elif action == "sell":
                base_size_pct = -0.10 * confidence
            else:
                base_size_pct = 0
            
            # Apply risk tolerance
            risk_adjusted_size_pct = base_size_pct * self.config.risk_tolerance / 0.02
            
            # Calculate position value and size
            position_value = abs(portfolio_value * risk_adjusted_size_pct)
            position_size = position_value / current_price if current_price > 0 else 0
            
            # Calculate stop loss and take profit
            stop_loss = None
            take_profit = None
            
            if action in ["strong_buy", "buy"]:
                # Long position
                stop_loss = current_price * (1 - self.risk_params["stop_loss_pct"])
                take_profit = current_price * (1 + self.risk_params["take_profit_pct"])
            elif action in ["strong_sell", "sell"]:
                # Short position (if supported)
                stop_loss = current_price * (1 + self.risk_params["stop_loss_pct"])
                take_profit = current_price * (1 - self.risk_params["take_profit_pct"])
            
            return {
                "position_size": position_size,
                "position_value": position_value,
                "position_side": "long" if base_size_pct > 0 else "short" if base_size_pct < 0 else "none",
                "entry_price": current_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk_amount": abs(position_value * self.risk_params["stop_loss_pct"]),
                "reward_amount": abs(position_value * self.risk_params["take_profit_pct"]),
                "risk_reward_ratio": self.risk_params["take_profit_pct"] / self.risk_params["stop_loss_pct"]
            }
            
        except Exception as e:
            logger.error(f"Error calculating position details: {e}")
            return {"position_size": 0, "error": str(e)}
    
    def _assess_decision_risk(
        self, 
        decision: Dict[str, Any], 
        agent_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess the risk level of the final decision."""
        try:
            action = decision.get("action", "hold")
            confidence = decision.get("confidence", 0.5)
            
            # Base risk assessment
            action_risk = {
                "strong_buy": 0.8,
                "buy": 0.6,
                "hold": 0.2,
                "sell": 0.6,
                "strong_sell": 0.8
            }
            
            base_risk = action_risk.get(action, 0.5)
            
            # Adjust for confidence (lower confidence = higher risk)
            confidence_adjusted_risk = base_risk * (1.1 - confidence)
            
            # Factor in agent-specific risks
            risk_factors = []
            
            # Technical risk
            if "technical" in agent_results:
                tech_result = agent_results["technical"]
                if tech_result.get("success"):
                    tech_score = tech_result.get("technical_score", 50)
                    if tech_score > 80 or tech_score < 20:
                        risk_factors.append("Extreme technical signals")
            
            # Trading agent risk
            if "trading" in agent_results:
                trading_result = agent_results["trading"]
                if trading_result.get("success"):
                    trading_strategy = trading_result.get("trading_strategy", {})
                    if isinstance(trading_strategy, dict):
                        risk_info = trading_strategy.get("risk", {})
                        if risk_info.get("level") == "high":
                            risk_factors.append("High trading signal risk")
                        signal_strength = trading_strategy.get("signal_strength", 0.5)
                        if signal_strength > 0.9 or signal_strength < 0.1:
                            risk_factors.append("Extreme trading signal strength")
            
            # Sentiment risk
            if "sentiment" in agent_results:
                sent_result = agent_results["sentiment"]
                if sent_result.get("success"):
                    sent_signals = sent_result.get("sentiment_signals", {})
                    if sent_signals.get("contrarian_signal", False):
                        risk_factors.append("Contrarian sentiment indicators")
            
            # News risk
            if "news" in agent_results:
                news_result = agent_results["news"]
                if news_result.get("success"):
                    news_signals = news_result.get("news_signals", {})
                    if news_signals.get("regulatory_risk", "low") == "high":
                        risk_factors.append("High regulatory risk")
            
            # Risk agent assessment
            if "risk" in agent_results:
                risk_result = agent_results["risk"]
                if risk_result.get("success"):
                    risk_score = risk_result.get("risk_score", 50)
                    if risk_score > 70:
                        risk_factors.append("High portfolio risk")
            
            # Final risk level
            if confidence_adjusted_risk > 0.7:
                risk_level = "high"
            elif confidence_adjusted_risk > 0.4:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            return {
                "risk_level": risk_level,
                "risk_score": confidence_adjusted_risk,
                "risk_factors": risk_factors,
                "confidence_impact": 1.1 - confidence
            }
            
        except Exception as e:
            logger.error(f"Error assessing decision risk: {e}")
            return {"risk_level": "unknown", "error": str(e)}
    
    def _summarize_market_context(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize market context for the decision."""
        try:
            return {
                "current_price": market_data.get("current_price", 0),
                "price_change_24h": market_data.get("price_change_24h", 0),
                "volume": market_data.get("volume", 0),
                "volatility": market_data.get("volatility_metrics", {}).get("volatility_24h", 0),
                "liquidity_score": market_data.get("liquidity_score", 50)
            }
        except Exception as e:
            logger.error(f"Error summarizing market context: {e}")
            return {}
    
    def _create_error_decision(self, error_message: str) -> Dict[str, Any]:
        """Create an error decision when processing fails."""
        return {
            "success": False,
            "error": error_message,
            "action": "hold",
            "confidence": 0.0,
            "reasoning": f"Decision making failed: {error_message}",
            "timestamp": datetime.now().isoformat()
        }
    
    def _store_decision(self, decision: Dict[str, Any]):
        """Store decision in history."""
        try:
            self.decision_history.append(decision)
            
            # Keep only recent history
            max_history = 100
            if len(self.decision_history) > max_history:
                self.decision_history = self.decision_history[-max_history:]
                
        except Exception as e:
            logger.error(f"Error storing decision: {e}")
    
    def get_decision_history(
        self, 
        symbol: Optional[str] = None, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get decision history, optionally filtered by symbol."""
        try:
            history = self.decision_history
            
            if symbol:
                history = [d for d in history if d.get("symbol") == symbol]
            
            return history[-limit:] if history else []
            
        except Exception as e:
            logger.error(f"Error getting decision history: {e}")
            return []
    
    def analyze_decision_performance(self, days: int = 30) -> Dict[str, Any]:
        """Analyze performance of recent decisions."""
        try:
            if not self.decision_history:
                return {"error": "No decision history available"}
            
            recent_decisions = self.decision_history[-days:] if len(self.decision_history) > days else self.decision_history
            
            # Count actions
            action_counts = {}
            confidence_sum = 0
            
            for decision in recent_decisions:
                action = decision.get("action", "hold")
                action_counts[action] = action_counts.get(action, 0) + 1
                confidence_sum += decision.get("confidence", 0)
            
            avg_confidence = confidence_sum / len(recent_decisions) if recent_decisions else 0
            
            return {
                "total_decisions": len(recent_decisions),
                "action_distribution": action_counts,
                "average_confidence": avg_confidence,
                "most_common_action": max(action_counts.items(), key=lambda x: x[1])[0] if action_counts else "none"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing decision performance: {e}")
            return {"error": str(e)}
    
    def update_agent_weights(self, new_weights: Dict[str, float]):
        """Update agent weights for decision making."""
        try:
            # Validate weights sum to 1.0
            total_weight = sum(new_weights.values())
            if abs(total_weight - 1.0) > 0.01:
                logger.warning(f"Agent weights sum to {total_weight}, normalizing...")
                new_weights = {k: v/total_weight for k, v in new_weights.items()}
            
            # Update weights
            for agent, weight in new_weights.items():
                if agent in self.agent_weights:
                    self.agent_weights[agent] = weight
            
            logger.info(f"Updated agent weights: {self.agent_weights}")
            
        except Exception as e:
            logger.error(f"Error updating agent weights: {e}")
    
    def get_decision_summary(self) -> Dict[str, Any]:
        """Get summary of decision maker status."""
        try:
            return {
                "total_decisions": len(self.decision_history),
                "agent_weights": self.agent_weights,
                "risk_parameters": self.risk_params,
                "last_decision": self.decision_history[-1].get("timestamp") if self.decision_history else None
            }
        except Exception as e:
            logger.error(f"Error getting decision summary: {e}")
            return {"error": str(e)}
