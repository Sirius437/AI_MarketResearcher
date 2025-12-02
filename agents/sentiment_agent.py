"""Sentiment analysis agent for cryptocurrency trading."""

import logging
from typing import Dict, List, Optional, Any
import re
from datetime import datetime, timedelta

from .base_agent import BaseAgent
from config.settings import MarketResearcherConfig

logger = logging.getLogger(__name__)


class SentimentAgent(BaseAgent):
    """Agent specialized in market sentiment analysis."""
    
    def __init__(self, llm_client, prompt_manager, config: MarketResearcherConfig):
        """Initialize sentiment analysis agent."""
        super().__init__(llm_client, prompt_manager, config, "Sentiment Analyst")
        
    def get_agent_type(self) -> str:
        """Return the agent type identifier."""
        return "sentiment"
    
    def analyze(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform sentiment analysis for the given symbol."""
        try:
            if not self._validate_analysis_data(data):
                return {
                    "success": False,
                    "error": "Invalid input data",
                    "agent": self.agent_name
                }
            
            # Extract sentiment data
            sentiment_data = self._extract_sentiment_data(data)
            
            # Calculate sentiment metrics
            sentiment_metrics = self._calculate_sentiment_metrics(sentiment_data)
            
            # Create analysis prompt
            messages = self.prompt_manager.create_sentiment_analysis_prompt(
                symbol=symbol,
                sentiment_data={**sentiment_data, **sentiment_metrics}
            )
            
            # Execute LLM analysis
            llm_result = self._execute_llm_analysis(messages)
            
            if llm_result["success"]:
                # Use raw LLM response content for analysis
                raw_content = llm_result["raw_response"]
                
                # Extract sentiment signals from raw content
                sentiment_signals = self._extract_sentiment_signals(raw_content)
                
                # Calculate overall sentiment score
                sentiment_metrics = {
                    "social_sentiment": 0.1,  # From symbol data
                    "fear_greed_index": 45,
                    "fear_greed_label": "Neutral"
                }
                sentiment_score = self._calculate_sentiment_score(sentiment_metrics, sentiment_signals)
                
                # Extract confidence score from raw content
                confidence = self._extract_confidence_score(raw_content)
                
                analysis_result = {
                    "success": True,
                    "agent": self.agent_name,
                    "symbol": symbol,
                    "analysis": raw_content,  # Use raw LLM content
                    "summary": raw_content[:300] + "..." if len(raw_content) > 300 else raw_content,
                    "sentiment_signals": sentiment_signals,
                    "sentiment_score": sentiment_score,
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
            logger.error(f"Error in sentiment analysis for {symbol}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.agent_name,
                "symbol": symbol
            }
    
    def _extract_sentiment_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract sentiment-related data from input."""
        try:
            sentiment_data = {
                "current_price": data.get("current_price", data.get("price", 0)),
                "recent_performance": self._calculate_recent_performance(data),
                "social_mentions": data.get("social_mentions", 0),
                "sentiment_score": data.get("sentiment_score", 0),
                "fear_greed_index": data.get("fear_greed_index", 50),
                "news_headlines": data.get("news_headlines", []),
                "reddit_activity": data.get("reddit_activity", "Low"),
                "twitter_trends": data.get("twitter_trends", []),
                "technical_context": data.get("technical_context", "Technical analysis data not available"),
                "technical_indicators": data.get("technical_indicators", {}),
                "ohlcv_30d": data.get("ohlcv_30d", {})
            }
            
            # Extract market sentiment from order book data
            if "order_book_data" in data:
                sentiment_data.update(self._analyze_order_book_sentiment(data["order_book_data"]))
            
            # Extract volume sentiment
            if "volume_data" in data:
                sentiment_data.update(self._analyze_volume_sentiment(data["volume_data"]))
            
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Error extracting sentiment data: {e}")
            return {"current_price": 0, "sentiment_score": 0}
    
    def _calculate_recent_performance(self, data: Dict[str, Any]) -> str:
        """Calculate recent price performance description."""
        try:
            change_24h = data.get("price_change_24h", data.get("change_24h", 0))
            
            if change_24h > 10:
                return "Very Positive (+10%+)"
            elif change_24h > 5:
                return "Positive (+5% to +10%)"
            elif change_24h > 2:
                return "Slightly Positive (+2% to +5%)"
            elif change_24h > -2:
                return "Neutral (-2% to +2%)"
            elif change_24h > -5:
                return "Slightly Negative (-2% to -5%)"
            elif change_24h > -10:
                return "Negative (-5% to -10%)"
            else:
                return "Very Negative (-10%+)"
                
        except Exception as e:
            logger.error(f"Error calculating recent performance: {e}")
            return "Unknown"
    
    def _analyze_order_book_sentiment(self, order_book_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment from order book data."""
        try:
            bid_ask_ratio = order_book_data.get("bid_ask_ratio", 1.0)
            buy_sell_ratio = order_book_data.get("buy_sell_ratio", 1.0)
            
            # Interpret ratios
            if bid_ask_ratio > 1.2:
                order_book_sentiment = "Bullish (Strong Bid Support)"
            elif bid_ask_ratio > 1.05:
                order_book_sentiment = "Slightly Bullish"
            elif bid_ask_ratio < 0.8:
                order_book_sentiment = "Bearish (Weak Bid Support)"
            elif bid_ask_ratio < 0.95:
                order_book_sentiment = "Slightly Bearish"
            else:
                order_book_sentiment = "Neutral"
            
            return {
                "order_book_sentiment": order_book_sentiment,
                "bid_ask_ratio": bid_ask_ratio,
                "buy_sell_ratio": buy_sell_ratio
            }
            
        except Exception as e:
            logger.error(f"Error analyzing order book sentiment: {e}")
            return {"order_book_sentiment": "Unknown"}
    
    def _analyze_volume_sentiment(self, volume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment from volume patterns."""
        try:
            current_volume = volume_data.get("current_volume", 0)
            avg_volume = volume_data.get("average_volume", 0)
            
            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
                
                if volume_ratio > 2.0:
                    volume_sentiment = "Very High Volume (Strong Interest)"
                elif volume_ratio > 1.5:
                    volume_sentiment = "High Volume (Increased Interest)"
                elif volume_ratio > 0.8:
                    volume_sentiment = "Normal Volume"
                elif volume_ratio > 0.5:
                    volume_sentiment = "Low Volume (Decreased Interest)"
                else:
                    volume_sentiment = "Very Low Volume (Minimal Interest)"
            else:
                volume_sentiment = "Unknown Volume Pattern"
            
            return {
                "volume_sentiment": volume_sentiment,
                "volume_ratio": volume_ratio if avg_volume > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volume sentiment: {e}")
            return {"volume_sentiment": "Unknown"}
    
    def _calculate_sentiment_metrics(self, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive sentiment metrics."""
        try:
            metrics = {}
            
            # Social sentiment score (normalize to -1 to 1)
            raw_sentiment = sentiment_data.get("sentiment_score", 0)
            if isinstance(raw_sentiment, (int, float)):
                if -1 <= raw_sentiment <= 1:
                    metrics["normalized_sentiment"] = raw_sentiment
                elif 0 <= raw_sentiment <= 100:
                    metrics["normalized_sentiment"] = (raw_sentiment - 50) / 50
                else:
                    metrics["normalized_sentiment"] = 0
            else:
                metrics["normalized_sentiment"] = 0
            
            # Fear & Greed interpretation
            fear_greed = sentiment_data.get("fear_greed_index", 50)
            if fear_greed >= 75:
                metrics["fear_greed_label"] = "Extreme Greed"
            elif fear_greed >= 55:
                metrics["fear_greed_label"] = "Greed"
            elif fear_greed >= 45:
                metrics["fear_greed_label"] = "Neutral"
            elif fear_greed >= 25:
                metrics["fear_greed_label"] = "Fear"
            else:
                metrics["fear_greed_label"] = "Extreme Fear"
            
            # Social activity level
            mentions = sentiment_data.get("social_mentions", 0)
            if mentions > 1000:
                metrics["social_activity"] = "Very High"
            elif mentions > 500:
                metrics["social_activity"] = "High"
            elif mentions > 100:
                metrics["social_activity"] = "Medium"
            elif mentions > 10:
                metrics["social_activity"] = "Low"
            else:
                metrics["social_activity"] = "Very Low"
            
            # News sentiment analysis
            headlines = sentiment_data.get("news_headlines", [])
            if headlines:
                metrics["news_sentiment"] = self._analyze_news_sentiment(headlines)
            else:
                metrics["news_sentiment"] = "Neutral"
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating sentiment metrics: {e}")
            return {"normalized_sentiment": 0}
    
    def _analyze_news_sentiment(self, headlines: List[str]) -> str:
        """Analyze sentiment from news headlines."""
        try:
            if not headlines:
                return "Neutral"
            
            positive_keywords = [
                'surge', 'rally', 'bullish', 'gains', 'rise', 'up', 'positive', 
                'breakthrough', 'adoption', 'partnership', 'upgrade', 'launch'
            ]
            
            negative_keywords = [
                'crash', 'dump', 'bearish', 'losses', 'fall', 'down', 'negative',
                'hack', 'ban', 'regulation', 'concern', 'warning', 'decline'
            ]
            
            positive_count = 0
            negative_count = 0
            
            for headline in headlines[:10]:  # Analyze top 10 headlines
                headline_lower = headline.lower()
                positive_count += sum(1 for word in positive_keywords if word in headline_lower)
                negative_count += sum(1 for word in negative_keywords if word in headline_lower)
            
            if positive_count > negative_count * 1.5:
                return "Very Positive"
            elif positive_count > negative_count:
                return "Positive"
            elif negative_count > positive_count * 1.5:
                return "Very Negative"
            elif negative_count > positive_count:
                return "Negative"
            else:
                return "Neutral"
                
        except Exception as e:
            logger.error(f"Error analyzing news sentiment: {e}")
            return "Neutral"
    
    def _extract_sentiment_signals(self, analysis: str) -> Dict[str, Any]:
        """Extract sentiment signals from LLM analysis."""
        try:
            full_text = analysis.lower() if isinstance(analysis, str) else str(analysis).lower()
            
            signals = {
                "overall_sentiment": "neutral",
                "social_sentiment": "neutral",
                "market_psychology": "neutral",
                "sentiment_strength": "moderate",
                "contrarian_signal": False
            }
            
            # Extract overall sentiment
            if any(phrase in full_text for phrase in ["very bullish", "extremely positive"]):
                signals["overall_sentiment"] = "very_bullish"
            elif "bullish" in full_text or "positive" in full_text:
                signals["overall_sentiment"] = "bullish"
            elif any(phrase in full_text for phrase in ["very bearish", "extremely negative"]):
                signals["overall_sentiment"] = "very_bearish"
            elif "bearish" in full_text or "negative" in full_text:
                signals["overall_sentiment"] = "bearish"
            
            # Extract sentiment strength
            if any(word in full_text for word in ["strong", "intense", "extreme"]):
                signals["sentiment_strength"] = "strong"
            elif any(word in full_text for word in ["weak", "mild", "slight"]):
                signals["sentiment_strength"] = "weak"
            
            # Check for contrarian indicators
            contrarian_phrases = ["extreme", "euphoria", "panic", "capitulation", "overextended"]
            if any(phrase in full_text for phrase in contrarian_phrases):
                signals["contrarian_signal"] = True
            
            return signals
            
        except Exception as e:
            logger.error(f"Error extracting sentiment signals: {e}")
            return {"overall_sentiment": "neutral"}
    
    def _calculate_sentiment_score(
        self, 
        metrics: Dict[str, Any], 
        signals: Dict[str, Any]
    ) -> float:
        """Calculate overall sentiment score (0-100)."""
        try:
            score = 50  # Neutral starting point
            
            # Normalized sentiment contribution
            normalized_sentiment = metrics.get("normalized_sentiment", 0)
            score += normalized_sentiment * 25  # -25 to +25 range
            
            # Fear & Greed contribution
            fear_greed_label = metrics.get("fear_greed_label", "Neutral")
            fear_greed_scores = {
                "Extreme Greed": 20,
                "Greed": 10,
                "Neutral": 0,
                "Fear": -10,
                "Extreme Fear": -20
            }
            score += fear_greed_scores.get(fear_greed_label, 0)
            
            # Overall sentiment signal contribution
            sentiment_signal = signals.get("overall_sentiment", "neutral")
            sentiment_scores = {
                "very_bullish": 20,
                "bullish": 10,
                "neutral": 0,
                "bearish": -10,
                "very_bearish": -20
            }
            score += sentiment_scores.get(sentiment_signal, 0)
            
            # News sentiment contribution
            news_sentiment = metrics.get("news_sentiment", "Neutral")
            news_scores = {
                "Very Positive": 15,
                "Positive": 7,
                "Neutral": 0,
                "Negative": -7,
                "Very Negative": -15
            }
            score += news_scores.get(news_sentiment, 0)
            
            # Contrarian adjustment
            if signals.get("contrarian_signal", False):
                # Reverse extreme scores
                if score > 75:
                    score = 100 - score
                elif score < 25:
                    score = 100 - score
            
            # Ensure score is within bounds
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating sentiment score: {e}")
            return 50.0
    
    # Removed _generate_recommendation - Trading Agent handles all trading decisions
    
    # Removed _generate_sentiment_recommendation - Trading Agent handles all trading decisions
    
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
    
    def get_sentiment_summary(self, symbol: str) -> Dict[str, Any]:
        """Get summary of recent sentiment analysis."""
        try:
            if not self.last_analysis:
                return {"error": "No recent analysis available"}
            
            return {
                "symbol": symbol,
                "last_analysis": self.last_analysis.get("timestamp"),
                "sentiment_score": self.last_analysis.get("sentiment_score", 0),
                "recommendation": self.last_analysis.get("recommendation", {}),
                "key_metrics": {
                    "overall_sentiment": self.last_analysis.get("sentiment_signals", {}).get("overall_sentiment"),
                    "social_activity": self.last_analysis.get("sentiment_metrics", {}).get("social_activity"),
                    "fear_greed": self.last_analysis.get("sentiment_metrics", {}).get("fear_greed_label"),
                    "news_sentiment": self.last_analysis.get("sentiment_metrics", {}).get("news_sentiment")
                },
                "confidence": self.last_analysis.get("confidence", 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting sentiment summary: {e}")
            return {"error": str(e)}
