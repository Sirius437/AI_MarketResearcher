"""Centralized technical context formatting for all analyzers."""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from rich.table import Table
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


class AgentDisplayFormatter:
    """Centralized agent result display formatting for all analyzers."""
    
    @staticmethod
    def display_trading_agent_results(analysis: Dict[str, Any], agent_table: Table):
        """Display trading agent results in a clean, formatted way."""
        try:
            # Extract symbol and basic info
            symbol = analysis.get('symbol', 'N/A')
            agent_table.add_row("Symbol", symbol)
            
            # Position Direction - handle the actual data structure
            position_direction = analysis.get('position_direction', {})
            if isinstance(position_direction, dict):
                action = position_direction.get('action', 'N/A')
                confidence = position_direction.get('confidence', 0)
                position_type = position_direction.get('position_type', 'N/A')
                
                agent_table.add_row("Position Action", f"{action}")
                agent_table.add_row("Position Type", position_type.replace('_', ' ').title())
                agent_table.add_row("Direction Confidence", f"{confidence:.1f}")
                
                reasoning = position_direction.get('reasoning', '')
                if reasoning and len(reasoning) < 120:
                    agent_table.add_row("Reasoning", reasoning)
            
            # Position Analysis - Extract key metrics
            position_analysis = analysis.get('position_analysis', {})
            if isinstance(position_analysis, dict):
                exposure = position_analysis.get('portfolio_exposure', 0)
                if exposure > 0:
                    agent_table.add_row("Portfolio Exposure", f"{exposure:.1f}%")
                
                # Profit targets
                target_1 = position_analysis.get('profit_target_1', 0)
                target_2 = position_analysis.get('profit_target_2', 0)
                target_3 = position_analysis.get('profit_target_3', 0)
                if target_1 > 0:
                    agent_table.add_row("Profit Targets", f"${target_1:,.2f} | ${target_2:,.2f} | ${target_3:,.2f}")
                
                # Stop loss
                stop_loss_price = position_analysis.get('stop_loss_price', 0)
                stop_loss_pct = position_analysis.get('stop_loss_percent', 0)
                if stop_loss_price > 0:
                    agent_table.add_row("Stop Loss", f"${stop_loss_price:,.2f} ({stop_loss_pct:.1f}%)")
                elif stop_loss_pct > 0:
                    agent_table.add_row("Stop Loss", f"{stop_loss_pct:.1f}%")
                
                # Trailing stop
                trailing_activation = position_analysis.get('trailing_stop_activation', 0)
                trailing_distance = position_analysis.get('trailing_stop_distance', 0)
                if trailing_activation > 0:
                    agent_table.add_row("Trailing Stop", f"Activate at ${trailing_activation:,.2f}, {trailing_distance:.1f}% distance")
            
            # Risk Parameters
            risk_params = analysis.get('risk_parameters', {})
            if isinstance(risk_params, dict):
                risk_level = risk_params.get('risk_level', 'N/A')
                risk_score = risk_params.get('risk_score', 0)
                agent_table.add_row("Risk Level", f"{risk_level} ({risk_score:.1f}/10)")
                
                max_position = risk_params.get('max_position_size', 0)
                if max_position > 0:
                    agent_table.add_row("Max Position Size", f"{max_position:.1f}%")
                
                risk_reward = risk_params.get('risk_reward_ratio', 0)
                if risk_reward > 0:
                    agent_table.add_row("Risk/Reward Ratio", f"1:{risk_reward:.1f}")
            
            # Trading Strategy - Extract key recommendation only
            trading_strategy = analysis.get('trading_strategy', {})
            if isinstance(trading_strategy, dict):
                summary = trading_strategy.get('summary', '')
                if summary and len(summary) < 300:
                    agent_table.add_row("Strategy", summary)
                elif summary:
                    agent_table.add_row("Strategy", summary[:300] + "...")
            
            # Overall confidence from analysis
            confidence = analysis.get('confidence', 0)
            if confidence > 0 and confidence <= 1.0:
                agent_table.add_row("Confidence", f"{confidence*100:.1f}%")
                
        except Exception as e:
            agent_table.add_row("Display Error", f"{str(e)}")
    
    @staticmethod
    def display_sentiment_agent_results(analysis: Dict[str, Any], agent_table: Table):
        """Display sentiment agent results with key metrics extracted."""
        try:
            # Basic info
            symbol = analysis.get('symbol', 'N/A')
            agent_table.add_row("Symbol", symbol)
            
            # Extract sentiment signals from the response
            sentiment_signals = analysis.get('sentiment_signals', {})
            if isinstance(sentiment_signals, dict) and sentiment_signals:
                overall = sentiment_signals.get('overall_sentiment', 'N/A')
                social = sentiment_signals.get('social_sentiment', 'N/A')
                psychology = sentiment_signals.get('market_psychology', 'N/A')
                agent_table.add_row("Overall Sentiment", overall.replace('_', ' ').title())
                agent_table.add_row("Social Sentiment", social.replace('_', ' ').title())
                agent_table.add_row("Market Psychology", psychology.replace('_', ' ').title())
            
            # Sentiment score
            sentiment_score = analysis.get('sentiment_score', 0)
            if sentiment_score > 0:
                agent_table.add_row("Sentiment Score", f"{sentiment_score:.0f}/100")
            
            # Recommendation
            recommendation = analysis.get('recommendation', {})
            if isinstance(recommendation, dict) and recommendation:
                action = recommendation.get('action', 'N/A')
                strength = recommendation.get('strength', 'N/A')
                score = recommendation.get('score', 0)
                agent_table.add_row("Recommendation", f"{action.upper()} ({strength}, {score:.0f}/100)")
            
            # Confidence
            confidence = analysis.get('confidence', 0)
            if confidence > 0:
                if confidence <= 1.0:
                    agent_table.add_row("Confidence", f"{confidence*100:.1f}%")
                else:
                    agent_table.add_row("Confidence", f"{confidence:.1f}%")
            
            # Add commentary from LLM analysis
            analysis_text = analysis.get('analysis', analysis.get('summary', ''))
            if analysis_text:
                # Extract a meaningful snippet for commentary
                commentary = AgentDisplayFormatter._extract_commentary(analysis_text, 'sentiment')
                if commentary:
                    agent_table.add_row("Commentary", commentary)
                    
        except Exception as e:
            agent_table.add_row("Display Error", f"{str(e)}")
        
        # Display detailed analysis sections after the table
        analysis_text = analysis.get('analysis', '')
        if analysis_text and len(analysis_text) > 500:
            console.print(f"\n[dim]📄 Detailed Sentiment Analysis:[/dim]")
            AgentDisplayFormatter._display_detailed_analysis(analysis_text)
    
    @staticmethod
    def display_news_agent_results(analysis: Dict[str, Any], agent_table: Table):
        """Display news agent results with key metrics extracted."""
        try:
            # Basic info
            symbol = analysis.get('symbol', 'N/A')
            agent_table.add_row("Symbol", symbol)
            
            # Extract news signals
            news_signals = analysis.get('news_signals', {})
            if isinstance(news_signals, dict) and news_signals:
                impact = news_signals.get('news_impact', 'N/A')
                timeframe = news_signals.get('impact_timeframe', 'N/A')
                strength = news_signals.get('fundamental_strength', 'N/A')
                agent_table.add_row("News Impact", impact.replace('_', ' ').title())
                agent_table.add_row("Impact Timeframe", timeframe.replace('_', ' ').title())
                agent_table.add_row("Fundamental Strength", strength.replace('_', ' ').title())
            
            # News score
            news_score = analysis.get('news_score', 0)
            if news_score > 0:
                agent_table.add_row("News Score", f"{news_score:.0f}/100")
            
            # Recommendation
            recommendation = analysis.get('recommendation', {})
            if isinstance(recommendation, dict) and recommendation:
                action = recommendation.get('action', 'N/A')
                strength = recommendation.get('strength', 'N/A')
                score = recommendation.get('score', 0)
                agent_table.add_row("Recommendation", f"{action.upper()} ({strength}, {score:.0f}/100)")
            
            # Confidence
            confidence = analysis.get('confidence', 0)
            if confidence > 0:
                if confidence <= 1.0:
                    agent_table.add_row("Confidence", f"{confidence*100:.1f}%")
                else:
                    agent_table.add_row("Confidence", f"{confidence:.1f}%")
            
            # Add commentary from LLM analysis
            analysis_text = analysis.get('analysis', analysis.get('summary', ''))
            if analysis_text:
                # Extract a meaningful snippet for commentary
                commentary = AgentDisplayFormatter._extract_commentary(analysis_text, 'news')
                if commentary:
                    agent_table.add_row("Commentary", commentary)
                    
        except Exception as e:
            agent_table.add_row("Display Error", f"{str(e)}")
        
        # Display detailed analysis sections after the table
        analysis_text = analysis.get('analysis', '')
        if analysis_text and len(analysis_text) > 500:
            console.print(f"\n[dim]📄 Detailed News Analysis:[/dim]")
            AgentDisplayFormatter._display_detailed_analysis(analysis_text)
    
    @staticmethod
    def display_risk_agent_results(analysis: Dict[str, Any], agent_table: Table):
        """Display risk agent results with key metrics extracted."""
        try:
            # Basic info
            symbol = analysis.get('symbol', 'N/A')
            agent_table.add_row("Symbol", symbol)
            
            # Extract risk signals
            risk_signals = analysis.get('risk_signals', {})
            if isinstance(risk_signals, dict) and risk_signals:
                risk_level = risk_signals.get('risk_level', 'N/A')
                position_sizing = risk_signals.get('position_sizing', 'N/A')
                mitigation = risk_signals.get('mitigation_needed', 0)
                agent_table.add_row("Risk Level", risk_level.replace('_', ' ').upper())
                agent_table.add_row("Position Sizing", position_sizing.replace('_', ' ').title())
                if mitigation > 0:
                    if mitigation <= 1.0:
                        agent_table.add_row("Mitigation Needed", f"{mitigation*100:.0f}%")
                    else:
                        agent_table.add_row("Mitigation Needed", f"{mitigation:.0f}%")
            
            # Risk score
            risk_score = analysis.get('risk_score', 0)
            if risk_score > 0:
                agent_table.add_row("Risk Score", f"{risk_score:.0f}/100")
            
            # Recommendation
            recommendation = analysis.get('recommendation', {})
            if isinstance(recommendation, dict) and recommendation:
                action = recommendation.get('action', 'N/A')
                strength = recommendation.get('strength', 'N/A')
                score = recommendation.get('score', 0)
                agent_table.add_row("Recommendation", f"{action.upper()} ({strength}, {score:.0f}/100)")
            
            # Confidence
            confidence = analysis.get('confidence', 0)
            if confidence > 0:
                if confidence <= 1.0:
                    agent_table.add_row("Confidence", f"{confidence*100:.1f}%")
                else:
                    agent_table.add_row("Confidence", f"{confidence:.1f}%")
            
            # Add commentary from LLM analysis
            analysis_text = analysis.get('analysis', analysis.get('summary', ''))
            if analysis_text:
                # Extract a meaningful snippet for commentary
                commentary = AgentDisplayFormatter._extract_commentary(analysis_text, 'risk')
                if commentary:
                    agent_table.add_row("Commentary", commentary)
                    
        except Exception as e:
            agent_table.add_row("Display Error", f"{str(e)}")
        
        # Display detailed analysis sections after the table
        analysis_text = analysis.get('analysis', '')
        if analysis_text and len(analysis_text) > 500:
            console.print(f"\n[dim]📄 Detailed Risk Analysis:[/dim]")
            AgentDisplayFormatter._display_detailed_analysis(analysis_text)
    
    @staticmethod
    def _extract_commentary(analysis_text: str, agent_type: str) -> str:
        """Extract meaningful commentary from LLM analysis text."""
        try:
            if not analysis_text:
                return ""
            
            # Extract key sections from the analysis
            sections = []
            current_section = ""
            lines = analysis_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or 'disclaimer' in line.lower() or line.startswith('*'):
                    continue
                    
                # Look for section headers
                if line.startswith('##') or line.startswith('###'):
                    if current_section and len(current_section) > 30:
                        sections.append(current_section.strip())
                    current_section = line.replace('#', '').strip() + ": "
                elif line.startswith('|') or line.startswith('**'):
                    # Skip table headers and bold formatting
                    continue
                elif current_section and len(line) > 20:
                    # Add meaningful content to current section
                    clean_line = line.strip('- *').strip()
                    if clean_line and not clean_line.startswith('|'):
                        current_section += clean_line + " "
                        if len(current_section) > 300:  # Limit section length
                            sections.append(current_section.strip())
                            current_section = ""
                            break
            
            # Add final section if exists
            if current_section and len(current_section) > 30:
                sections.append(current_section.strip())
            
            # Return the most relevant sections
            if sections:
                # Take first 2-3 most informative sections
                relevant_sections = sections[:2]
                commentary = " | ".join(relevant_sections)
                
                # Limit total length but be more generous
                if len(commentary) > 500:
                    commentary = commentary[:500] + "..."
                return commentary
            
            # Fallback: extract key bullet points
            bullet_points = []
            for line in lines:
                line = line.strip()
                if line.startswith('-') or line.startswith('•'):
                    clean_point = line.strip('- •*').strip()
                    if len(clean_point) > 20 and len(clean_point) < 200:
                        bullet_points.append(clean_point)
                        if len(bullet_points) >= 3:
                            break
            
            if bullet_points:
                return " | ".join(bullet_points)
            
            # Final fallback to meaningful paragraphs
            paragraphs = analysis_text.split('\n\n')
            for para in paragraphs:
                clean_para = para.strip('- *#|').strip()
                if len(clean_para) > 50 and 'disclaimer' not in clean_para.lower():
                    if len(clean_para) > 400:
                        return clean_para[:400] + "..."
                    return clean_para
            
            return ""
            
        except Exception as e:
            return f"Commentary extraction error: {str(e)}"
    
    @staticmethod
    def _display_detailed_analysis(analysis_text: str):
        """Display detailed LLM analysis in structured format."""
        try:
            # Split into sections based on headers
            sections = []
            current_section = {"title": "", "content": []}
            lines = analysis_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Detect section headers
                if line.startswith('##') or line.startswith('###'):
                    if current_section["content"]:
                        sections.append(current_section)
                    current_section = {
                        "title": line.replace('#', '').strip(),
                        "content": []
                    }
                elif line.startswith('|') or 'disclaimer' in line.lower():
                    # Skip table formatting and disclaimers
                    continue
                elif line and len(line) > 15:
                    # Add meaningful content
                    clean_line = line.strip('- *').strip()
                    if clean_line and not clean_line.startswith('**'):
                        current_section["content"].append(clean_line)
            
            # Add final section
            if current_section["content"]:
                sections.append(current_section)
            
            # Display sections with Rich formatting
            for section in sections[:4]:  # Limit to first 4 sections
                if section["title"] and section["content"]:
                    console.print(f"\n[bold cyan]{section['title']}[/bold cyan]")
                    
                    # Group content into meaningful paragraphs
                    content_text = " ".join(section["content"])
                    if len(content_text) > 300:
                        content_text = content_text[:300] + "..."
                    
                    # Wrap text nicely
                    from textwrap import fill
                    wrapped_text = fill(content_text, width=80)
                    console.print(f"[dim]{wrapped_text}[/dim]")
            
            # If no sections found, display as paragraphs
            if not sections:
                paragraphs = analysis_text.split('\n\n')
                for i, para in enumerate(paragraphs[:3]):  # Show first 3 paragraphs
                    clean_para = para.strip('- *#|').strip()
                    if len(clean_para) > 50:
                        console.print(f"\n[dim]{clean_para[:400]}{'...' if len(clean_para) > 400 else ''}[/dim]")
                        
        except Exception as e:
            console.print(f"[red]Error displaying detailed analysis: {str(e)}[/red]")
    
    @staticmethod
    def format_nested_dict(data: Dict[str, Any]) -> str:
        """Format nested dictionary for clean display."""
        try:
            if not isinstance(data, dict):
                return str(data)
            
            formatted_items = []
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    if 'percent' in key.lower() or 'pct' in key.lower():
                        formatted_items.append(f"{key}: {value:.1f}%")
                    elif 'price' in key.lower():
                        formatted_items.append(f"{key}: ${value:.4f}")
                    else:
                        formatted_items.append(f"{key}: {value:.2f}")
                elif isinstance(value, str) and len(value) < 50:
                    formatted_items.append(f"{key}: {value}")
                elif isinstance(value, bool):
                    formatted_items.append(f"{key}: {'Yes' if value else 'No'}")
            
            return " | ".join(formatted_items[:3])  # Limit to 3 items for readability
        except:
            return str(data)[:100]


