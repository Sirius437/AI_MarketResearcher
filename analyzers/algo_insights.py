"""
Algorithmic Trading Insights Module

This module extracts trading insights from Interactive Brokers algorithmic parameters
and integrates them into the signal generation process for enhanced trading decisions.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class MarketCondition(Enum):
    """Market condition classifications for algorithm selection."""
    LOW_VOLATILITY_HIGH_VOLUME = "low_vol_high_vol"
    HIGH_VOLATILITY = "high_vol"
    LOW_VOLUME = "low_vol"
    STRONG_TREND = "strong_trend"
    SIDEWAYS = "sideways"
    HIGH_VOLUME = "high_vol"
    LOW_VOLATILITY = "low_vol"
    MEDIUM_VOLATILITY = "medium_vol"

class AlgorithmSuitability(Enum):
    """Algorithm suitability ratings."""
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"

@dataclass
class AlgorithmInsight:
    """Represents insights about a specific algorithmic trading strategy."""
    algorithm: str
    market_impact: str
    execution_speed: str
    stealth_level: str
    volume_participation: float
    suitability_score: float
    recommended_conditions: List[MarketCondition]
    risk_profile: str

class AlgorithmicInsightsAnalyzer:
    """Analyzes algorithmic parameters to provide trading insights and recommendations."""
    
    def __init__(self):
        self.algorithm_profiles = self._initialize_algorithm_profiles()
        self.market_condition_weights = self._initialize_condition_weights()
    
    def _initialize_algorithm_profiles(self) -> Dict[str, AlgorithmInsight]:
        """Initialize comprehensive algorithm profiles for all 16+ IB algorithms."""
        return {
            "VWAP": AlgorithmInsight(
                algorithm="VWAP",
                market_impact="LOW",
                execution_speed="MODERATE",
                stealth_level="HIGH",
                volume_participation=0.1,
                suitability_score=0.8,
                recommended_conditions=[MarketCondition.HIGH_VOLUME, MarketCondition.HIGH_VOLATILITY],
                risk_profile="CONSERVATIVE"
            ),
            "TWAP": AlgorithmInsight(
                algorithm="TWAP",
                market_impact="LOW",
                execution_speed="SLOW_STEADY",
                stealth_level="HIGH",
                volume_participation=0.05,
                suitability_score=0.7,
                recommended_conditions=[MarketCondition.LOW_VOLATILITY, MarketCondition.SIDEWAYS],
                risk_profile="CONSERVATIVE"
            ),
            "ArrivalPx": AlgorithmInsight(
                algorithm="ArrivalPx",
                market_impact="MEDIUM",
                execution_speed="FAST",
                stealth_level="MEDIUM",
                volume_participation=0.15,
                suitability_score=0.9,
                recommended_conditions=[MarketCondition.STRONG_TREND, MarketCondition.HIGH_VOLATILITY],
                risk_profile="AGGRESSIVE"
            ),
            "Adaptive": AlgorithmInsight(
                algorithm="Adaptive",
                market_impact="MEDIUM",
                execution_speed="ADAPTIVE",
                stealth_level="MEDIUM",
                volume_participation=0.08,
                suitability_score=0.85,
                recommended_conditions=[MarketCondition.LOW_VOLATILITY],
                risk_profile="BALANCED"
            ),
            "PctVol": AlgorithmInsight(
                algorithm="PctVol",
                market_impact="HIGH",
                execution_speed="FAST",
                stealth_level="LOW",
                volume_participation=0.2,
                suitability_score=0.75,
                recommended_conditions=[MarketCondition.HIGH_VOLUME],
                risk_profile="AGGRESSIVE"
            ),
            "DarkIce": AlgorithmInsight(
                algorithm="DarkIce",
                market_impact="VERY_LOW",
                execution_speed="SLOW_STEADY",
                stealth_level="VERY_HIGH",
                volume_participation=0.03,
                suitability_score=0.9,
                recommended_conditions=[MarketCondition.HIGH_VOLUME, MarketCondition.STRONG_TREND],
                risk_profile="STEALTH"
            ),
            "BalanceImpact": AlgorithmInsight(
                algorithm="BalanceImpact",
                market_impact="LOW",
                execution_speed="MODERATE",
                stealth_level="HIGH",
                volume_participation=0.07,
                suitability_score=0.8,
                recommended_conditions=[MarketCondition.LOW_VOLATILITY, MarketCondition.SIDEWAYS],
                risk_profile="BALANCED"
            ),
            "MinImpact": AlgorithmInsight(
                algorithm="MinImpact",
                market_impact="VERY_LOW",
                execution_speed="VERY_SLOW",
                stealth_level="VERY_HIGH",
                volume_participation=0.02,
                suitability_score=0.85,
                recommended_conditions=[MarketCondition.LOW_VOLUME, MarketCondition.LOW_VOLATILITY],
                risk_profile="ULTRA_CONSERVATIVE"
            ),
            "ClosePx": AlgorithmInsight(
                algorithm="ClosePx",
                market_impact="MEDIUM",
                execution_speed="FAST",
                stealth_level="LOW",
                volume_participation=0.25,
                suitability_score=0.7,
                recommended_conditions=[MarketCondition.STRONG_TREND],
                risk_profile="AGGRESSIVE"
            ),
            "PctVolPx": AlgorithmInsight(
                algorithm="PctVolPx",
                market_impact="MEDIUM",
                execution_speed="MODERATE",
                stealth_level="MEDIUM",
                volume_participation=0.12,
                suitability_score=0.75,
                recommended_conditions=[MarketCondition.HIGH_VOLUME, MarketCondition.HIGH_VOLATILITY],
                risk_profile="MODERATE"
            ),
            "PctVolSz": AlgorithmInsight(
                algorithm="PctVolSz",
                market_impact="MEDIUM",
                execution_speed="MODERATE",
                stealth_level="MEDIUM",
                volume_participation=0.15,
                suitability_score=0.75,
                recommended_conditions=[MarketCondition.HIGH_VOLUME],
                risk_profile="MODERATE"
            ),
            "PctVolTm": AlgorithmInsight(
                algorithm="PctVolTm",
                market_impact="MEDIUM",
                execution_speed="SLOW_STEADY",
                stealth_level="HIGH",
                volume_participation=0.1,
                suitability_score=0.8,
                recommended_conditions=[MarketCondition.HIGH_VOLUME, MarketCondition.SIDEWAYS],
                risk_profile="CONSERVATIVE"
            ),
            "JefferiesVWAP": AlgorithmInsight(
                algorithm="JefferiesVWAP",
                market_impact="LOW",
                execution_speed="MODERATE",
                stealth_level="HIGH",
                volume_participation=0.08,
                suitability_score=0.85,
                recommended_conditions=[MarketCondition.HIGH_VOLUME, MarketCondition.HIGH_VOLATILITY],
                risk_profile="CONSERVATIVE"
            ),
            "CSFBInline": AlgorithmInsight(
                algorithm="CSFBInline",
                market_impact="LOW",
                execution_speed="FAST",
                stealth_level="MEDIUM",
                volume_participation=0.12,
                suitability_score=0.8,
                recommended_conditions=[MarketCondition.STRONG_TREND, MarketCondition.HIGH_VOLUME],
                risk_profile="MODERATE"
            ),
            "QBStrobe": AlgorithmInsight(
                algorithm="QBStrobe",
                market_impact="HIGH",
                execution_speed="VERY_FAST",
                stealth_level="LOW",
                volume_participation=0.3,
                suitability_score=0.9,
                recommended_conditions=[MarketCondition.STRONG_TREND, MarketCondition.HIGH_VOLATILITY],
                risk_profile="VERY_AGGRESSIVE"
            ),
            "Accumulate": AlgorithmInsight(
                algorithm="Accumulate",
                market_impact="VERY_LOW",
                execution_speed="VERY_SLOW",
                stealth_level="VERY_HIGH",
                volume_participation=0.01,
                suitability_score=0.8,
                recommended_conditions=[MarketCondition.LOW_VOLATILITY, MarketCondition.SIDEWAYS],
                risk_profile="ULTRA_CONSERVATIVE"
            )
        }
    
    def _initialize_condition_weights(self) -> Dict[str, float]:
        """Initialize weights for different market conditions in algorithm selection."""
        return {
            "volatility_weight": 0.4,
            "volume_weight": 0.3,
            "trend_weight": 0.2,
            "liquidity_weight": 0.1
        }
    
    def analyze_market_conditions(self, market_data: Dict[str, Any]) -> List[MarketCondition]:
        """Analyze current market conditions to determine appropriate algorithm selection."""
        conditions = []
        
        # Extract market metrics
        volatility = market_data.get("volatility", 0.02)
        volume = market_data.get("volume", 1000000)
        avg_volume = market_data.get("avg_volume", 1000000)
        price_change = market_data.get("price_change_pct", 0.0)
        
        # Classify volatility
        if volatility < 0.015:
            vol_condition = "LOW"
        elif volatility > 0.04:
            vol_condition = "HIGH"
        else:
            vol_condition = "MEDIUM"
        
        # Classify volume
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
        if volume_ratio > 1.5:
            vol_level = "HIGH"
        elif volume_ratio < 0.7:
            vol_level = "LOW"
        else:
            vol_level = "NORMAL"
        
        # Classify trend
        if abs(price_change) > 0.03:
            trend = "STRONG_TREND"
        else:
            trend = "SIDEWAYS"
        
        # Map to market conditions
        if vol_condition == "LOW" and vol_level == "HIGH":
            conditions.append(MarketCondition.LOW_VOLATILITY_HIGH_VOLUME)
        
        if vol_condition == "HIGH":
            conditions.append(MarketCondition.HIGH_VOLATILITY)
        
        if vol_level == "LOW":
            conditions.append(MarketCondition.LOW_VOLUME)
        
        if trend == "STRONG_TREND":
            conditions.append(MarketCondition.STRONG_TREND)
        else:
            conditions.append(MarketCondition.SIDEWAYS)
        
        return conditions
    
    def recommend_algorithms(self, market_conditions: List[MarketCondition], 
                           signal_strength: float = 0.5, 
                           confidence: float = 0.5,
                           trend_strength: float = 0.5,
                           stealth_required: bool = False) -> List[Tuple[str, float, str]]:
        """Enhanced algorithm recommendation with comprehensive market analysis."""
        recommendations = []
        
        # Convert market conditions to simplified format for enhanced logic
        volatility = "medium"
        volume_ratio = 1.0
        
        for condition in market_conditions:
            if condition == MarketCondition.HIGH_VOLATILITY:
                volatility = "high"
            elif condition == MarketCondition.LOW_VOLATILITY:
                volatility = "low"
            elif condition == MarketCondition.HIGH_VOLUME:
                volume_ratio = 2.0
            elif condition == MarketCondition.LOW_VOLUME:
                volume_ratio = 0.5
        
        # Enhanced algorithm selection logic from test script
        selected_algo = self._select_optimal_algorithm(
            volatility, volume_ratio, signal_strength, confidence, 
            trend_strength, stealth_required
        )
        
        # Score all algorithms based on suitability
        for algo_name, profile in self.algorithm_profiles.items():
            # Base suitability score
            base_score = profile.suitability_score
            
            # Condition matching bonus
            condition_bonus = 0.0
            for condition in market_conditions:
                if condition in profile.recommended_conditions:
                    condition_bonus += 0.2
            
            # Signal strength alignment
            signal_bonus = 0.0
            if signal_strength > 0.8 and profile.execution_speed in ["FAST", "VERY_FAST"]:
                signal_bonus += 0.15
            elif signal_strength < 0.3 and profile.stealth_level in ["HIGH", "VERY_HIGH"]:
                signal_bonus += 0.1
            
            # Stealth requirement bonus
            stealth_bonus = 0.0
            if stealth_required and profile.stealth_level in ["HIGH", "VERY_HIGH"]:
                stealth_bonus += 0.2
            
            # Selected algorithm gets highest score
            selection_bonus = 0.3 if algo_name == selected_algo else 0.0
            
            # Calculate final score
            final_score = min(1.0, base_score * 0.4 + condition_bonus * 0.2 + 
                             signal_bonus * 0.15 + stealth_bonus * 0.15 + selection_bonus * 0.1)
            
            # Determine rating
            if final_score >= 0.85:
                rating = AlgorithmSuitability.EXCELLENT.value
            elif final_score >= 0.7:
                rating = AlgorithmSuitability.GOOD.value
            elif final_score >= 0.5:
                rating = AlgorithmSuitability.FAIR.value
            else:
                rating = AlgorithmSuitability.POOR.value
            
            recommendations.append((algo_name, final_score, rating))
        
        # Sort by score (descending)
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations
    
    def _select_optimal_algorithm(self, volatility: str, volume_ratio: float, 
                                signal_strength: float, confidence: float,
                                trend_strength: float, stealth_required: bool) -> str:
        """Select optimal algorithm using enhanced logic from test script."""
        # Ultra-stealth requirements (large orders, sensitive positions)
        if stealth_required or signal_strength > 0.9:
            if volume_ratio < 0.5:  # Low volume = ultra stealth
                return "MinImpact"
            elif volume_ratio > 1.5:  # High volume = dark pools
                return "DarkIce"
            else:
                return "Accumulate"
        
        # High volatility + high signal strength = aggressive execution
        if volatility == 'high' and signal_strength > 0.8:
            if trend_strength > 0.7:  # Strong trend = very aggressive
                return "QBStrobe"
            elif volume_ratio > 2.0:  # High volume = close price
                return "ClosePx"
            elif volume_ratio > 1.5:  # Medium-high volume = VWAP variants
                return "JefferiesVWAP"
            else:
                return "ArrivalPx"
        
        # High volume conditions (sophisticated volume algorithms)
        elif volume_ratio > 2.5:
            if volatility == 'high':
                return "PctVolPx"  # Price-sensitive volume
            elif trend_strength > 0.6:
                return "CSFBInline"  # Trend-following
            else:
                return "PctVolSz"  # Size-sensitive volume
        
        # Medium-high volume conditions
        elif volume_ratio > 1.5:
            if volatility == 'low':
                return "PctVolTm"  # Time-sensitive volume
            else:
                return "VWAP"  # Standard VWAP
        
        # Low volatility conditions (conservative algorithms)
        elif volatility == 'low':
            if confidence > 0.8:
                return "Adaptive"  # High confidence = adaptive
            elif volume_ratio < 0.7:
                return "BalanceImpact"  # Low volume = balanced
            else:
                return "TWAP"  # Standard TWAP
        
        # Strong trend conditions
        elif trend_strength > 0.7:
            if signal_strength > 0.7:
                return "ArrivalPx"  # Strong signal + trend = arrival
            else:
                return "CSFBInline"  # Trend following
        
        # Medium conditions (balanced approach)
        elif confidence > 0.7:
            return "Adaptive"
        elif volume_ratio > 1.2:
            return "PctVol"
        
        # Default to TWAP for uncertain conditions
        return "TWAP"
    
    def get_execution_insights(self, algorithm: str, position_size: int, 
                             market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed execution insights for a specific algorithm."""
        if algorithm not in self.algorithm_profiles:
            return {"error": f"Unknown algorithm: {algorithm}"}
        
        profile = self.algorithm_profiles[algorithm]
        avg_volume = market_data.get("avg_volume", 1000000)
        
        # Calculate participation rate impact
        participation_impact = (position_size * profile.volume_participation) / avg_volume
        
        # Enhanced execution time estimation
        if profile.execution_speed == "VERY_FAST":
            est_time_minutes = 2
        elif profile.execution_speed == "FAST":
            est_time_minutes = 5
        elif profile.execution_speed == "MODERATE":
            est_time_minutes = 30
        elif profile.execution_speed == "SLOW_STEADY":
            est_time_minutes = 120
        elif profile.execution_speed == "VERY_SLOW":
            est_time_minutes = 240
        elif profile.execution_speed == "ADAPTIVE":
            est_time_minutes = 45
        else:
            est_time_minutes = 60
        
        # Enhanced market impact estimation
        if profile.market_impact == "VERY_LOW":
            impact_bps = 1
        elif profile.market_impact == "LOW":
            impact_bps = 2
        elif profile.market_impact == "MEDIUM":
            impact_bps = 5
        elif profile.market_impact == "HIGH":
            impact_bps = 8
        elif profile.market_impact == "VERY_HIGH":
            impact_bps = 12
        else:
            impact_bps = 3
        
        return {
            "algorithm": algorithm,
            "estimated_execution_time_minutes": est_time_minutes,
            "estimated_market_impact_bps": impact_bps,
            "participation_rate": profile.volume_participation,
            "participation_impact": participation_impact,
            "stealth_rating": profile.stealth_level,
            "risk_profile": profile.risk_profile,
            "suitability_for_size": "HIGH" if participation_impact < 0.1 else "MEDIUM" if participation_impact < 0.2 else "LOW"
        }
    
    def enhance_signal_with_algo_insights(self, signal_data: Dict[str, Any], 
                                        market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance trading signal with algorithmic execution insights."""
        # Analyze market conditions
        conditions = self.analyze_market_conditions(market_data)
        
        # Get signal strength
        signal_strength = signal_data.get("confidence", 0.5)
        position_size = signal_data.get("position_size", 100)
        
        # Get algorithm recommendations
        recommendations = self.recommend_algorithms(conditions, signal_strength)
        
        # Select top algorithm
        if recommendations:
            top_algo, score, rating = recommendations[0]
            execution_insights = self.get_execution_insights(top_algo, position_size, market_data)
        else:
            top_algo = "VWAP"  # Default fallback
            execution_insights = self.get_execution_insights(top_algo, position_size, market_data)
        
        # Enhance signal data
        enhanced_signal = signal_data.copy()
        enhanced_signal.update({
            "recommended_algorithm": top_algo,
            "algorithm_recommendations": recommendations[:3],  # Top 3
            "market_conditions": [c.value for c in conditions],
            "execution_insights": execution_insights,
            "algo_confidence": score if recommendations else 0.5
        })
        
        logger.info(f"Enhanced signal with algorithm insights: {top_algo} (score: {score:.2f})")
        return enhanced_signal

def create_algo_insights_analyzer() -> AlgorithmicInsightsAnalyzer:
    """Factory function to create an AlgorithmicInsightsAnalyzer instance."""
    return AlgorithmicInsightsAnalyzer()
