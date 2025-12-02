"""Prompt management and formatting for local LLM interactions."""

import logging
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

from config.prompts import PromptTemplates
from config.settings import MarketResearcherConfig

logger = logging.getLogger(__name__)


class PromptManager:
    """Manage and format prompts for different trading agents."""
    
    def __init__(self, config: MarketResearcherConfig):
        """Initialize prompt manager."""
        self.config = config
        self.templates = PromptTemplates()
        self._conversation_history = {}
    
    def create_technical_analysis_prompt(
        self, 
        symbol: str, 
        market_data: Dict[str, Any],
        indicators: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Create prompt for technical analysis agent."""
        try:
            # Format market data for prompt with proper None handling
            def format_indicator(value, decimal_places=2):
                """Format indicator value, handling None/NaN properly."""
                if value is None or (hasattr(value, '__iter__') and len(str(value)) == 0):
                    return 'N/A'
                try:
                    if isinstance(value, (int, float)) and not pd.isna(value):
                        return f"{value:.{decimal_places}f}"
                    return str(value)
                except:
                    return 'N/A'
            
            prompt_data = {
                'symbol': symbol,
                'current_price': format_indicator(market_data.get('current_price', market_data.get('price', 0)), 2),
                'price_change_24h': format_indicator(market_data.get('price_change', market_data.get('change_24h', market_data.get('price_change_24h', 0))), 2),
                'price_change_percent': format_indicator(market_data.get('price_change_percent', 0), 2),
                'volume': self._format_volume(market_data.get('volume', 0)),
                'rsi': format_indicator(indicators.get('rsi', indicators.get('rsi_14')), 2),
                'macd_line': format_indicator(indicators.get('macd_line', indicators.get('macd')), 4),
                'macd_signal': format_indicator(indicators.get('macd_signal'), 4),
                'bb_upper': format_indicator(indicators.get('bb_upper'), 2),
                'bb_lower': format_indicator(indicators.get('bb_lower'), 2),
                'support_levels': self._format_levels(indicators.get('support_levels', [indicators.get('support_level')])),
                'resistance_levels': self._format_levels(indicators.get('resistance_levels', [indicators.get('resistance_level')])),
                'price_history': self._format_price_history(market_data.get('price_history', [])) or f"30-day historical data available with {len(market_data.get('historical_data', []))} data points",
                'technical_context': market_data.get('technical_context', 'Technical analysis data not available')
            }
            
            system_prompt = self.templates.get_system_prompt("technical")
            user_prompt = self.templates.format_prompt(
                self.templates.TECHNICAL_ANALYSIS, 
                **prompt_data
            )
            
            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
        except Exception as e:
            logger.error(f"Error creating technical analysis prompt: {e}")
            return self._get_fallback_prompt("technical", symbol)
    
    def create_sentiment_analysis_prompt(
        self, 
        symbol: str, 
        sentiment_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Create prompt for sentiment analysis agent."""
        try:
            prompt_data = {
                'symbol': symbol,
                'social_mentions': sentiment_data.get('social_mentions', 0),
                'sentiment_score': sentiment_data.get('sentiment_score', 0),
                'fear_greed_index': sentiment_data.get('fear_greed_index', 50),
                'news_headlines': self._format_news_headlines(sentiment_data.get('news_headlines', [])),
                'reddit_activity': sentiment_data.get('reddit_activity', 'Low'),
                'twitter_trends': sentiment_data.get('twitter_trends', []),
                'current_price': sentiment_data.get('current_price', 0),
                'recent_performance': sentiment_data.get('recent_performance', 'Neutral'),
                'technical_context': sentiment_data.get('technical_context', 'Technical analysis data not available')
            }
            
            system_prompt = self.templates.get_system_prompt("sentiment")
            user_prompt = self.templates.format_prompt(
                self.templates.SENTIMENT_ANALYSIS, 
                **prompt_data
            )
            
            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
        except Exception as e:
            logger.error(f"Error creating sentiment analysis prompt: {e}")
            return self._get_fallback_prompt("sentiment", symbol)
    
    def create_news_analysis_prompt(
        self, 
        symbol: str, 
        news_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Create prompt for news analysis agent."""
        try:
            prompt_data = {
                'symbol': symbol,
                'headlines': self._format_news_headlines(news_data.get('headlines', [])),
                'regulatory_news': news_data.get('regulatory_news', []),
                'partnerships': news_data.get('partnerships', []),
                'tech_updates': news_data.get('tech_updates', []),
                'market_events': news_data.get('market_events', []),
                'current_price': news_data.get('current_price', 0),
                'market_cap_rank': news_data.get('market_cap_rank', 'N/A'),
                'volume': self._format_volume(news_data.get('volume', 0))
            }
            
            system_prompt = self.templates.get_system_prompt("news")
            user_prompt = self.templates.format_prompt(
                self.templates.NEWS_ANALYSIS, 
                **prompt_data
            )
            
            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
        except Exception as e:
            logger.error(f"Error creating news analysis prompt: {e}")
            return self._get_fallback_prompt("news", symbol)
    
    def create_risk_assessment_prompt(
        self, 
        symbol: str, 
        position_data: Dict[str, Any],
        portfolio_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Create prompt for risk assessment agent."""
        try:
            prompt_data = {
                'symbol': symbol,
                'action': position_data.get('action', 'hold'),
                'position_size': position_data.get('position_size', 0),
                'entry_price': position_data.get('entry_price', 0),
                'stop_loss': position_data.get('stop_loss', 0),
                'take_profit': position_data.get('take_profit', 0),
                'current_price': position_data.get('current_price', 0),
                'volatility': position_data.get('volatility', 0),
                'btc_correlation': position_data.get('btc_correlation', 0),
                'liquidity_score': position_data.get('liquidity_score', 0),
                'market_cap': position_data.get('market_cap', 0),
                'portfolio_value': portfolio_data.get('total_value', 0),
                'existing_positions': portfolio_data.get('positions', []),
                'available_cash': portfolio_data.get('available_cash', 0),
                'portfolio_beta': portfolio_data.get('beta', 1.0),
                'price_history': self._format_price_history(position_data.get('price_history', [])),
                'volatility_patterns': position_data.get('volatility_patterns', 'N/A'),
                'market_cycles': position_data.get('market_cycles', 'N/A')
            }
            
            system_prompt = self.templates.get_system_prompt("risk")
            user_prompt = self.templates.format_prompt(
                self.templates.RISK_ASSESSMENT, 
                **prompt_data
            )
            
            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
        except Exception as e:
            logger.error(f"Error creating risk assessment prompt: {e}")
            return self._get_fallback_prompt("risk", symbol)
    
    
    def create_decision_synthesis_prompt(
        self, 
        symbol: str, 
        agent_reports: Dict[str, str],
        market_context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Create prompt for final decision synthesis."""
        try:
            prompt_data = {
                'symbol': symbol,
                'technical_report': agent_reports.get('technical', 'No technical analysis available'),
                'sentiment_report': agent_reports.get('sentiment', 'No sentiment analysis available'),
                'news_report': agent_reports.get('news', 'No news analysis available'),
                'risk_report': agent_reports.get('risk', 'No risk assessment available'),
                'current_price': market_context.get('current_price', 0),
                'market_conditions': market_context.get('market_conditions', 'Unknown'),
                'available_capital': market_context.get('available_capital', 0)
            }
            
            system_prompt = self.templates.get_system_prompt("decision")
            user_prompt = self.templates.format_prompt(
                self.templates.DECISION_SYNTHESIS, 
                **prompt_data
            )
            
            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
        except Exception as e:
            logger.error(f"Error creating decision synthesis prompt: {e}")
            return self._get_fallback_prompt("decision", symbol)
    
    def add_conversation_context(
        self, 
        agent_type: str, 
        messages: List[Dict[str, str]], 
        max_history: int = 3
    ) -> List[Dict[str, str]]:
        """Add conversation history context to messages."""
        try:
            if agent_type not in self._conversation_history:
                self._conversation_history[agent_type] = []
            
            history = self._conversation_history[agent_type]
            
            # Add recent history to messages
            if history:
                context_messages = []
                for entry in history[-max_history:]:
                    context_messages.extend([
                        {"role": "user", "content": entry["user"]},
                        {"role": "assistant", "content": entry["assistant"]}
                    ])
                
                # Insert history after system prompt
                if messages and messages[0]["role"] == "system":
                    return [messages[0]] + context_messages + messages[1:]
                else:
                    return context_messages + messages
            
            return messages
            
        except Exception as e:
            logger.error(f"Error adding conversation context: {e}")
            return messages
    
    def save_conversation_turn(
        self, 
        agent_type: str, 
        user_message: str, 
        assistant_response: str
    ):
        """Save a conversation turn for context."""
        try:
            if agent_type not in self._conversation_history:
                self._conversation_history[agent_type] = []
            
            self._conversation_history[agent_type].append({
                "timestamp": datetime.now().isoformat(),
                "user": user_message,
                "assistant": assistant_response
            })
            
            # Keep only recent conversations
            max_history = 10
            if len(self._conversation_history[agent_type]) > max_history:
                self._conversation_history[agent_type] = \
                    self._conversation_history[agent_type][-max_history:]
                    
        except Exception as e:
            logger.error(f"Error saving conversation turn: {e}")
    
    def _format_price_history(self, price_history: List[Dict[str, Any]]) -> str:
        """Format price history for prompt."""
        if not price_history:
            return ""
        
        formatted = []
        for entry in price_history[-5:]:  # Last 5 entries
            date = entry.get('date', 'Unknown')
            price = entry.get('price', 0)
            change = entry.get('change', 0)
            formatted.append(f"{date}: ${price:.2f} ({change:+.2f}%)")
        
        return "\n".join(formatted)
    
    def _format_levels(self, levels: List) -> str:
        """Format support/resistance levels for prompt."""
        if not levels or all(level is None or level == 'N/A' for level in levels):
            return "Calculated from historical data"
        
        formatted_levels = []
        for level in levels:
            if level is not None and level != 'N/A':
                try:
                    formatted_levels.append(f"${float(level):.2f}")
                except (ValueError, TypeError):
                    continue
        
        return ", ".join(formatted_levels) if formatted_levels else "Calculated from historical data"
    
    def _format_news_headlines(self, headlines: List[str]) -> str:
        """Format news headlines for prompt inclusion."""
        if not headlines:
            return "No recent news available"
        
        try:
            formatted_headlines = []
            for i, headline in enumerate(headlines[:5], 1):  # Top 5 headlines
                formatted_headlines.append(f"{i}. {headline}")
            
            return "\n".join(formatted_headlines)
        except Exception as e:
            logger.error(f"Error formatting news headlines: {e}")
            return "News formatting error"
    
    def _get_fallback_prompt(self, agent_type: str, symbol: str) -> List[Dict[str, str]]:
        """Get fallback prompt when main prompt creation fails."""
        system_prompt = self.templates.get_system_prompt(agent_type)
        user_prompt = f"Please analyze {symbol} based on available market data. Provide your {agent_type} assessment."
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def validate_prompt_data(self, prompt_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate prompt data completeness."""
        errors = []
        required_fields = ['symbol']
        
        for field in required_fields:
            if field not in prompt_data or prompt_data[field] is None:
                errors.append(f"Missing required field: {field}")
        
        # Check for reasonable data ranges
        if 'current_price' in prompt_data:
            price = prompt_data['current_price']
            if not isinstance(price, (int, float)) or price <= 0:
                errors.append("Invalid current_price value")
        
        return len(errors) == 0, errors
    
    def clear_conversation_history(self, agent_type: Optional[str] = None):
        """Clear conversation history for specific agent or all agents."""
        try:
            if agent_type:
                if agent_type in self._conversation_history:
                    del self._conversation_history[agent_type]
                    logger.info(f"Cleared conversation history for {agent_type}")
            else:
                self._conversation_history.clear()
                logger.info("Cleared all conversation history")
        except Exception as e:
            logger.error(f"Error clearing conversation history: {e}")
    
    def _format_volume(self, volume: Any) -> str:
        """Format volume for better LLM understanding."""
        try:
            if volume is None or volume == 0:
                return "0"
            
            volume_num = float(volume)
            if volume_num >= 1_000_000_000:
                return f"{volume_num / 1_000_000_000:.2f}B"
            elif volume_num >= 1_000_000:
                return f"{volume_num / 1_000_000:.2f}M"
            elif volume_num >= 1_000:
                return f"{volume_num / 1_000:.2f}K"
            else:
                return f"{volume_num:.0f}"
        except (ValueError, TypeError):
            return "N/A"
    
    def format_scanner_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Format scanner analysis prompt with context data."""
        try:
            return self.templates.SCANNER_ANALYSIS.format(
                top_opportunities=json.dumps(context.get('top_opportunities', []), indent=2),
                scanner_summary=json.dumps(context.get('scanner_summary', {}), indent=2),
                market_conditions=json.dumps(context.get('market_conditions', {}), indent=2)
            )
        except Exception as e:
            logger.error(f"Error formatting scanner analysis prompt: {e}")
            return "Error formatting scanner analysis prompt"
    
    def get_prompt(self, prompt_type: str) -> str:
        """Get a specific prompt by type."""
        if prompt_type == "scanner_analysis_system":
            return self.templates.get_system_prompt("scanner")
        elif hasattr(self.templates, prompt_type.upper()):
            return getattr(self.templates, prompt_type.upper())
        else:
            logger.warning(f"Unknown prompt type: {prompt_type}")
            return "You are a helpful financial analysis assistant."
    
    def get_conversation_summary(self, agent_type: str) -> Dict[str, Any]:
        """Get summary of conversation history for an agent."""
        try:
            if agent_type not in self._conversation_history:
                return {"total_turns": 0, "recent_topics": []}
            
            history = self._conversation_history[agent_type]
            return {
                "total_turns": len(history),
                "recent_topics": [entry["user"][:100] + "..." if len(entry["user"]) > 100 
                                else entry["user"] for entry in history[-3:]],
                "last_interaction": history[-1]["timestamp"] if history else None
            }
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return {"error": str(e)}