class TechnicalContextFormatter:
    """Centralized technical context formatting for all market analyzers."""
    
    @staticmethod
    def format_technical_context_for_agents(
        ohlcv_summary: Dict[str, Any], 
        technical_indicators: Dict[str, Any], 
        current_price: float,
        asset_type: str = "asset"
    ) -> str:
        """Format technical analysis context for agent consumption."""
        try:
            context_parts = []
            
            # Price performance
            if 'price_change_30d_pct' in ohlcv_summary:
                change_pct = ohlcv_summary['price_change_30d_pct']
                context_parts.append(f"30-day performance: {change_pct:+.2f}%")
            
            # Volatility
            if 'volatility_30d' in ohlcv_summary:
                volatility = ohlcv_summary['volatility_30d']
                context_parts.append(f"30-day volatility: {volatility:.2f}%")
            
            # Volume analysis
            if 'avg_volume_30d' in ohlcv_summary and 'volume_trend' in ohlcv_summary:
                volume_trend = ohlcv_summary['volume_trend']
                context_parts.append(f"Volume trend: {volume_trend}")
            
            # RSI analysis
            if 'rsi' in technical_indicators and technical_indicators['rsi'] is not None:
                rsi = technical_indicators['rsi']
                if rsi > 70:
                    rsi_trend = "overbought"
                elif rsi < 30:
                    rsi_trend = "oversold"
                else:
                    rsi_trend = "neutral"
                context_parts.append(f"RSI: {rsi:.1f} ({rsi_trend})")
            
            # Moving average trend
            sma_20 = technical_indicators.get('sma_20')
            if sma_20 is not None:
                if current_price > sma_20:
                    ma_trend = "above 20-day MA"
                else:
                    ma_trend = "below 20-day MA"
                
                if asset_type == "crypto":
                    context_parts.append(f"Price: {ma_trend} (${sma_20:.6f})")
                else:
                    context_parts.append(f"Price: {ma_trend} (${sma_20:.2f})")
            
            # MACD trend
            if 'macd' in technical_indicators and 'macd_signal' in technical_indicators:
                macd = technical_indicators['macd']
                macd_signal = technical_indicators['macd_signal']
                if macd is not None and macd_signal is not None:
                    macd_trend = "bullish" if macd > macd_signal else "bearish"
                    context_parts.append(f"MACD: {macd_trend} trend")
                elif macd is not None:
                    context_parts.append(f"MACD: {macd:.4f} (signal unavailable)")
            elif 'macd' in technical_indicators and technical_indicators['macd'] is not None:
                context_parts.append(f"MACD: {technical_indicators['macd']:.4f} (signal unavailable)")
            
            # Support and resistance levels
            support = technical_indicators.get('support_level')
            resistance = technical_indicators.get('resistance_level')
            if support is not None and resistance is not None:
                if asset_type == "crypto":
                    context_parts.append(f"Support: ${support:.6f}, Resistance: ${resistance:.6f}")
                else:
                    context_parts.append(f"Support: ${support:.2f}, Resistance: ${resistance:.2f}")
            
            # Bollinger Bands position
            bb_position = technical_indicators.get('bb_position')
            if bb_position is not None:
                if bb_position > 0.8:
                    bb_status = "near upper band (overbought)"
                elif bb_position < 0.2:
                    bb_status = "near lower band (oversold)"
                else:
                    bb_status = "within normal range"
                context_parts.append(f"Bollinger Bands: {bb_status}")
            
            # Stochastic oscillator
            stoch_k = technical_indicators.get('stoch_k')
            stoch_d = technical_indicators.get('stoch_d')
            if stoch_k is not None and stoch_d is not None:
                if stoch_k > 80:
                    stoch_status = "overbought"
                elif stoch_k < 20:
                    stoch_status = "oversold"
                else:
                    stoch_status = "neutral"
                context_parts.append(f"Stochastic: {stoch_status} ({stoch_k:.1f})")
            
            return " | ".join(context_parts) if context_parts else "Limited technical data available"
            
        except Exception as e:
            logger.error(f"Error formatting technical context: {e}")
            return "Error processing technical context"
    
    @staticmethod
    def extract_indicators_from_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
        """Extract technical indicators from DataFrame with calculated indicators."""
        try:
            if df.empty:
                return {}
            
            indicators = {}
            latest = df.iloc[-1]
            
            # Extract all available indicators
            indicator_mappings = {
                'rsi': 'rsi',
                'macd_line': 'macd',
                'macd_signal': 'macd_signal', 
                'bb_upper': 'bb_upper',
                'bb_lower': 'bb_lower',
                'bb_middle': 'bb_middle',
                'bb_percent': 'bb_position',
                'sma_20': 'sma_20',
                'sma_50': 'sma_50',
                'sma_200': 'sma_200',
                'ema_12': 'ema_12',
                'ema_26': 'ema_26',
                'stoch_k': 'stoch_k',
                'stoch_d': 'stoch_d',
                'atr': 'atr',
                'obv': 'obv'
            }
            
            for df_col, indicator_key in indicator_mappings.items():
                if df_col in df.columns:
                    value = latest[df_col]
                    indicators[indicator_key] = value if pd.notna(value) else None
            
            # Calculate support/resistance if not available
            if 'support_level' not in indicators or 'resistance_level' not in indicators:
                try:
                    from data.indicators import TechnicalIndicators
                    support_resistance = TechnicalIndicators.calculate_support_resistance(df)
                    if support_resistance['support']:
                        indicators['support_level'] = support_resistance['support'][-1]
                    if support_resistance['resistance']:
                        indicators['resistance_level'] = support_resistance['resistance'][0]
                except Exception as e:
                    logger.warning(f"Could not calculate support/resistance: {e}")
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error extracting technical indicators: {e}")
            return {}
