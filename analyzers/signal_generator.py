#!/usr/bin/env python3
"""
Unified Signal Generation Module

This module provides a shared signal generation system that can be used across
different agents (TechnicalAgent, TradingAgent) for consistent trading signals.
Enhanced with algorithmic parameter insights from Interactive Brokers.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass

from .algo_insights import create_algo_insights_analyzer

logger = logging.getLogger(__name__)

@dataclass
class SignalResult:
    """Standardized signal result structure with position management."""
    signal: str  # BUY, SELL, HOLD
    strength: float  # 0-1 signal strength
    technical_score: float  # 0-1 technical analysis score
    momentum_score: float  # 0-1 momentum score
    volume_score: float  # 0-1 volume score
    confidence: float  # 0-1 overall confidence
    indicators: Dict[str, float]  # Technical indicators used
    reasoning: str  # Human-readable reasoning
    # Position management fields
    entry_range: Dict[str, float]  # min_price, max_price, optimal_price
    profit_target: float  # Single profit target
    stop_loss: float  # Stop loss price
    trailing_stop_activation: float  # Price to activate trailing stop
    trailing_stop_distance: float  # Trailing stop distance percentage
    position_size_pct: float  # Recommended position size as % of portfolio


class UnifiedSignalGenerator:
    """Unified signal generation system with technical analysis and algorithmic insights."""
    
    def __init__(self):
        self.algo_analyzer = create_algo_insights_analyzer()
        self.logger = logging.getLogger(__name__)
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical indicators for signal generation."""
        try:
            if len(data) < 20:
                self.logger.warning("Insufficient data for technical analysis")
                return {}
            
            indicators = {}
            
            # Convert numeric columns to float, preserve datetime index
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
            
            # Handle any remaining non-numeric columns that should be numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
            
            # RSI (simplified calculation)
            close_prices = data['close']
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            indicators['rsi'] = float(rsi.iloc[-1]) if not rsi.empty and not pd.isna(rsi.iloc[-1]) else 50.0
            
            # MACD (simplified calculation)
            ema_12 = close_prices.ewm(span=12).mean()
            ema_26 = close_prices.ewm(span=26).mean()
            macd = ema_12 - ema_26
            macd_signal = macd.ewm(span=9).mean()
            macd_histogram = macd - macd_signal
            
            indicators['macd'] = float(macd.iloc[-1]) if not macd.empty and not pd.isna(macd.iloc[-1]) else 0.0
            indicators['macd_signal'] = float(macd_signal.iloc[-1]) if not macd_signal.empty and not pd.isna(macd_signal.iloc[-1]) else 0.0
            indicators['macd_histogram'] = float(macd_histogram.iloc[-1]) if not macd_histogram.empty and not pd.isna(macd_histogram.iloc[-1]) else 0.0
            
            # Bollinger Bands (simplified calculation)
            sma_20 = close_prices.rolling(20).mean()
            std_20 = close_prices.rolling(20).std()
            bb_upper = sma_20 + (2 * std_20)
            bb_lower = sma_20 - (2 * std_20)
            
            current_price = float(close_prices.iloc[-1])
            indicators['bb_upper'] = float(bb_upper.iloc[-1]) if not bb_upper.empty and not pd.isna(bb_upper.iloc[-1]) else current_price * 1.02
            indicators['bb_lower'] = float(bb_lower.iloc[-1]) if not bb_lower.empty and not pd.isna(bb_lower.iloc[-1]) else current_price * 0.98
            indicators['bb_middle'] = float(sma_20.iloc[-1]) if not sma_20.empty and not pd.isna(sma_20.iloc[-1]) else current_price
            
            bb_range = indicators['bb_upper'] - indicators['bb_lower']
            indicators['bb_position'] = (current_price - indicators['bb_lower']) / bb_range if bb_range > 0 else 0.5
            
            # Moving averages
            indicators['sma_20'] = float(sma_20.iloc[-1]) if not sma_20.empty and not pd.isna(sma_20.iloc[-1]) else current_price
            sma_50 = close_prices.rolling(50).mean() if len(data) >= 50 else sma_20
            indicators['sma_50'] = float(sma_50.iloc[-1]) if not sma_50.empty and not pd.isna(sma_50.iloc[-1]) else indicators['sma_20']
            
            # Volume analysis
            if 'volume' in data.columns:
                volume_sma = data['volume'].rolling(20).mean()
                indicators['volume_sma'] = float(volume_sma.iloc[-1]) if not volume_sma.empty and not pd.isna(volume_sma.iloc[-1]) else float(data['volume'].iloc[-1])
                indicators['volume_ratio'] = float(data['volume'].iloc[-1]) / indicators['volume_sma'] if indicators['volume_sma'] > 0 else 1.0
            else:
                indicators['volume_sma'] = 1000000.0  # Default volume
                indicators['volume_ratio'] = 1.0
            
            # Price momentum
            if len(data) >= 2:
                indicators['price_change_1d'] = float((close_prices.iloc[-1] - close_prices.iloc[-2]) / close_prices.iloc[-2] * 100)
            else:
                indicators['price_change_1d'] = 0.0
                
            if len(data) >= 6:
                indicators['price_change_5d'] = float((close_prices.iloc[-1] - close_prices.iloc[-6]) / close_prices.iloc[-6] * 100)
            else:
                indicators['price_change_5d'] = indicators['price_change_1d']
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Technical indicator calculation failed: {e}")
            return {}
    
    def generate_signal_score(self, symbol: str, market_data: Dict[str, Any], 
                            technical_indicators: Dict[str, float]) -> SignalResult:
        """Generate trading signal based on technical analysis."""
        try:
            if not technical_indicators:
                return SignalResult(
                    signal="HOLD",
                    strength=0.5,
                    technical_score=0.5,
                    momentum_score=0.5,
                    volume_score=0.5,
                    confidence=0.5,
                    indicators={},
                    reasoning="Insufficient technical data"
                )
            
            scores = {"technical": 0.5, "momentum": 0.5, "volume": 0.5}
            reasoning_parts = []
            
            # Technical Analysis Score
            technical_score = 0.5
            
            # RSI analysis
            rsi = technical_indicators.get('rsi', 50)
            if rsi > 70:
                technical_score -= 0.2  # Overbought
                reasoning_parts.append(f"RSI overbought ({rsi:.1f})")
            elif rsi < 30:
                technical_score += 0.2  # Oversold
                reasoning_parts.append(f"RSI oversold ({rsi:.1f})")
            elif 40 <= rsi <= 60:
                technical_score += 0.1  # Neutral zone
                reasoning_parts.append(f"RSI neutral ({rsi:.1f})")
            
            # MACD analysis
            macd = technical_indicators.get('macd', 0)
            macd_signal = technical_indicators.get('macd_signal', 0)
            macd_histogram = technical_indicators.get('macd_histogram', 0)
            
            if macd > macd_signal and macd_histogram > 0:
                technical_score += 0.15  # Bullish MACD
                reasoning_parts.append("MACD bullish crossover")
            elif macd < macd_signal and macd_histogram < 0:
                technical_score -= 0.15  # Bearish MACD
                reasoning_parts.append("MACD bearish crossover")
            
            # Bollinger Bands analysis
            bb_position = technical_indicators.get('bb_position', 0.5)
            if bb_position > 0.8:
                technical_score -= 0.1  # Near upper band
                reasoning_parts.append("Near BB upper band")
            elif bb_position < 0.2:
                technical_score += 0.1  # Near lower band
                reasoning_parts.append("Near BB lower band")
            
            # Moving average crossover
            current_price = market_data.get("price", market_data.get("last_price", 0))
            sma_20 = technical_indicators.get('sma_20', current_price)
            sma_50 = technical_indicators.get('sma_50', current_price)
            
            if current_price > sma_20 > sma_50:
                technical_score += 0.1  # Bullish trend
                reasoning_parts.append("Price above MA20 > MA50")
            elif current_price < sma_20 < sma_50:
                technical_score -= 0.1  # Bearish trend
                reasoning_parts.append("Price below MA20 < MA50")
            
            scores["technical"] = max(0, min(1, technical_score))
            
            # Momentum Analysis Score
            momentum_score = 0.5
            
            price_change_1d = technical_indicators.get('price_change_1d', 0)
            price_change_5d = technical_indicators.get('price_change_5d', 0)
            
            # Short-term momentum
            if price_change_1d > 2:
                momentum_score += 0.2
                reasoning_parts.append(f"Strong 1D momentum (+{price_change_1d:.1f}%)")
            elif price_change_1d > 0.5:
                momentum_score += 0.1
                reasoning_parts.append(f"Positive 1D momentum (+{price_change_1d:.1f}%)")
            elif price_change_1d < -2:
                momentum_score -= 0.2
                reasoning_parts.append(f"Weak 1D momentum ({price_change_1d:.1f}%)")
            elif price_change_1d < -0.5:
                momentum_score -= 0.1
                reasoning_parts.append(f"Negative 1D momentum ({price_change_1d:.1f}%)")
            
            # Medium-term momentum
            if price_change_5d > 5:
                momentum_score += 0.15
                reasoning_parts.append(f"Strong 5D trend (+{price_change_5d:.1f}%)")
            elif price_change_5d < -5:
                momentum_score -= 0.15
                reasoning_parts.append(f"Weak 5D trend ({price_change_5d:.1f}%)")
            
            scores["momentum"] = max(0, min(1, momentum_score))
            
            # Volume Analysis Score
            volume_score = 0.5
            volume_ratio = technical_indicators.get('volume_ratio', 1)
            
            if volume_ratio > 1.5:
                volume_score += 0.2  # High volume
                reasoning_parts.append(f"High volume ({volume_ratio:.1f}x avg)")
            elif volume_ratio > 1.2:
                volume_score += 0.1  # Above average volume
                reasoning_parts.append(f"Above avg volume ({volume_ratio:.1f}x)")
            elif volume_ratio < 0.5:
                volume_score -= 0.1  # Low volume
                reasoning_parts.append(f"Low volume ({volume_ratio:.1f}x avg)")
            
            scores["volume"] = max(0, min(1, volume_score))
            
            # Overall signal with weighted scoring (same as IB system)
            overall_score = (scores["technical"] * 0.5 + scores["momentum"] * 0.3 + scores["volume"] * 0.2)
            
            # Signal thresholds (same as IB system)
            if overall_score > 0.7:
                signal = "BUY"
            elif overall_score < 0.3:
                signal = "SELL"
            else:
                signal = "HOLD"
            
            # Calculate confidence based on score consistency
            score_variance = np.var([scores["technical"], scores["momentum"], scores["volume"]])
            confidence = max(0.3, min(0.9, 1.0 - score_variance))
            
            reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Neutral market conditions"
            
            # Calculate position management parameters
            current_price = market_data.get('price', market_data.get('last_price', 0))
            position_params = self._calculate_position_management(
                signal, overall_score, confidence, current_price, technical_indicators
            )
            
            return SignalResult(
                signal=signal,
                strength=overall_score,
                technical_score=scores["technical"],
                momentum_score=scores["momentum"],
                volume_score=scores["volume"],
                confidence=confidence,
                indicators=technical_indicators,
                reasoning=reasoning,
                entry_range=position_params["entry_range"],
                profit_target=position_params["profit_target"],
                stop_loss=position_params["stop_loss"],
                trailing_stop_activation=position_params["trailing_stop_activation"],
                trailing_stop_distance=position_params["trailing_stop_distance"],
                position_size_pct=position_params["position_size_pct"]
            )
            
        except Exception as e:
            self.logger.error(f"Signal generation failed for {symbol}: {e}")
            return SignalResult(
                signal="HOLD",
                strength=0.5,
                technical_score=0.5,
                momentum_score=0.5,
                volume_score=0.5,
                confidence=0.5,
                indicators={},
                reasoning=f"Error: {str(e)}",
                entry_range={"min_price": 0, "max_price": 0, "optimal_price": 0},
                profit_targets={"target_1": 0, "target_2": 0, "target_3": 0},
                stop_loss=0,
                trailing_stop_activation=0,
                trailing_stop_distance=0,
                position_size_pct=0
            )
    
    def generate_signal(self, symbol: str, market_data: Dict[str, Any], 
                       technical_indicators: Dict[str, float]) -> SignalResult:
        """Generate a unified trading signal with technical analysis and algorithmic insights."""
        try:
            # Generate signal result (returns SignalResult object, not tuple)
            signal_result = self.generate_signal_score(
                symbol, market_data, technical_indicators
            )
            
            # Extract values from SignalResult
            signal = signal_result.signal
            overall_score = signal_result.strength
            scores = {
                "technical": signal_result.technical_score,
                "momentum": signal_result.momentum_score,
                "volume": signal_result.volume_score
            }
            
            # Return the original signal_result (already complete)
            return signal_result
            
        except Exception as e:
            self.logger.error(f"Error generating signal for {symbol}: {e}")
            return SignalResult(
                signal="HOLD",
                strength=0.5,
                technical_score=0.5,
                momentum_score=0.5,
                volume_score=0.5,
                confidence=0.5,
                indicators={},
                reasoning=f"Error: {str(e)}",
                entry_range={"min_price": 0, "max_price": 0, "optimal_price": 0},
                profit_targets={"target_1": 0, "target_2": 0, "target_3": 0},
                stop_loss=0,
                trailing_stop_activation=0,
                trailing_stop_distance=0,
                position_size_pct=0
            )
    
    def _calculate_position_management(
        self, 
        signal: str, 
        strength: float, 
        confidence: float, 
        current_price: float,
        technical_indicators: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate comprehensive position management parameters."""
        try:
            if current_price <= 0:
                return self._get_default_position_params()
            
            # Get volatility for risk calculations
            volatility = technical_indicators.get('volatility', 0.02)  # Default 2%
            atr = technical_indicators.get('atr', current_price * 0.02)  # Default 2% ATR
            
            # Position size based on signal strength and confidence
            base_position_size = min(strength * confidence * 0.15, 0.10)  # Max 10% of portfolio
            
            if signal == "BUY":
                # Entry range for BUY signals
                entry_range = self._calculate_buy_entry_range(current_price, strength, technical_indicators)
                
                # Single profit target (2x ATR) - calculated from entry max to ensure it's above entry
                entry_max = entry_range.get("max_price", current_price)
                profit_target = entry_max * (1 + (atr / entry_max) * 2)
                
                # Stop loss (risk-based)
                stop_loss = current_price * (1 - min(0.05, max(0.02, volatility * 1.5)))
                
                # Trailing stop activation (when to start trailing)
                trailing_stop_activation = current_price * (1 + (atr / current_price) * 1.5)
                
            elif signal == "SELL":
                # Entry range for SELL signals
                entry_range = self._calculate_sell_entry_range(current_price, strength, technical_indicators)
                
                # Single profit target for short positions - calculated from entry max to ensure it's below entry
                entry_max = entry_range.get("max_price", current_price)
                profit_target = entry_max * (1 - (atr / entry_max) * 2)
                
                # Stop loss for short
                stop_loss = current_price * (1 + min(0.05, max(0.02, volatility * 1.5)))
                
                # Trailing stop activation for short
                trailing_stop_activation = current_price * (1 - (atr / current_price) * 1.5)
                
            else:  # HOLD
                return self._get_hold_position_params(current_price)
            
            # Trailing stop distance (percentage)
            trailing_stop_distance = min(3.0, max(1.0, volatility * 100))  # 1-3%
            
            return {
                "entry_range": entry_range,
                "profit_target": profit_target,
                "stop_loss": stop_loss,
                "trailing_stop_activation": trailing_stop_activation,
                "trailing_stop_distance": trailing_stop_distance,
                "position_size_pct": base_position_size * 100  # Convert to percentage
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating position management: {e}")
            return self._get_default_position_params()
    
    def _calculate_buy_entry_range(self, current_price: float, strength: float, indicators: Dict[str, float]) -> Dict[str, float]:
        """Calculate optimal entry range for BUY signals."""
        # Support levels and technical factors
        support_level = indicators.get('support', current_price * 0.98)
        bb_lower = indicators.get('bb_lower', current_price * 0.97)
        
        # Entry range based on signal strength
        if strength > 0.8:  # Strong signal - can enter at market
            return {
                "min_price": current_price * 0.995,  # Very tight range
                "max_price": current_price * 1.005,
                "optimal_price": current_price
            }
        elif strength > 0.6:  # Moderate signal - wait for slight pullback
            return {
                "min_price": max(support_level, current_price * 0.985),
                "max_price": current_price * 1.01,
                "optimal_price": current_price * 0.995
            }
        else:  # Weak signal - wait for better entry
            return {
                "min_price": max(bb_lower, current_price * 0.97),
                "max_price": current_price * 0.99,
                "optimal_price": current_price * 0.98
            }
    
    def _calculate_sell_entry_range(self, current_price: float, strength: float, indicators: Dict[str, float]) -> Dict[str, float]:
        """Calculate optimal entry range for SELL signals."""
        # Resistance levels and technical factors
        resistance_level = indicators.get('resistance', current_price * 1.02)
        bb_upper = indicators.get('bb_upper', current_price * 1.03)
        
        # Entry range for short positions
        if strength > 0.8:  # Strong sell signal
            return {
                "min_price": current_price * 0.995,
                "max_price": current_price * 1.005,
                "optimal_price": current_price
            }
        elif strength > 0.6:  # Moderate sell signal
            return {
                "min_price": current_price * 0.99,
                "max_price": min(resistance_level, current_price * 1.015),
                "optimal_price": current_price * 1.005
            }
        else:  # Weak sell signal
            return {
                "min_price": current_price * 1.01,
                "max_price": min(bb_upper, current_price * 1.03),
                "optimal_price": current_price * 1.02
            }
    
    def _get_hold_position_params(self, current_price: float) -> Dict[str, Any]:
        """Get position parameters for HOLD signals."""
        return {
            "entry_range": {
                "min_price": current_price * 0.95,
                "max_price": current_price * 1.05,
                "optimal_price": current_price
            },
            "profit_target": current_price * 1.02,
            "stop_loss": current_price * 0.95,
            "trailing_stop_activation": current_price * 1.03,
            "trailing_stop_distance": 2.0,
            "position_size_pct": 2.0  # Small position for HOLD
        }
    
    def _get_default_position_params(self, current_price: float = 100.0) -> Dict[str, Any]:
        """Get default position parameters for error cases."""
        return {
            "entry_range": {"min_price": current_price, "max_price": current_price, "optimal_price": current_price},
            "profit_target": current_price,
            "stop_loss": current_price,
            "trailing_stop_activation": current_price,
            "trailing_stop_distance": 2.0,
            "position_size_pct": 0.0
        }
    
    def generate_enhanced_signal(self, symbol: str, market_data: Dict[str, Any], 
                               technical_indicators: Dict[str, float], 
                               position_size: int = 100) -> Dict[str, Any]:
        """Generate enhanced signal with algorithmic execution insights."""
        try:
            # Generate base signal
            base_signal = self.generate_signal(symbol, market_data, technical_indicators)
            
            # Convert to dict for enhancement
            signal_data = {
                "symbol": symbol,
                "signal": base_signal.signal,
                "strength": base_signal.strength,
                "confidence": base_signal.confidence,
                "position_size": position_size,
                "technical_score": base_signal.technical_score,
                "momentum_score": base_signal.momentum_score,
                "volume_score": base_signal.volume_score,
                "indicators": base_signal.indicators,
                "reasoning": base_signal.reasoning
            }
            
            # Enhance with algorithmic insights
            enhanced_signal = self.algo_analyzer.enhance_signal_with_algo_insights(
                signal_data, market_data
            )
            
            self.logger.info(f"Generated enhanced signal for {symbol}: {enhanced_signal['signal']} "
                           f"with {enhanced_signal['recommended_algorithm']} algorithm")
            
            return enhanced_signal
            
        except Exception as e:
            self.logger.error(f"Error generating enhanced signal for {symbol}: {e}")
            # Return basic signal without enhancement
            base_signal = self.generate_signal(symbol, market_data, technical_indicators)
            return {
                "symbol": symbol,
                "signal": base_signal.signal,
                "strength": base_signal.strength,
                "confidence": base_signal.confidence,
                "position_size": position_size,
                "recommended_algorithm": "VWAP",  # Safe default
                "error": str(e)
            }
    
    def calculate_price_targets(self, current_price: float, signal: str, 
                              technical_indicators: Dict[str, float]) -> Tuple[float, float]:
        """Calculate target price and stop loss based on technical analysis."""
        try:
            if signal == "BUY":
                # Target: Upper Bollinger Band or resistance level
                bb_upper = technical_indicators.get('bb_upper', current_price * 1.04)
                target_price = min(bb_upper, current_price * 1.08)  # Max 8% target
                
                # Stop loss: Lower Bollinger Band or support level
                bb_lower = technical_indicators.get('bb_lower', current_price * 0.96)
                stop_loss = max(bb_lower, current_price * 0.95)  # Max 5% stop loss
                
            elif signal == "SELL":
                # Target: Lower Bollinger Band or support level
                bb_lower = technical_indicators.get('bb_lower', current_price * 0.96)
                target_price = max(bb_lower, current_price * 0.92)  # Max 8% target
                
                # Stop loss: Upper Bollinger Band or resistance level
                bb_upper = technical_indicators.get('bb_upper', current_price * 1.04)
                stop_loss = min(bb_upper, current_price * 1.05)  # Max 5% stop loss
                
            else:  # HOLD
                target_price = current_price
                stop_loss = current_price * 0.93  # 7% stop loss for holds
            
            return target_price, stop_loss
            
        except Exception as e:
            self.logger.error(f"Price target calculation failed: {e}")
            return current_price, current_price * 0.95
    
    def calculate_position_sizing(self, signal_strength: float, current_price: float, 
                                portfolio_value: float = 100000) -> int:
        """Calculate position size based on signal strength and risk management."""
        try:
            # Base position as percentage of portfolio
            base_position_pct = 0.08  # 8% base position for strong signals
            
            # Adjust based on signal strength
            adjusted_pct = base_position_pct * signal_strength * 1.5
            
            # Calculate shares
            position_value = portfolio_value * adjusted_pct
            shares = int(position_value / current_price)
            
            # Minimum and maximum position limits
            min_shares = 10
            max_shares = int(portfolio_value * 0.2 / current_price)  # Max 20% of portfolio
            
            return max(min_shares, min(shares, max_shares))
            
        except Exception as e:
            self.logger.error(f"Position sizing calculation failed: {e}")
            return 100  # Default position
    
    def generate_enhanced_trading_signal(self, symbol: str, market_data: Dict[str, Any], 
                                  technical_indicators: Dict[str, float] = None, 
                                  position_size: int = 100) -> Dict[str, Any]:
        """Alias for generate_enhanced_signal to maintain API compatibility."""
        # Extract technical indicators from market_data if not provided
        if technical_indicators is None:
            technical_indicators = {}
            if 'historical_data' in market_data and not market_data['historical_data'].empty:
                # Try to extract indicators from historical data
                hist_data = market_data['historical_data']
                if 'rsi' in hist_data.columns:
                    technical_indicators['rsi'] = float(hist_data['rsi'].iloc[-1])
                if 'macd_line' in hist_data.columns:
                    technical_indicators['macd'] = float(hist_data['macd_line'].iloc[-1])
                if 'macd_signal' in hist_data.columns:
                    technical_indicators['macd_signal'] = float(hist_data['macd_signal'].iloc[-1])
                if 'macd_histogram' in hist_data.columns:
                    technical_indicators['macd_histogram'] = float(hist_data['macd_histogram'].iloc[-1])
                if 'bb_upper' in hist_data.columns:
                    technical_indicators['bb_upper'] = float(hist_data['bb_upper'].iloc[-1])
                if 'bb_lower' in hist_data.columns:
                    technical_indicators['bb_lower'] = float(hist_data['bb_lower'].iloc[-1])
                if 'bb_middle' in hist_data.columns:
                    technical_indicators['bb_middle'] = float(hist_data['bb_middle'].iloc[-1])
                
        # Call the original method
        return self.generate_enhanced_signal(symbol, market_data, technical_indicators, position_size)

    def generate_recommendation(self, signal_result: SignalResult) -> Dict[str, Any]:
        """Generate trading recommendation based on signal analysis."""
        try:
            # Adjust score based on confidence
            adjusted_score = signal_result.strength * signal_result.confidence
            
            if adjusted_score >= 0.75:
                action = "strong_buy" if signal_result.signal == "BUY" else "strong_sell"
                strength = "high"
            elif adjusted_score >= 0.60:
                action = signal_result.signal.lower()
                strength = "medium"
            elif adjusted_score >= 0.40:
                action = "hold"
                strength = "low"
            elif adjusted_score >= 0.25:
                action = "sell" if signal_result.signal == "BUY" else "buy"
                strength = "medium"
            else:
                action = "strong_sell" if signal_result.signal == "BUY" else "strong_buy"
                strength = "high"
            
            return {
                "action": action,
                "strength": strength,
                "score": signal_result.strength,
                "confidence": signal_result.confidence,
                "adjusted_score": adjusted_score,
                "reasoning": signal_result.reasoning
            }
            
        except Exception as e:
            self.logger.error(f"Error generating recommendation: {e}")
            return {"action": "hold", "strength": "low", "score": 0.5, "reasoning": "Error in analysis"}
