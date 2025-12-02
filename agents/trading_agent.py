"""Trading agent for position management and risk analysis."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import re

from agents.base_agent import BaseAgent
from llm.local_client import LocalLLMClient
from llm.prompt_manager import PromptManager
from config.settings import MarketResearcherConfig
from analyzers.signal_generator import UnifiedSignalGenerator, SignalResult
from analyzers.algo_insights import AlgorithmicInsightsAnalyzer

logger = logging.getLogger(__name__)


class TradingAgent(BaseAgent):
    """Agent specialized in trading position analysis and risk management."""
    
    def __init__(self, llm_client: Optional[LocalLLMClient] = None, prompt_manager: Optional[PromptManager] = None, config: Optional[MarketResearcherConfig] = None):
        """Initialize trading agent with optional LLM dependencies for web mode."""
        if llm_client and prompt_manager and config:
            # Full initialization for CLI mode
            super().__init__(llm_client, prompt_manager, config, "Trading Agent")
        else:
            # Simplified initialization for web mode
            self.agent_name = "Trading Agent"
            self.llm_client = None
            self.prompt_manager = None
            self.config = None
            
        self.agent_type = "trading"
        self.signal_generator = UnifiedSignalGenerator()
        self.algo_insights = AlgorithmicInsightsAnalyzer()
    
    def get_agent_type(self) -> str:
        """Return the agent type identifier."""
        return self.agent_type
    
    def analyze(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trading position and risk management parameters."""
        try:
            logger.info(f"Starting trading analysis for {symbol}")
            
            # Validate input data
            if not self._validate_analysis_data(data):
                return {
                    "success": False,
                    "error": "Invalid analysis data provided",
                    "agent": self.agent_name
                }
            
            # Extract market data
            current_price = data.get("current_price", 0)
            price_change_24h = data.get("price_change_24h", 0)
            volatility = data.get("volatility_metrics", {}).get("volatility_30d", 0.02)
            volume = data.get("volume", 0)
            
            # Generate unified signal first
            unified_signal = self._generate_unified_signal(symbol, data)
            
            # Enhance signal with algorithmic insights
            enhanced_signal = self._enhance_signal_with_algo_insights(unified_signal, data)
            
            # Use position management from enhanced signal
            position_analysis = {
                "portfolio_exposure": enhanced_signal.get("position_size_pct", unified_signal.position_size_pct),
                "profit_target": enhanced_signal.get("profit_target", unified_signal.profit_target),
                "stop_loss": enhanced_signal.get("stop_loss", unified_signal.stop_loss),
                "risk_reward_ratio": self._calculate_risk_reward_ratio(unified_signal),
                "position_direction": self._convert_unified_to_position_direction(unified_signal),
                "recommended_algorithm": enhanced_signal.get("recommended_algorithm", "VWAP"),
                "execution_insights": enhanced_signal.get("execution_insights", {}),
                "algo_confidence": enhanced_signal.get("algo_confidence", 0.5)
            }
            
            # Extract position direction from analysis
            position_direction = position_analysis["position_direction"]
            
            # Detect asset type from symbol
            asset_type = self._detect_asset_type(symbol)
            
            # Calculate risk parameters
            risk_parameters = self._calculate_risk_parameters(
                current_price, volatility, position_direction, asset_type
            )
            
            # Generate trading strategy based on unified signals only
            trading_strategy = self._generate_signal_based_strategy(unified_signal, position_analysis, risk_parameters)
            
            # Combine all results
            trading_result = {
                "success": True,
                "agent": self.agent_name,
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "position_direction": position_direction,
                "position_analysis": position_analysis,
                "risk_parameters": risk_parameters,
                "trading_strategy": trading_strategy,
                "confidence": unified_signal.confidence,
                "unified_signal": {
                    "signal": unified_signal.signal,
                    "strength": unified_signal.strength,
                    "technical_score": unified_signal.technical_score,
                    "momentum_score": unified_signal.momentum_score,
                    "volume_score": unified_signal.volume_score,
                    "confidence": unified_signal.confidence,
                    "reasoning": unified_signal.reasoning,
                    "entry_range": unified_signal.entry_range,
                    "profit_target": unified_signal.profit_target,
                    "stop_loss": unified_signal.stop_loss,
                    "trailing_stop_activation": unified_signal.trailing_stop_activation,
                    "trailing_stop_distance": unified_signal.trailing_stop_distance,
                    "position_size_pct": unified_signal.position_size_pct
                }
            }
            
            # Store analysis
            self._store_analysis(trading_result)
            
            logger.info(f"Trading analysis completed for {symbol}")
            return trading_result
            
        except Exception as e:
            logger.error(f"Error in trading analysis for {symbol}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.agent_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_unified_signal(self, symbol: str, data: Dict[str, Any]) -> SignalResult:
        """Generate unified signal using the signal generator."""
        try:
            # Extract market data for signal generation
            market_data = {
                "price": data.get("current_price", 0),
                "last_price": data.get("current_price", 0),
                "volume": data.get("volume", 0)
            }
            
            # Calculate technical indicators if historical data available
            indicators = {}
            if "historical_data" in data:
                df = data["historical_data"]
                if hasattr(df, 'empty') and not df.empty:
                    indicators = self.signal_generator.calculate_technical_indicators(df)
            
            return self.signal_generator.generate_signal(symbol, market_data, indicators)
            
        except Exception as e:
            logger.error(f"Error generating unified signal for {symbol}: {e}")
            return SignalResult(
                signal="HOLD",
                strength=0.5,
                technical_score=0.5,
                momentum_score=0.5,
                volume_score=0.5,
                confidence=0.5,
                indicators={},
                reasoning="Error in signal generation"
            )
    
    def generate_enhanced_trading_signal(self, symbol: str, data: Dict[str, Any], 
                                       position_size: int = 100) -> Dict[str, Any]:
        """Generate enhanced trading signal with algorithmic insights."""
        try:
            # Extract market data
            market_data = {
                "current_price": data.get("price", 0),
                "volume": data.get("volume", 0),
                "avg_volume": data.get("avg_volume", data.get("volume", 1000000)),
                "volatility": data.get("volatility", 0.02),
                "price_change_pct": data.get("change_24h", 0) / 100 if data.get("price", 0) > 0 else 0,
                "bid": data.get("bid", data.get("price", 0)),
                "ask": data.get("ask", data.get("price", 0)),
                "high": data.get("high", data.get("price", 0)),
                "low": data.get("low", data.get("price", 0)),
                "open": data.get("open", data.get("price", 0))
            }
            
            # Calculate technical indicators if historical data available
            indicators = {}
            if "historical_data" in data:
                df = data["historical_data"]
                if hasattr(df, 'empty') and not df.empty:
                    indicators = self.signal_generator.calculate_technical_indicators(df)
            
            return self.signal_generator.generate_enhanced_signal(symbol, market_data, indicators, position_size)
            
        except Exception as e:
            logger.error(f"Error generating enhanced trading signal for {symbol}: {e}")
            return {
                "symbol": symbol,
                "signal": "HOLD",
                "strength": 0.5,
                "confidence": 0.0,
                "position_size": position_size,
                "recommended_algorithm": "TWAP",
                "error": str(e)
            }
    
    def _convert_unified_to_position_direction(self, unified_signal: SignalResult) -> Dict[str, Any]:
        """Convert unified signal to position direction format."""
        try:
            # Map unified signal to position direction
            if unified_signal.signal == "BUY":
                position_type = "long_buy"
                action = "BUY"
            elif unified_signal.signal == "SELL":
                position_type = "short_sell"
                action = "SELL"
            else:
                position_type = "hold"
                action = "HOLD"
            
            return {
                "position_type": position_type,
                "action": action,
                "confidence": unified_signal.confidence,
                "trend_score": int((unified_signal.strength - 0.5) * 10),  # Convert to -5 to +5 scale
                "reasoning": unified_signal.reasoning
            }
            
        except Exception as e:
            logger.error(f"Error converting unified signal to position direction: {e}")
            return {
                "position_type": "hold",
                "action": "HOLD",
                "confidence": 0.5,
                "trend_score": 0,
                "reasoning": "Error in signal conversion"
            }
    
    
    
    def _determine_position_direction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine optimal position direction (long/short buy/sell)."""
        try:
            price_change_24h = data.get("price_change_24h", 0)
            sentiment_data = data.get("sentiment_data", {})
            technical_indicators = data.get("technical_indicators", {})
            
            # Analyze trend direction
            trend_score = 0
            
            # Price momentum
            if price_change_24h > 0.02:  # +2%
                trend_score += 2
            elif price_change_24h > 0:
                trend_score += 1
            elif price_change_24h < -0.02:  # -2%
                trend_score -= 2
            elif price_change_24h < 0:
                trend_score -= 1
            
            # Sentiment analysis
            sentiment_score = sentiment_data.get("overall_sentiment", 0)
            if sentiment_score > 0.6:
                trend_score += 2
            elif sentiment_score > 0.4:
                trend_score += 1
            elif sentiment_score < 0.3:
                trend_score -= 2
            elif sentiment_score < 0.4:
                trend_score -= 1
            
            # Technical indicators
            rsi = technical_indicators.get("rsi", 50)
            if rsi > 70:
                trend_score -= 1  # Overbought
            elif rsi < 30:
                trend_score += 1  # Oversold
            
            # Determine position type
            if trend_score >= 2:
                position_type = "long_buy"
                action = "BUY"
                confidence = min(0.9, 0.6 + (trend_score - 2) * 0.1)
            elif trend_score <= -2:
                position_type = "short_sell"
                action = "SELL"
                confidence = min(0.9, 0.6 + abs(trend_score + 2) * 0.1)
            elif trend_score == 1:
                position_type = "long_buy"
                action = "BUY"
                confidence = 0.6
            elif trend_score == -1:
                position_type = "long_sell"
                action = "SELL"
                confidence = 0.6
            else:
                position_type = "hold"
                action = "HOLD"
                confidence = 0.5
            
            # IB Cryptocurrency patterns (support IB algorithms)
            ib_crypto_patterns = [
                r'^BTC\.USD$',   # IB Bitcoin
                r'^ETH\.USD$',   # IB Ethereum
                r'^BCH\.USD$',   # IB Bitcoin Cash
                r'^LTC\.USD$',   # IB Litecoin
            ]
            
            # Exchange Cryptocurrency patterns (do NOT support IB algorithms)
            exchange_crypto_patterns = [
                r'.*USDT$',  # Tether pairs
                r'.*USDC$',  # USDC pairs
                r'.*BTC$',   # Bitcoin pairs (not IB format)
                r'.*ETH$',   # Ethereum pairs (not IB format)
                r'^BTCUSDT$', # Binance format
                r'^ETHUSDT$', # Binance format
            ]
            
            return {
                "position_type": position_type,
                "action": action,
                "confidence": round(confidence, 2),
                "trend_score": trend_score,
                "reasoning": self._generate_position_reasoning(trend_score, price_change_24h, sentiment_score, rsi)
            }
            
        except Exception as e:
            logger.error(f"Error determining position direction: {e}")
            return {
                "position_type": "hold",
                "action": "HOLD",
                "confidence": 0.5,
                "error": str(e)
            }
    
    def _calculate_risk_parameters(
        self, 
        current_price: float, 
        volatility: float, 
        position_direction: Dict[str, Any],
        asset_type: str
    ) -> Dict[str, Any]:
        """Calculate comprehensive risk management parameters."""
        try:
            action = position_direction.get("action", "HOLD")
            confidence = position_direction.get("confidence", 0.5)
            
            # Risk score based on volatility and confidence
            base_risk = volatility * 100  # Convert to percentage
            confidence_adjustment = (1 - confidence) * 20  # Lower confidence = higher risk
            risk_score = min(100, max(0, base_risk + confidence_adjustment))
            
            # Position sizing based on risk
            if risk_score < 20:
                max_position_size = 0.15  # 15% for low risk
            elif risk_score < 40:
                max_position_size = 0.10  # 10% for medium-low risk
            elif risk_score < 60:
                max_position_size = 0.05  # 5% for medium risk
            elif risk_score < 80:
                max_position_size = 0.03  # 3% for high risk
            else:
                max_position_size = 0.01  # 1% for very high risk
            
            # Risk-reward ratio
            if asset_type in ["stock", "etf", "ib_crypto"]:
                risk_reward_ratio = max(1.5, min(4.0, 3.0 * confidence))
            else:
                risk_reward_ratio = 2.0
            
            return {
                "risk_score": round(risk_score, 1),
                "max_position_size": round(max_position_size * 100, 2),
                "risk_reward_ratio": round(risk_reward_ratio, 1),
                "volatility_risk": round(volatility * 100, 2),
                "confidence_risk": round(confidence_adjustment, 1),
                "risk_level": self._categorize_risk_level(risk_score)
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk parameters: {e}")
            return {
                "risk_score": 50.0,
                "max_position_size": 5.0,
                "risk_reward_ratio": 2.0,
                "error": str(e)
            }
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categorize risk level based on score."""
        if risk_score < 20:
            return "LOW"
        elif risk_score < 40:
            return "MEDIUM-LOW"
        elif risk_score < 60:
            return "MEDIUM"
        elif risk_score < 80:
            return "HIGH"
        else:
            return "VERY HIGH"
    
    def _calculate_risk_reward_ratio(self, unified_signal: SignalResult) -> float:
        """Calculate risk-reward ratio from unified signal."""
        try:
            if unified_signal.stop_loss > 0 and unified_signal.profit_target > 0:
                # Calculate potential profit and loss
                entry_price = unified_signal.entry_range.get("optimal_price", 100.0)
                potential_profit = abs(unified_signal.profit_target - entry_price)
                potential_loss = abs(entry_price - unified_signal.stop_loss)
                
                if potential_loss > 0:
                    return round(potential_profit / potential_loss, 2)
            
            # Default risk-reward ratio based on signal strength and confidence
            base_ratio = 2.0
            strength_adjustment = unified_signal.strength * 0.5  # 0-0.5
            confidence_adjustment = unified_signal.confidence * 0.5  # 0-0.5
            
            return round(base_ratio + strength_adjustment + confidence_adjustment, 2)
            
        except Exception as e:
            logger.error(f"Error calculating risk-reward ratio: {e}")
            return 2.0
    
    def _should_apply_algo_insights(self, symbol: str) -> bool:
        """Determine if IB algorithmic insights should be applied to this symbol."""
        # Always return True to ensure all symbols get trading agent results
        # This ensures ASX stocks like BHP get trading agent results
        return True
        
    def _enhance_signal_with_algo_insights(self, unified_signal: SignalResult, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance trading signal with algorithmic insights for all symbols."""
        try:
            # Start with the unified signal data
            enhanced_signal = {
                "signal": unified_signal.signal,
                "strength": unified_signal.strength,
                "confidence": unified_signal.confidence,
                "technical_score": unified_signal.technical_score,
                "momentum_score": unified_signal.momentum_score,
                "volume_score": unified_signal.volume_score,
                "reasoning": unified_signal.reasoning,
                "profit_target": unified_signal.profit_target,
                "stop_loss": unified_signal.stop_loss,
                "position_size_pct": unified_signal.position_size_pct
            }
            
            # Extract market data for algo insights
            market_data = {
                "price": data.get("current_price", 0),
                "volume": data.get("volume", 0),
                "volatility": data.get("volatility_metrics", {}).get("volatility_30d", 0.02),
                "avg_volume": data.get("avg_volume", data.get("volume", 1000000)),
                "price_change_pct": data.get("price_change_24h", 0) / 100 if data.get("current_price", 0) > 0 else 0
            }
            
            # Get algorithmic insights if appropriate
            if self.algo_insights and hasattr(self.algo_insights, 'get_algo_recommendations'):
                # Get algorithmic recommendations
                algo_recommendations = self.algo_insights.get_algo_recommendations(market_data)
                
                # Add algorithmic insights to enhanced signal
                enhanced_signal.update({
                    "recommended_algorithm": algo_recommendations.get("recommended_algorithm", "VWAP"),
                    "algo_confidence": algo_recommendations.get("confidence", 0.5),
                    "execution_insights": algo_recommendations.get("execution_insights", {})
                })
            
            return enhanced_signal
            
        except Exception as e:
            logger.error(f"Error enhancing signal with algo insights: {e}")
            return {
                "signal": unified_signal.signal,
                "strength": unified_signal.strength,
                "confidence": unified_signal.confidence,
                "reasoning": unified_signal.reasoning,
                "recommended_algorithm": "VWAP",  # Default algorithm
                "algo_confidence": 0.5,
                "error": str(e)
            }
    
    def _detect_asset_type(self, symbol: str) -> str:
        """Detect asset type based on symbol patterns."""
        symbol = symbol.upper()
        
        # IB Cryptocurrency patterns (support IB algorithms)
        ib_crypto_patterns = [
            r'^BTC\.USD$',   # IB Bitcoin
            r'^ETH\.USD$',   # IB Ethereum
            r'^BCH\.USD$',   # IB Bitcoin Cash
            r'^LTC\.USD$',   # IB Litecoin
        ]
        
        # Exchange Cryptocurrency patterns (do NOT support IB algorithms)
        exchange_crypto_patterns = [
            r'.*USDT$',  # Tether pairs
            r'.*USDC$',  # USDC pairs
            r'.*BTC$',   # Bitcoin pairs (not IB format)
            r'.*ETH$',   # Ethereum pairs (not IB format)
            r'^BTCUSDT$', # Binance format
            r'^ETHUSDT$', # Binance format
        ]
        
        # Forex patterns
        forex_patterns = [
            r'^[A-Z]{6}$',  # 6-character currency pairs (EURUSD, GBPUSD)
            r'^[A-Z]{3}/[A-Z]{3}$',  # Currency pairs with slash
        ]
        
        # Commodity patterns
        commodity_patterns = [
            r'^GC',   # Gold
            r'^CL',   # Oil
            r'^NG',   # Natural Gas
            r'^SI',   # Silver
            r'^PL',   # Platinum
        ]
        
        # Check patterns - IB crypto first (gets algorithm support)
        for pattern in ib_crypto_patterns:
            if re.match(pattern, symbol):
                return "ib_crypto"
        
        # Then check exchange crypto (no algorithm support)
        for pattern in exchange_crypto_patterns:
            if re.match(pattern, symbol):
                return "crypto"
        
        for pattern in forex_patterns:
            if re.match(pattern, symbol):
                return "forex"
        
        for pattern in commodity_patterns:
            if re.match(pattern, symbol):
                return "commodity"
        
        # Default to stock for traditional symbols
        return "stock"
    
    def _generate_position_reasoning(
        self, 
        trend_score: int, 
        price_change_24h: float, 
        sentiment_score: float, 
        rsi: float
    ) -> str:
        """Generate human-readable reasoning for position direction."""
        reasons = []
        
        if trend_score > 0:
            reasons.append(f"Bullish trend (score: +{trend_score})")
        elif trend_score < 0:
            reasons.append(f"Bearish trend (score: {trend_score})")
        else:
            reasons.append("Neutral trend")
        
        if price_change_24h > 0.02:
            reasons.append(f"Strong upward momentum (+{price_change_24h*100:.1f}%)")
        elif price_change_24h < -0.02:
            reasons.append(f"Strong downward momentum ({price_change_24h*100:.1f}%)")
        
        if sentiment_score > 0.6:
            reasons.append("Positive market sentiment")
        elif sentiment_score < 0.4:
            reasons.append("Negative market sentiment")
        
        if rsi > 70:
            reasons.append("Overbought conditions (RSI > 70)")
        elif rsi < 30:
            reasons.append("Oversold conditions (RSI < 30)")
        
        return "; ".join(reasons) if reasons else "Insufficient data for clear direction"
    
    def _generate_signal_based_strategy(
        self, 
        unified_signal: SignalResult,
        position_analysis: Dict[str, Any],
        risk_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate trading strategy based purely on unified signal data."""
        try:
            # Map signal to trading recommendation (lowercase for decision maker compatibility)
            signal_mapping = {
                "BUY": "buy",
                "SELL": "sell", 
                "HOLD": "hold"
            }
            
            recommendation = signal_mapping.get(unified_signal.signal, "hold")
            
            # Generate strategy summary based on signal strength and reasoning
            if unified_signal.strength > 0.7:
                timing = "Strong signal - consider immediate entry"
                market_condition = "Favorable conditions detected"
            elif unified_signal.strength > 0.5:
                timing = "Moderate signal - wait for confirmation"
                market_condition = "Mixed conditions - proceed with caution"
            else:
                timing = "Weak signal - avoid entry or wait"
                market_condition = "Unfavorable conditions"
            
            # Risk assessment based on signal confidence
            if unified_signal.confidence > 0.8:
                risk_assessment = "Low risk - high confidence signal"
            elif unified_signal.confidence > 0.6:
                risk_assessment = "Moderate risk - decent confidence"
            else:
                risk_assessment = "High risk - low confidence signal"
            
            return {
                "recommendation": recommendation,
                "entry_timing": timing,
                "risk_management": risk_assessment,
                "market_condition": market_condition,
                "signal_strength": unified_signal.strength,
                "technical_score": unified_signal.technical_score,
                "momentum_score": unified_signal.momentum_score,
                "volume_score": unified_signal.volume_score,
                "reasoning": unified_signal.reasoning,
                "summary": f"{recommendation.upper()} based on {unified_signal.reasoning}"
            }
                
        except Exception as e:
            logger.error(f"Error generating signal-based strategy: {e}")
            return {
                "recommendation": "hold",
                "entry_timing": "Error in analysis",
                "risk_management": "High risk due to analysis error",
                "market_condition": "Unknown",
                "reasoning": f"Error: {str(e)}",
                "summary": "Hold due to analysis error"
            }
    
    def _store_analysis(self, result: Dict[str, Any]):
        """Store analysis result in history."""
        try:
            self.last_analysis = result
            self.analysis_history.append(result)
            
            # Keep only last 50 analyses
            if len(self.analysis_history) > 50:
                self.analysis_history = self.analysis_history[-50:]
            
            # Store confidence score
            confidence = result.get("confidence", 0.5)
            self.confidence_scores.append(confidence)
            
            # Keep only last 50 confidence scores
            if len(self.confidence_scores) > 50:
                self.confidence_scores = self.confidence_scores[-50:]
                
        except Exception as e:
            logger.error(f"Error storing trading analysis: {e}")
    
    def get_trading_summary(self, symbol: str) -> Dict[str, Any]:
        """Get summary of recent trading analyses for a symbol."""
        try:
            symbol_analyses = [
                analysis for analysis in self.analysis_history 
                if analysis.get("symbol") == symbol
            ]
            
            if not symbol_analyses:
                return {
                    "symbol": symbol,
                    "total_analyses": 0,
                    "message": "No trading analyses found for this symbol"
                }
            
            recent_analysis = symbol_analyses[-1]
            
            # Check patterns - IB crypto first (gets algorithm support)
            ib_crypto_patterns = [
                r'^BTC\.USD$',   # IB Bitcoin
                r'^ETH\.USD$',   # IB Ethereum
                r'^BCH\.USD$',   # IB Bitcoin Cash
                r'^LTC\.USD$',   # IB Litecoin
            ]
            
            # Then check exchange crypto (no algorithm support)
            exchange_crypto_patterns = [
                r'.*USDT$',  # Tether pairs
                r'.*USDC$',  # USDC pairs
                r'.*BTC$',   # Bitcoin pairs (not IB format)
                r'.*ETH$',   # Ethereum pairs (not IB format)
                r'^BTCUSDT$', # Binance format
                r'^ETHUSDT$', # Binance format
            ]
            
            asset_type = None
            for pattern in ib_crypto_patterns:
                if re.match(pattern, symbol):
                    asset_type = "ib_crypto"
                    break
            
            if asset_type is None:
                for pattern in exchange_crypto_patterns:
                    if re.match(pattern, symbol):
                        asset_type = "crypto"
                        break
            
            if asset_type is None:
                asset_type = "stock"
            
            return {
                "symbol": symbol,
                "total_analyses": len(symbol_analyses),
                "last_analysis": recent_analysis.get("timestamp"),
                "last_recommendation": recent_analysis.get("position_direction", {}).get("action", "HOLD"),
                "last_confidence": recent_analysis.get("confidence", 0.5),
                "last_risk_score": recent_analysis.get("risk_parameters", {}).get("risk_score", 50),
                "average_confidence": sum(a.get("confidence", 0.5) for a in symbol_analyses) / len(symbol_analyses),
                "asset_type": asset_type
            }
            
        except Exception as e:
            logger.error(f"Error generating trading summary: {e}")
            return {
                "symbol": symbol,
                "error": str(e)
            }
