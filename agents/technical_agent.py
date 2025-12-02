"""Technical analysis agent for cryptocurrency trading."""

import logging
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

from .base_agent import BaseAgent
from data.indicators import TechnicalIndicators
from config.settings import MarketResearcherConfig
from analyzers.signal_generator import UnifiedSignalGenerator, SignalResult

logger = logging.getLogger(__name__)


class TechnicalAgent(BaseAgent):
    """Agent specialized in technical analysis of cryptocurrency markets."""
    
    def __init__(self, llm_client, prompt_manager, config: MarketResearcherConfig):
        """Initialize technical analysis agent."""
        super().__init__(llm_client, prompt_manager, config, "Technical Analyst")
        self.indicators = TechnicalIndicators()
        self.signal_generator = UnifiedSignalGenerator()
        
    def get_agent_type(self) -> str:
        """Return the agent type identifier."""
        return "technical"
    
    def analyze(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform technical analysis for the given symbol."""
        try:
            if not self._validate_analysis_data(data):
                return {
                    "success": False,
                    "error": "Invalid input data",
                    "agent": self.agent_name
                }
            
            # Extract market data
            market_data = self._extract_market_data(data)
            
            # Calculate technical indicators using unified signal generator
            indicators_data = self._calculate_unified_indicators(data)
            
            # Generate support/resistance levels
            support_resistance = self._calculate_support_resistance(data)
            
            # Generate unified signal
            signal_result = self._generate_unified_signal(symbol, market_data, indicators_data)
            
            # Create analysis prompt
            messages = self.prompt_manager.create_technical_analysis_prompt(
                symbol=symbol,
                market_data=market_data,
                indicators={**indicators_data, **support_resistance}
            )
            
            # Execute LLM analysis
            llm_result = self._execute_llm_analysis(messages)
            
            if llm_result["success"]:
                # Use raw LLM response content for analysis
                raw_content = llm_result["raw_response"]
                
                # Parse technical signals from raw content (legacy)
                technical_signals = self._extract_technical_signals(raw_content)
                
                # Use unified signal generation results
                technical_score = signal_result.technical_score * 100  # Convert to 0-100 scale
                confidence = signal_result.confidence
                
                analysis_result = {
                    "success": True,
                    "agent": self.agent_name,
                    "symbol": symbol,
                    "analysis": raw_content,  # Use raw LLM content
                    "summary": raw_content[:300] + "..." if len(raw_content) > 300 else raw_content,
                    "technical_signals": technical_signals,
                    "technical_score": technical_score,
                    "confidence": confidence,
                    "indicators": indicators_data,
                    "support_resistance": support_resistance,
                    # Remove recommendation - Trading Agent handles all trading decisions
                    "unified_signal": {
                        "signal": signal_result.signal,
                        "strength": signal_result.strength,
                        "technical_score": signal_result.technical_score,
                        "momentum_score": signal_result.momentum_score,
                        "volume_score": signal_result.volume_score,
                        "reasoning": signal_result.reasoning
                    },
                    "timestamp": llm_result["timestamp"]
                }
                
                # Store analysis
                self._store_analysis(analysis_result)
                
                return analysis_result
            else:
                return llm_result
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Error in technical analysis for {symbol}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.agent_name,
                "symbol": symbol
            }
    
    def _extract_market_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and format market data for analysis."""
        try:
            # Debug: Log available keys and volume value
            logging.getLogger(__name__).info(f"Available data keys: {list(data.keys())}")
            logging.getLogger(__name__).info(f"Raw volume value from data: {data.get('volume')} (type: {type(data.get('volume'))})")
            
            # Check if volume exists in historical data
            if 'historical_data' in data:
                df = data['historical_data']
                if isinstance(df, pd.DataFrame) and not df.empty and 'volume' in df.columns:
                    latest_volume = df['volume'].iloc[-1]
                    logging.getLogger(__name__).info(f"Latest volume from historical data: {latest_volume}")
            
            market_data = {
                "price": data.get("current_price", data.get("price", 0)),
                "change_24h": data.get("price_change_24h", data.get("change_24h", 0)),
                "volume": data.get("volume", data.get("volume_24h", data.get("daily_volume", 0))),
                "high_24h": data.get("high_24h", data.get("high", 0)),
                "low_24h": data.get("low_24h", data.get("low", 0))
            }
            
            # If volume is 0, check market_overview for 24h volume instead of historical data
            if market_data["volume"] == 0 and 'market_overview' in data:
                market_overview = data['market_overview']
                if isinstance(market_overview, dict):
                    # Try various volume keys in market overview
                    overview_volume = (market_overview.get('volume') or 
                                     market_overview.get('volume_24h') or 
                                     market_overview.get('daily_volume') or 0)
                    if overview_volume > 0:
                        market_data["volume"] = overview_volume
                        logging.getLogger(__name__).info(f"Using 24h volume from market overview: {market_data['volume']}")
                    else:
                        # Fallback to historical data only if market overview doesn't have volume
                        if 'historical_data' in data:
                            df = data['historical_data']
                            if isinstance(df, pd.DataFrame) and not df.empty and 'volume' in df.columns:
                                market_data["volume"] = df['volume'].iloc[-1]
                                logging.getLogger(__name__).info(f"Fallback: Using latest volume from historical data: {market_data['volume']}")
            elif market_data["volume"] == 0 and 'historical_data' in data:
                # Original fallback if no market_overview
                df = data['historical_data']
                if isinstance(df, pd.DataFrame) and not df.empty and 'volume' in df.columns:
                    market_data["volume"] = df['volume'].iloc[-1]
                    logging.getLogger(__name__).info(f"Using volume from historical data: {market_data['volume']}")
            
            # Debug: Log final extracted volume
            logging.getLogger(__name__).info(f"Final extracted volume: {market_data['volume']}")
            
            # Add price history if available
            if "price_history" in data:
                market_data["price_history"] = data["price_history"]
            elif "historical_data" in data:
                df = data["historical_data"]
                if isinstance(df, pd.DataFrame) and not df.empty:
                    market_data["price_history"] = self._format_price_history(df)
            
            return market_data
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error extracting market data: {e}")
            return {"price": 0, "change_24h": 0, "volume": 0}
    
    def _generate_unified_signal(self, symbol: str, market_data: Dict[str, Any], 
                               indicators_data: Dict[str, Any]) -> SignalResult:
        """Generate unified signal using the signal generator."""
        try:
            return self.signal_generator.generate_signal(symbol, market_data, indicators_data)
        except Exception as e:
            logging.getLogger(__name__).error(f"Error generating unified signal: {e}")
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
    
    def _generate_enhanced_signal(self, symbol: str, market_data: Dict[str, Any], 
                                indicators_data: Dict[str, Any], position_size: int = 100) -> Dict[str, Any]:
        """Generate enhanced signal with algorithmic insights."""
        try:
            return self.signal_generator.generate_enhanced_signal(symbol, market_data, indicators_data, position_size)
        except Exception as e:
            logging.getLogger(__name__).error(f"Error generating enhanced signal: {e}")
            return {
                "symbol": symbol,
                "signal": "HOLD",
                "strength": 0.5,
                "confidence": 0.0,
                "position_size": position_size,
                "recommended_algorithm": "VWAP",
                "error": str(e)
            }
    
    def _calculate_unified_indicators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate technical indicators using unified signal generator."""
        try:
            # If we have historical DataFrame, use unified signal generator
            if "historical_data" in data:
                df = data["historical_data"]
                if isinstance(df, pd.DataFrame) and not df.empty:
                    return self.signal_generator.calculate_technical_indicators(df)
            
            # Fallback to legacy method
            return self._calculate_indicators_legacy(data)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error calculating unified indicators: {e}")
            return self._calculate_indicators_legacy(data)
    
    def _calculate_indicators_legacy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate technical indicators from market data."""
        try:
            # If indicators already calculated, return them
            if "technical_indicators" in data:
                return data["technical_indicators"]
            elif "indicators" in data:
                return data["indicators"]
            
            # If we have historical DataFrame, calculate indicators
            if "historical_data" in data:
                df = data["historical_data"]
                if isinstance(df, pd.DataFrame) and not df.empty:
                    df_with_indicators = self.indicators.calculate_all_indicators(df)
                    latest = df_with_indicators.iloc[-1]
                    
                    return {
                        "rsi": latest.get("rsi", np.nan),
                        "macd_line": latest.get("macd_line", np.nan),
                        "macd_signal": latest.get("macd_signal", np.nan),
                        "macd_histogram": latest.get("macd_histogram", np.nan),
                        "bb_upper": latest.get("bb_upper", np.nan),
                        "bb_middle": latest.get("bb_middle", np.nan),
                        "bb_lower": latest.get("bb_lower", np.nan),
                        "sma_20": latest.get("sma_20", np.nan),
                        "sma_50": latest.get("sma_50", np.nan),
                        "ema_12": latest.get("ema_12", np.nan),
                        "ema_26": latest.get("ema_26", np.nan),
                        "stoch_k": latest.get("stoch_k", np.nan),
                        "stoch_d": latest.get("stoch_d", np.nan),
                        "atr": latest.get("atr", np.nan)
                    }
            
            # Return empty indicators if no data available
            return {
                "rsi": "N/A",
                "macd_line": "N/A",
                "macd_signal": "N/A",
                "bb_upper": "N/A",
                "bb_lower": "N/A"
            }
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error calculating indicators: {e}")
            return {}
    
    def _calculate_support_resistance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate support and resistance levels."""
        try:
            if "historical_data" in data:
                df = data["historical_data"]
                if isinstance(df, pd.DataFrame) and not df.empty:
                    levels = self.indicators.calculate_support_resistance(df)
                    return {
                        "support_levels": levels.get("support", []),
                        "resistance_levels": levels.get("resistance", [])
                    }
            
            return {"support_levels": [], "resistance_levels": []}
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error calculating support/resistance: {e}")
            return {"support_levels": [], "resistance_levels": []}
    
    def _extract_technical_signals(self, analysis: str) -> Dict[str, Any]:
        """Extract technical signals from LLM analysis."""
        try:
            full_text = analysis.lower() if isinstance(analysis, str) else str(analysis).lower()
            
            signals = {
                "trend": "neutral",
                "momentum": "neutral",
                "volatility": "normal",
                "volume": "normal",
                "overall_signal": "hold"
            }
            
            # Extract trend signals
            if any(word in full_text for word in ["strong bullish", "very bullish", "uptrend"]):
                signals["trend"] = "strong_bullish"
            elif any(word in full_text for word in ["bullish", "upward", "rising"]):
                signals["trend"] = "bullish"
            elif any(word in full_text for word in ["strong bearish", "very bearish", "downtrend"]):
                signals["trend"] = "strong_bearish"
            elif any(word in full_text for word in ["bearish", "downward", "falling"]):
                signals["trend"] = "bearish"
            
            # Extract momentum signals
            if any(word in full_text for word in ["strong momentum", "accelerating"]):
                signals["momentum"] = "strong"
            elif any(word in full_text for word in ["momentum", "gaining"]):
                signals["momentum"] = "positive"
            elif any(word in full_text for word in ["losing momentum", "weakening"]):
                signals["momentum"] = "negative"
            
            # Extract overall signal
            if any(word in full_text for word in ["strong buy", "buy recommendation"]):
                signals["overall_signal"] = "strong_buy"
            elif "buy" in full_text:
                signals["overall_signal"] = "buy"
            elif any(word in full_text for word in ["strong sell", "sell recommendation"]):
                signals["overall_signal"] = "strong_sell"
            elif "sell" in full_text:
                signals["overall_signal"] = "sell"
            
            return signals
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error extracting technical signals: {e}")
            return {"overall_signal": "hold", "trend": "neutral"}
    
    def _calculate_technical_score(
        self, 
        indicators: Dict[str, Any], 
        signals: Dict[str, Any]
    ) -> float:
        """Calculate overall technical score (0-100)."""
        try:
            score = 50  # Neutral starting point
            
            # RSI scoring
            rsi = indicators.get("rsi")
            if isinstance(rsi, (int, float)) and not np.isnan(rsi):
                if rsi > 70:
                    score -= 15  # Overbought
                elif rsi < 30:
                    score += 15  # Oversold
                elif 40 <= rsi <= 60:
                    score += 5   # Neutral zone
            
            # MACD scoring
            macd_line = indicators.get("macd_line")
            macd_signal = indicators.get("macd_signal")
            if all(isinstance(x, (int, float)) and not np.isnan(x) for x in [macd_line, macd_signal]):
                if macd_line > macd_signal:
                    score += 10  # Bullish crossover
                else:
                    score -= 10  # Bearish crossover
            
            # Trend scoring
            trend = signals.get("trend", "neutral")
            trend_scores = {
                "strong_bullish": 20,
                "bullish": 10,
                "neutral": 0,
                "bearish": -10,
                "strong_bearish": -20
            }
            score += trend_scores.get(trend, 0)
            
            # Momentum scoring
            momentum = signals.get("momentum", "neutral")
            momentum_scores = {
                "strong": 10,
                "positive": 5,
                "neutral": 0,
                "negative": -5
            }
            score += momentum_scores.get(momentum, 0)
            
            # Ensure score is within bounds
            return max(0, min(100, score))
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error calculating technical score: {e}")
            return 50.0
    
    # Removed _generate_recommendation - Trading Agent handles all trading decisions
    def _format_price_history(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Format price history from DataFrame."""
        try:
            history = []
            # Calculate percentage change for the entire close column
            pct_changes = df["close"].pct_change() * 100
            
            for i, (idx, row) in enumerate(df.tail(10).iterrows()):
                # Get the corresponding percentage change for this row
                change = float(pct_changes.iloc[df.index.get_loc(idx)]) if not pd.isna(pct_changes.iloc[df.index.get_loc(idx)]) else 0
                
                history.append({
                    "timestamp": idx.strftime("%Y-%m-%d %H:%M") if hasattr(idx, 'strftime') else str(idx),
                    "price": float(row["close"]),
                    "change": change
                })
            return history
        except Exception as e:
            logging.getLogger(__name__).error(f"Error formatting price history: {e}")
            return []
    
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
            logging.getLogger(__name__).error(f"Error storing analysis: {e}")
    
    def get_technical_summary(self, symbol: str) -> Dict[str, Any]:
        """Get summary of recent technical analysis."""
        try:
            if not self.last_analysis:
                return {"error": "No recent analysis available"}
            
            return {
                "symbol": symbol,
                "last_analysis": self.last_analysis.get("timestamp"),
                "technical_score": self.last_analysis.get("technical_score", 0),
                "recommendation": self.last_analysis.get("recommendation", {}),
                "key_indicators": {
                    "rsi": self.last_analysis.get("indicators", {}).get("rsi"),
                    "macd_signal": self.last_analysis.get("technical_signals", {}).get("trend"),
                    "overall_signal": self.last_analysis.get("technical_signals", {}).get("overall_signal")
                },
                "confidence": self.last_analysis.get("confidence", 0)
            }
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error getting technical summary: {e}")
            return {"error": str(e)}
