"""News analysis agent for cryptocurrency trading."""

import logging
from typing import Dict, List, Optional, Any
import re
from datetime import datetime, timedelta
import requests
import feedparser

from .base_agent import BaseAgent
from config.settings import MarketResearcherConfig, NEWS_SOURCES

logger = logging.getLogger(__name__)


class NewsAgent(BaseAgent):
    """Agent specialized in news and fundamental analysis."""
    
    def __init__(self, llm_client, prompt_manager, config: MarketResearcherConfig):
        """Initialize news analysis agent."""
        super().__init__(llm_client, prompt_manager, config, "News Analyst")
        self.news_sources = NEWS_SOURCES
        
        # Initialize Finnhub client for priority news access
        try:
            from data.finnhub_client import FinnhubClient
            finnhub_key = getattr(config, 'finnhub_api_key', None)
            if finnhub_key:
                self.finnhub_client = FinnhubClient(finnhub_key)
                logger.info("Finnhub client initialized for news analysis")
            else:
                self.finnhub_client = None
                logger.warning("Finnhub API key not found - using fallback news sources")
        except Exception as e:
            logger.warning(f"Failed to initialize Finnhub client: {e}")
            self.finnhub_client = None
        
    def get_agent_type(self) -> str:
        """Return the agent type identifier."""
        return "news"
    
    def analyze(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform news analysis for the given symbol."""
        try:
            if not self._validate_analysis_data(data):
                return {
                    "success": False,
                    "error": "Invalid input data",
                    "agent": self.agent_name
                }
            
            # Extract news data
            news_data = self._extract_news_data(symbol, data)
            
            # Fetch additional news if needed - prioritize Finnhub
            if not news_data.get("headlines") and self.config.enable_news_analysis:
                fresh_news = self._fetch_recent_news(symbol)
                news_data.update(fresh_news)
            
            # Analyze news impact
            news_impact = self._analyze_news_impact(news_data)
            
            # Create analysis prompt
            messages = self.prompt_manager.create_news_analysis_prompt(
                symbol=symbol,
                news_data={**news_data, **news_impact}
            )
            
            # Execute LLM analysis
            llm_result = self._execute_llm_analysis(messages)
            
            if llm_result["success"]:
                # Use raw LLM response content for analysis
                raw_content = llm_result["raw_response"]
                
                # Extract news signals from raw content
                news_signals = self._extract_news_signals(raw_content)
                
                # Calculate overall news impact score
                impact_analysis = {
                    "regulatory_impact": "neutral",
                    "adoption_impact": "neutral", 
                    "technical_impact": "neutral"
                }
                news_score = self._calculate_news_score(impact_analysis, news_signals)
                
                # Extract confidence score from raw content
                confidence = self._extract_confidence_score(raw_content)
                
                analysis_result = {
                    "success": True,
                    "agent": self.agent_name,
                    "symbol": symbol,
                    "analysis": raw_content,
                    "summary": raw_content[:300] + "..." if len(raw_content) > 300 else raw_content,
                    "news_signals": news_signals,
                    "news_score": news_score,
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
            logger.error(f"Error in news analysis for {symbol}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.agent_name,
                "symbol": symbol
            }
    
    def _extract_news_data(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract news-related data from input."""
        try:
            news_data = {
                "current_price": data.get("current_price", data.get("price", 0)),
                "market_cap_rank": data.get("market_cap_rank", "N/A"),
                "volume": data.get("volume", 0),
                "headlines": data.get("news_headlines", data.get("headlines", [])),
                "regulatory_news": data.get("regulatory_news", []),
                "partnerships": data.get("partnerships", []),
                "tech_updates": data.get("tech_updates", []),
                "market_events": data.get("market_events", [])
            }
            
            return news_data
            
        except Exception as e:
            logger.error(f"Error extracting news data: {e}")
            return {"current_price": 0, "headlines": []}
    
    def _fetch_recent_news(self, symbol: str) -> Dict[str, Any]:
        """Fetch recent news from configured sources with Finnhub priority."""
        try:
            all_headlines = []
            regulatory_news = []
            partnerships = []
            tech_updates = []
            
            # Extract base asset from symbol (e.g., BTC from BTCUSDT)
            base_asset = self._extract_base_asset(symbol)
            
            # Priority 1: Finnhub news (best quality, real-time)
            if self.finnhub_client:
                try:
                    logger.info(f"Fetching news from Finnhub for {symbol}")
                    finnhub_news = self._fetch_finnhub_news(symbol, base_asset)
                    if finnhub_news.get("headlines"):
                        all_headlines.extend(finnhub_news["headlines"])
                        regulatory_news.extend(finnhub_news.get("regulatory_news", []))
                        partnerships.extend(finnhub_news.get("partnerships", []))
                        tech_updates.extend(finnhub_news.get("tech_updates", []))
                        logger.info(f"Retrieved {len(finnhub_news['headlines'])} headlines from Finnhub")
                except Exception as e:
                    logger.warning(f"Finnhub news fetch failed: {e}")
            
            # Priority 2: RSS feeds (fallback if Finnhub insufficient)
            if len(all_headlines) < 5:  # Only fetch RSS if we need more news
                logger.info("Fetching additional news from RSS feeds")
                for feed_url in self.news_sources.get("crypto_news", []):
                    try:
                        headlines = self._fetch_rss_headlines(feed_url, base_asset)
                        all_headlines.extend(headlines)
                    except Exception as e:
                        logger.warning(f"Failed to fetch from {feed_url}: {e}")
                
                # Categorize RSS news
                for headline in all_headlines[len(finnhub_news.get("headlines", [])):]:
                    headline_lower = headline.lower()
                    
                    if any(word in headline_lower for word in ['regulation', 'sec', 'cftc', 'ban', 'legal']):
                        regulatory_news.append(headline)
                    elif any(word in headline_lower for word in ['partnership', 'collaboration', 'integration']):
                        partnerships.append(headline)
                    elif any(word in headline_lower for word in ['upgrade', 'update', 'fork', 'protocol']):
                        tech_updates.append(headline)
            
            return {
                "headlines": all_headlines[:15],  # Top 15 headlines (more with Finnhub)
                "regulatory_news": regulatory_news[:8],
                "partnerships": partnerships[:8],
                "tech_updates": tech_updates[:8],
                "market_events": []  # Could be expanded to include scheduled events
            }
            
        except Exception as e:
            logger.error(f"Error fetching recent news: {e}")
            return {"headlines": []}
    
    def _fetch_finnhub_news(self, symbol: str, base_asset: str) -> Dict[str, Any]:
        """Fetch news from Finnhub API with categorization."""
        try:
            all_headlines = []
            regulatory_news = []
            partnerships = []
            tech_updates = []
            
            # Try both symbol formats for better coverage
            symbols_to_try = [symbol, base_asset]
            if symbol != symbol.upper():
                symbols_to_try.append(symbol.upper())
            
            for sym in symbols_to_try:
                try:
                    # Get company news (works for stocks)
                    company_news = self.finnhub_client.get_company_news(sym)
                    if company_news and len(company_news) > 0:
                        for article in company_news[:10]:  # Limit per symbol
                            headline = article.get('headline', '')
                            if headline and len(headline.strip()) > 0:
                                all_headlines.append(headline)
                                self._categorize_finnhub_headline(headline, regulatory_news, partnerships, tech_updates)
                        break  # Found news, no need to try other symbols
                except Exception as e:
                    logger.debug(f"Company news failed for {sym}: {e}")
            
            # Get general market news if no company-specific news found
            if len(all_headlines) == 0:
                try:
                    general_news = self.finnhub_client.get_general_news()
                    if general_news and len(general_news) > 0:
                        # Filter for relevant news
                        for article in general_news[:20]:  # Check more general news
                            headline = article.get('headline', '')
                            if headline and self._is_relevant_to_asset(headline, base_asset):
                                all_headlines.append(headline)
                                self._categorize_finnhub_headline(headline, regulatory_news, partnerships, tech_updates)
                                if len(all_headlines) >= 8:  # Limit relevant general news
                                    break
                except Exception as e:
                    logger.debug(f"General news failed: {e}")
            
            return {
                "headlines": all_headlines,
                "regulatory_news": regulatory_news,
                "partnerships": partnerships,
                "tech_updates": tech_updates
            }
            
        except Exception as e:
            logger.error(f"Error fetching Finnhub news: {e}")
            return {"headlines": []}
    
    def _categorize_finnhub_headline(self, headline: str, regulatory_news: List[str], 
                                   partnerships: List[str], tech_updates: List[str]):
        """Categorize a Finnhub headline into appropriate news types."""
        try:
            headline_lower = headline.lower()
            
            # Regulatory keywords
            if any(word in headline_lower for word in [
                'regulation', 'regulatory', 'sec', 'cftc', 'fda', 'ftc', 'doj',
                'ban', 'legal', 'lawsuit', 'investigation', 'compliance',
                'approval', 'license', 'permit', 'sanctions'
            ]):
                regulatory_news.append(headline)
            
            # Partnership keywords
            elif any(word in headline_lower for word in [
                'partnership', 'collaboration', 'alliance', 'joint venture',
                'merger', 'acquisition', 'deal', 'agreement', 'contract',
                'integration', 'cooperation', 'strategic'
            ]):
                partnerships.append(headline)
            
            # Technical/product keywords
            elif any(word in headline_lower for word in [
                'upgrade', 'update', 'launch', 'release', 'version',
                'technology', 'innovation', 'development', 'platform',
                'software', 'hardware', 'product', 'feature', 'beta'
            ]):
                tech_updates.append(headline)
                
        except Exception as e:
            logger.error(f"Error categorizing headline: {e}")
    
    def _fetch_rss_headlines(self, feed_url: str, asset: str) -> List[str]:
        """Fetch headlines from RSS feed filtered by asset."""
        try:
            feed = feedparser.parse(feed_url)
            headlines = []
            
            for entry in feed.entries[:20]:  # Check recent entries
                title = entry.get('title', '')
                summary = entry.get('summary', '')
                
                # Check if headline is relevant to the asset
                if self._is_relevant_to_asset(title + ' ' + summary, asset):
                    headlines.append(title)
                    
                if len(headlines) >= 5:  # Limit per source
                    break
            
            return headlines
            
        except Exception as e:
            logger.error(f"Error fetching RSS from {feed_url}: {e}")
            return []
    
    def _extract_base_asset(self, symbol: str) -> str:
        """Extract base asset from trading pair symbol."""
        try:
            # Common quote currencies to remove
            quote_currencies = ['USDT', 'USDC', 'BTC', 'ETH', 'BNB', 'USD']
            
            for quote in quote_currencies:
                if symbol.endswith(quote):
                    return symbol[:-len(quote)]
            
            # If no quote currency found, return first 3-4 characters
            return symbol[:4] if len(symbol) > 4 else symbol
            
        except Exception as e:
            logger.error(f"Error extracting base asset from {symbol}: {e}")
            return symbol
    
    def _is_relevant_to_asset(self, text: str, asset: str) -> bool:
        """Check if text is relevant to the specified asset."""
        try:
            text_lower = text.lower()
            asset_lower = asset.lower()
            
            # Direct asset name match
            if asset_lower in text_lower:
                return True
            
            # Common asset name variations
            asset_variations = {
                'btc': ['bitcoin', 'btc'],
                'eth': ['ethereum', 'eth', 'ether'],
                'ada': ['cardano', 'ada'],
                'bnb': ['binance', 'bnb'],
                'xrp': ['ripple', 'xrp'],
                'sol': ['solana', 'sol'],
                'dot': ['polkadot', 'dot'],
                'matic': ['polygon', 'matic'],
                'avax': ['avalanche', 'avax'],
                'link': ['chainlink', 'link']
            }
            
            variations = asset_variations.get(asset_lower, [asset_lower])
            return any(variation in text_lower for variation in variations)
            
        except Exception as e:
            logger.error(f"Error checking relevance: {e}")
            return False
    
    def _analyze_news_impact(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the potential impact of news items."""
        try:
            impact_analysis = {
                "overall_impact": "neutral",
                "regulatory_impact": "neutral",
                "adoption_impact": "neutral",
                "technical_impact": "neutral",
                "market_impact": "neutral"
            }
            
            headlines = news_data.get("headlines", [])
            regulatory_news = news_data.get("regulatory_news", [])
            partnerships = news_data.get("partnerships", [])
            tech_updates = news_data.get("tech_updates", [])
            
            # Analyze headline sentiment
            if headlines:
                headline_sentiment = self._analyze_headline_sentiment(headlines)
                impact_analysis["overall_impact"] = headline_sentiment
            
            # Regulatory impact
            if regulatory_news:
                reg_impact = self._analyze_regulatory_impact(regulatory_news)
                impact_analysis["regulatory_impact"] = reg_impact
            
            # Adoption impact from partnerships
            if partnerships:
                adoption_impact = self._analyze_adoption_impact(partnerships)
                impact_analysis["adoption_impact"] = adoption_impact
            
            # Technical impact
            if tech_updates:
                tech_impact = self._analyze_technical_impact(tech_updates)
                impact_analysis["technical_impact"] = tech_impact
            
            return impact_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing news impact: {e}")
            return {"overall_impact": "neutral"}
    
    def _analyze_headline_sentiment(self, headlines: List[str]) -> str:
        """Analyze sentiment from headlines."""
        try:
            positive_keywords = [
                'surge', 'rally', 'bullish', 'gains', 'rise', 'breakthrough', 
                'adoption', 'partnership', 'upgrade', 'launch', 'success', 'growth'
            ]
            
            negative_keywords = [
                'crash', 'dump', 'bearish', 'losses', 'fall', 'hack', 'ban', 
                'regulation', 'concern', 'warning', 'decline', 'drop', 'plunge'
            ]
            
            positive_score = 0
            negative_score = 0
            
            for headline in headlines:
                headline_lower = headline.lower()
                positive_score += sum(1 for word in positive_keywords if word in headline_lower)
                negative_score += sum(1 for word in negative_keywords if word in headline_lower)
            
            if positive_score > negative_score * 1.5:
                return "very_positive"
            elif positive_score > negative_score:
                return "positive"
            elif negative_score > positive_score * 1.5:
                return "very_negative"
            elif negative_score > positive_score:
                return "negative"
            else:
                return "neutral"
                
        except Exception as e:
            logger.error(f"Error analyzing headline sentiment: {e}")
            return "neutral"
    
    def _analyze_regulatory_impact(self, regulatory_news: List[str]) -> str:
        """Analyze regulatory impact from news."""
        try:
            if not regulatory_news:
                return "neutral"
            
            positive_reg_keywords = ['approval', 'clarity', 'framework', 'support', 'legal']
            negative_reg_keywords = ['ban', 'restriction', 'investigation', 'lawsuit', 'violation']
            
            positive_count = 0
            negative_count = 0
            
            for news in regulatory_news:
                news_lower = news.lower()
                positive_count += sum(1 for word in positive_reg_keywords if word in news_lower)
                negative_count += sum(1 for word in negative_reg_keywords if word in news_lower)
            
            if positive_count > negative_count:
                return "positive"
            elif negative_count > positive_count:
                return "negative"
            else:
                return "neutral"
                
        except Exception as e:
            logger.error(f"Error analyzing regulatory impact: {e}")
            return "neutral"
    
    def _analyze_adoption_impact(self, partnerships: List[str]) -> str:
        """Analyze adoption impact from partnerships."""
        try:
            if not partnerships:
                return "neutral"
            
            # More partnerships generally indicate positive adoption
            if len(partnerships) >= 3:
                return "very_positive"
            elif len(partnerships) >= 1:
                return "positive"
            else:
                return "neutral"
                
        except Exception as e:
            logger.error(f"Error analyzing adoption impact: {e}")
            return "neutral"
    
    def _analyze_technical_impact(self, tech_updates: List[str]) -> str:
        """Analyze technical impact from updates."""
        try:
            if not tech_updates:
                return "neutral"
            
            positive_tech_keywords = ['upgrade', 'improvement', 'enhancement', 'optimization']
            negative_tech_keywords = ['bug', 'vulnerability', 'issue', 'problem']
            
            positive_count = 0
            negative_count = 0
            
            for update in tech_updates:
                update_lower = update.lower()
                positive_count += sum(1 for word in positive_tech_keywords if word in update_lower)
                negative_count += sum(1 for word in negative_tech_keywords if word in update_lower)
            
            if positive_count > negative_count:
                return "positive"
            elif negative_count > positive_count:
                return "negative"
            else:
                return "neutral"
                
        except Exception as e:
            logger.error(f"Error analyzing technical impact: {e}")
            return "neutral"
    
    def _extract_news_signals(self, analysis: str) -> Dict[str, Any]:
        """Extract news signals from LLM analysis."""
        try:
            full_text = analysis.lower() if isinstance(analysis, str) else str(analysis).lower()
            
            signals = {
                "news_impact": "neutral",
                "impact_timeframe": "short-term",
                "fundamental_strength": "neutral",
                "regulatory_risk": "low",
                "market_catalysts": []
            }
            
            # Extract news impact
            if any(phrase in full_text for phrase in ["very positive", "extremely positive"]):
                signals["news_impact"] = "very_positive"
            elif "positive" in full_text:
                signals["news_impact"] = "positive"
            elif any(phrase in full_text for phrase in ["very negative", "extremely negative"]):
                signals["news_impact"] = "very_negative"
            elif "negative" in full_text:
                signals["news_impact"] = "negative"
            
            # Extract timeframe
            if any(word in full_text for word in ["long-term", "long term"]):
                signals["impact_timeframe"] = "long-term"
            elif any(word in full_text for word in ["immediate", "short-term", "short term"]):
                signals["impact_timeframe"] = "short-term"
            
            # Extract regulatory risk
            if any(word in full_text for word in ["high risk", "regulatory concern"]):
                signals["regulatory_risk"] = "high"
            elif any(word in full_text for word in ["medium risk", "some concern"]):
                signals["regulatory_risk"] = "medium"
            
            return signals
            
        except Exception as e:
            logger.error(f"Error extracting news signals: {e}")
            return {"news_impact": "neutral"}
    
    def _calculate_news_score(
        self, 
        impact_analysis: Dict[str, Any], 
        signals: Dict[str, Any]
    ) -> float:
        """Calculate overall news score (0-100)."""
        try:
            score = 50  # Neutral starting point
            
            # Overall impact contribution
            overall_impact = impact_analysis.get("overall_impact", "neutral")
            impact_scores = {
                "very_positive": 25,
                "positive": 15,
                "neutral": 0,
                "negative": -15,
                "very_negative": -25
            }
            score += impact_scores.get(overall_impact, 0)
            
            # Regulatory impact
            reg_impact = impact_analysis.get("regulatory_impact", "neutral")
            reg_scores = {"positive": 10, "neutral": 0, "negative": -15}
            score += reg_scores.get(reg_impact, 0)
            
            # Adoption impact
            adoption_impact = impact_analysis.get("adoption_impact", "neutral")
            adoption_scores = {"very_positive": 15, "positive": 10, "neutral": 0}
            score += adoption_scores.get(adoption_impact, 0)
            
            # Technical impact
            tech_impact = impact_analysis.get("technical_impact", "neutral")
            tech_scores = {"positive": 10, "neutral": 0, "negative": -10}
            score += tech_scores.get(tech_impact, 0)
            
            # News impact signal
            news_impact = signals.get("news_impact", "neutral")
            score += impact_scores.get(news_impact, 0)
            
            # Regulatory risk penalty
            reg_risk = signals.get("regulatory_risk", "low")
            risk_penalties = {"high": -20, "medium": -10, "low": 0}
            score += risk_penalties.get(reg_risk, 0)
            
            # Ensure score is within bounds
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating news score: {e}")
            return 50.0
    
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
    
    def get_news_summary(self, symbol: str) -> Dict[str, Any]:
        """Get summary of recent news analysis."""
        try:
            if not self.last_analysis:
                return {"error": "No recent analysis available"}
            
            return {
                "symbol": symbol,
                "last_analysis": self.last_analysis.get("timestamp"),
                "news_score": self.last_analysis.get("news_score", 0),
                # Remove recommendation reference - Trading Agent handles all trading decisions
                "key_impacts": {
                    "overall_impact": self.last_analysis.get("news_impact", {}).get("overall_impact"),
                    "regulatory_impact": self.last_analysis.get("news_impact", {}).get("regulatory_impact"),
                    "news_impact": self.last_analysis.get("news_signals", {}).get("news_impact"),
                    "regulatory_risk": self.last_analysis.get("news_signals", {}).get("regulatory_risk")
                },
                "confidence": self.last_analysis.get("confidence", 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting news summary: {e}")
            return {"error": str(e)}
