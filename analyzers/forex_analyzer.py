"""
Forex analysis module for CryptoBot.
Handles all forex-related analysis logic using Polygon.io API.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import questionary
import pandas as pd
import numpy as np
import yfinance as yf

from data.universal_cache import UniversalCache
from analyzers.technical_context import AgentDisplayFormatter

logger = logging.getLogger(__name__)
console = Console()


class ForexAnalyzer:
    """Handles forex analysis operations using Polygon.io API."""
    
    def __init__(self, polygon_client, llm_client, config=None, prediction_engine=None, market_data_manager=None):
        """Initialize forex analyzer with required clients."""
        self.polygon_client = polygon_client
        self.llm_client = llm_client
        self.alpha_vantage_client = None
        self.config = config
        self.cache = UniversalCache(config) if config else None
        self.prediction_engine = prediction_engine
        self.market_data_manager = market_data_manager
        
        # Initialize signal generator for enhanced analysis
        from analyzers.signal_generator import UnifiedSignalGenerator
        self.signal_generator = UnifiedSignalGenerator()
    
    async def analyze_forex(self):
        """Analyze a single forex pair using Polygon.io API with Alpha Vantage fallback."""
        try:
            # Initialize Alpha Vantage fallback if needed
            if not self.polygon_client:
                console.print("[yellow]Polygon.io not configured, using Alpha Vantage fallback[/yellow]")
                from data.alpha_vantage_client import AlphaVantageClient
                self.alpha_vantage_client = AlphaVantageClient("demo")  # Free demo key
                await self.alpha_vantage_client.initialize()
            
            # Show major pairs or let user enter custom pair
            choice = await questionary.select(
                "Choose forex pair analysis method:",
                choices=[
                    "major - Select from major currency pairs",
                    "custom - Enter custom forex pair"
                ]
            ).ask_async()
            
            if not choice:
                return
            
            if choice.startswith("major"):
                # Show major pairs from active client
                if self.polygon_client:
                    major_pairs = self.polygon_client.get_major_pairs()
                else:
                    major_pairs = self.alpha_vantage_client.get_major_pairs()
                    
                symbol = await questionary.select(
                    "Select a major forex pair:",
                    choices=major_pairs
                ).ask_async()
            else:
                # Custom pair entry
                symbol = await questionary.text(
                    "Enter forex pair (e.g., EUR/USD, GBP/JPY):",
                    default="EUR/USD"
                ).ask_async()
            
            if not symbol:
                return
            
            # Normalize symbol format
            symbol = symbol.upper().replace("/", "/")
            if "/" not in symbol and len(symbol) == 6:
                symbol = f"{symbol[:3]}/{symbol[3:]}"
            
            console.print(f"[yellow]Analyzing forex pair: {symbol}[/yellow]")
            
            # Try Polygon first, fallback to Alpha Vantage
            # Check cache first
            if self.cache:
                cached_analysis = self.cache.get("forex", symbol, symbol=symbol)
                if cached_analysis:
                    console.print(f"[cyan]Using cached forex data for {symbol}[/cyan]")
                    analysis = cached_analysis
                else:
                    analysis = await self._fetch_forex_data(symbol)
                    # Cache the result
                    if analysis and 'error' not in analysis:
                        self.cache.set("forex", symbol, analysis, symbol=symbol)
            else:
                analysis = await self._fetch_forex_data(symbol)
            
            if 'error' in analysis:
                console.print(f"[red]Error fetching data: {analysis['error']}[/red]")
                return
            
            # Display forex data
            await self._display_forex_data(symbol, analysis)
            
            # Prepare data for LLM analysis
            llm_data = {
                'symbol': symbol,
                'quote': analysis.get('quote', {}),
                'daily_data': analysis.get('daily_data', [])[:10],  # Last 10 days
                'hourly_data': analysis.get('hourly_data', [])[:24],  # Last 24 hours
                'market_status': analysis.get('market_status', {}),
                'news': analysis.get('news', [])[:3]  # Top 3 news
            }
            
            # Collect 30-day historical data for technical analysis
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Collecting 30-day historical data...", total=None)
                
                current_price = 0
                historical_data = None
                market_data = {}
                enriched_symbol_data = llm_data.copy()
                
                # Get current price and 30-day historical data from market data manager
                # Normalize symbol format (remove slash for MarketDataManager)
                normalized_symbol = symbol.replace("/", "")
                market_overview = await self.market_data_manager.get_market_overview([normalized_symbol])
                current_price = market_overview.get(normalized_symbol, {}).get('price', 0)
                
                # Get 60-day historical data with technical indicators (more data for MACD signal)
                historical_data = await self.market_data_manager.get_symbol_data(
                    normalized_symbol, timeframe='1d', limit=60, include_indicators=True
                )
                
                # Process historical data
                if not historical_data.empty:
                    progress.update(task, description="Processing technical data...")
                    
                    # Extract technical indicators (already calculated by MarketDataManager)
                    from analyzers.technical_context import TechnicalContextFormatter
                    technical_indicators = TechnicalContextFormatter.extract_indicators_from_dataframe(historical_data)
                    ohlcv_summary = self._process_ohlcv_data(historical_data)
                    
                    market_data['ohlcv_30d'] = ohlcv_summary
                    market_data['technical_indicators'] = technical_indicators
                    
                    # Prepare enriched data for prediction engine
                    enriched_symbol_data['ohlcv_30d'] = ohlcv_summary
                    enriched_symbol_data['technical_indicators'] = technical_indicators
                    enriched_symbol_data['historical_data_available'] = True
                    enriched_symbol_data['current_price'] = current_price
                    
                    # Format technical context for agents
                    tech_context = TechnicalContextFormatter.format_technical_context_for_agents(ohlcv_summary, technical_indicators, current_price, "forex")
                    enriched_symbol_data['technical_context'] = tech_context
                else:
                    enriched_symbol_data['historical_data_available'] = False
                    enriched_symbol_data['current_price'] = current_price
                
                progress.update(task, description="Running multi-agent analysis with technical data...")
                
                # Use prediction engine with all agents including trading agent
                if hasattr(self, 'prediction_engine') and self.prediction_engine:
                    forex_analysis = await self.prediction_engine.predict(normalized_symbol, enriched_symbol_data)
                    
                    # Add market data to analysis results
                    if forex_analysis.get("success") and market_data:
                        forex_analysis["market_data"] = market_data
                else:
                    # Fallback to legacy analysis if prediction engine not available
                    forex_analysis = await self._run_forex_llm_analysis(symbol, enriched_symbol_data)
                
                progress.update(task, description="✓ Analysis complete")
            
            # Display analysis results
            if forex_analysis.get("success", False):
                await self._display_forex_analysis_results(symbol, forex_analysis)
            else:
                console.print(f"[red]AI analysis failed: {forex_analysis.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error analyzing forex: {e}[/red]")
            logger.error(f"Forex analysis error: {e}")
    
    def _process_ohlcv_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process OHLCV DataFrame to compute 30-day metrics."""
        try:
            if df.empty:
                return {}
            
            # Get recent close price
            recent_close = df['close'].iloc[-1]
            
            # Calculate 30-day price change percentage
            price_change_30d = ((recent_close - df['close'].iloc[0]) / df['close'].iloc[0]) * 100
            
            # Calculate annualized volatility
            daily_returns = df['close'].pct_change().dropna()
            volatility_30d = daily_returns.std() * np.sqrt(365) * 100
            
            # Volume analysis
            avg_volume_30d = df['volume'].mean()
            recent_volume = df['volume'].iloc[-1]
            volume_ratio = recent_volume / avg_volume_30d if avg_volume_30d > 0 else 1.0
            
            # Price range analysis
            high_30d = df['high'].max()
            low_30d = df['low'].min()
            
            return {
                'price_change_30d_pct': round(price_change_30d, 2),
                'volatility_30d_annualized': round(volatility_30d, 2),
                'high_30d': high_30d,
                'low_30d': low_30d,
                'avg_volume_30d': avg_volume_30d,
                'volume_ratio': round(volume_ratio, 2),
                'trading_days': len(df),
                'recent_close': recent_close
            }
            
        except Exception as e:
            logger.error(f"Error processing OHLCV data: {e}")
            return {}
    
    
    def _extract_indicators_from_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
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
                'ema_12': 'ema_12',
                'ema_26': 'ema_26',
                'stoch_k': 'stoch_k',
                'stoch_d': 'stoch_d',
                'atr': 'atr'
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
    
    
    async def _fetch_forex_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch forex data using MarketDataManager."""
        try:
            console.print("[cyan]Fetching live forex data...[/cyan]")
            
            # Normalize symbol format for MarketDataManager (remove slash)
            normalized_symbol = symbol.replace("/", "")
            
            # Ensure we have market_data_manager
            if not self.market_data_manager:
                return {'error': 'MarketDataManager not available'}
            
            # Get current market data
            market_overview = await self.market_data_manager.get_market_overview([normalized_symbol])
            forex_data = market_overview.get(normalized_symbol, {})
            
            if not forex_data or forex_data.get('price', 0) <= 0:
                return {'error': f'No forex data available for {symbol}'}
            
            # Create analysis structure compatible with existing display methods
            analysis = {
                'quote': {
                    'price': forex_data.get('price', 0),
                    'p': forex_data.get('price', 0),
                    'timestamp': int(datetime.now().timestamp() * 1000)
                },
                'daily_data': [],  # Will be populated from historical data if needed
                'hourly_data': [],
                'market_status': {
                    'currencies': {
                        'fx': 'open'  # Forex markets are generally always open
                    }
                },
                'news': []  # Could be enhanced with news data later
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error fetching forex data: {e}")
            return {'error': str(e)}
    
    async def _display_forex_data(self, symbol: str, analysis: Dict[str, Any]):
        """Display basic forex data from Polygon.io API."""
        # Display current quote
        quote = analysis.get('quote', {})
        if quote:
            console.print(f"\n[bold blue]{symbol} - Current Quote[/bold blue]")
            
            # Extract price data
            price = quote.get('price', quote.get('p', 0))
            if price:
                console.print(f"[bold]Current Price: {price:.5f}[/bold]")
            
            # Show timestamp if available
            timestamp = quote.get('timestamp', quote.get('t'))
            if timestamp:
                if isinstance(timestamp, (int, float)):
                    dt = datetime.fromtimestamp(timestamp / 1000)  # Convert from milliseconds
                    console.print(f"Last Updated: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Display daily data summary
        daily_data = analysis.get('daily_data', [])
        if daily_data and len(daily_data) > 0:
            console.print(f"\n[bold green]Recent Daily Performance:[/bold green]")
            
            daily_table = Table()
            daily_table.add_column("Date", style="cyan")
            daily_table.add_column("Open", style="white")
            daily_table.add_column("High", style="green")
            daily_table.add_column("Low", style="red")
            daily_table.add_column("Close", style="magenta")
            daily_table.add_column("Volume", style="yellow")
            
            for day in daily_data[:5]:  # Show last 5 days
                timestamp = day.get('t', 0)
                date = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d') if timestamp else 'N/A'
                
                daily_table.add_row(
                    date,
                    f"{day.get('o', 0):.5f}",
                    f"{day.get('h', 0):.5f}",
                    f"{day.get('l', 0):.5f}",
                    f"{day.get('c', 0):.5f}",
                    f"{day.get('v', 0):,.0f}"
                )
            
            console.print(daily_table)
        
        # Display market status
        market_status = analysis.get('market_status', {})
        if market_status:
            console.print(f"\n[bold cyan]Market Status:[/bold cyan]")
            
            fx_status = market_status.get('currencies', {})
            if fx_status:
                fx_open = fx_status.get('fx', 'unknown')
                console.print(f"Forex Market: [{'green' if fx_open == 'open' else 'red'}]{fx_open.title()}[/{'green' if fx_open == 'open' else 'red'}]")
        
        # Display recent news
        news = analysis.get('news', [])
        if news:
            console.print(f"\n[bold yellow]Recent Forex News ({len(news)} articles):[/bold yellow]")
            news_table = Table()
            news_table.add_column("Date", style="cyan")
            news_table.add_column("Title", style="white")
            news_table.add_column("Publisher", style="magenta")
            
            for article in news[:3]:  # Show top 3 news
                pub_date = article.get('published_utc', '')
                if pub_date:
                    try:
                        date = datetime.fromisoformat(pub_date.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                    except:
                        date = pub_date[:10]
                else:
                    date = 'N/A'
                
                title = article.get('title', 'N/A')[:60] + "..." if len(article.get('title', '')) > 60 else article.get('title', 'N/A')
                publisher = article.get('publisher', {}).get('name', 'N/A')
                
                news_table.add_row(date, title, publisher)
            
            console.print(news_table)
    
    async def _run_forex_llm_analysis(self, symbol: str, forex_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run LLM analysis on forex data."""
        try:
            # Calculate basic metrics from daily data
            daily_data = forex_data['daily_data']
            current_price = 0
            price_change = 0
            price_change_pct = 0
            
            if daily_data and len(daily_data) >= 2:
                current_price = daily_data[0].get('c', 0)
                previous_price = daily_data[1].get('c', 0)
                if previous_price > 0:
                    price_change = current_price - previous_price
                    price_change_pct = (price_change / previous_price) * 100
            
            # Prepare forex analysis context
            context = {
                'symbol': symbol,
                'asset_type': 'forex',
                'current_price': current_price,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'daily_data': daily_data,
                'hourly_data': forex_data['hourly_data'],
                'market_status': forex_data['market_status'],
                'news': forex_data['news']
            }
            
            agents_analysis = {}
            
            # Calculate technical metrics
            volatility = 0
            trend_direction = "neutral"
            
            if len(daily_data) >= 5:
                prices = [day.get('c', 0) for day in daily_data[:5]]
                if all(p > 0 for p in prices):
                    avg_price = sum(prices) / len(prices)
                    volatility = sum(abs(p - avg_price) for p in prices) / len(prices) / avg_price * 100
                    
                    if prices[0] > prices[-1]:
                        trend_direction = "bullish"
                    elif prices[0] < prices[-1]:
                        trend_direction = "bearish"
            
            # Technical Analysis with concise prompt
            try:
                technical_prompt = f"Analyze {symbol} forex pair: Price {context['current_price']:.5f}, Change {context['price_change_pct']:.2f}%, Volatility {volatility:.2f}%, Trend {trend_direction}. Provide brief technical outlook on momentum, volatility, and trend direction."
                
                technical_response = self.llm_client.generate_response([{"role": "user", "content": technical_prompt}])
                analysis_text = technical_response.get('content', str(technical_response)) if isinstance(technical_response, dict) else str(technical_response)
                
                agents_analysis['technical'] = {
                    'analysis': analysis_text,
                    'confidence': 75,
                    'signal': trend_direction
                }
            except Exception as e:
                logger.error(f"Technical analysis error: {e}")
                agents_analysis['technical'] = {'error': str(e)}
            
            # Fundamental Analysis with efficient prompt
            try:
                news_headlines = [article.get('title', '')[:80] for article in forex_data['news'][:2]]  # Limit to 2 headlines, 80 chars each
                news_text = '; '.join(news_headlines) if news_headlines else "No recent news"
                
                base_curr, quote_curr = symbol.split('/')
                fundamental_prompt = f"Fundamental outlook for {symbol}: Recent news: {news_text}. Analyze {base_curr} vs {quote_curr} strength, central bank policies, and economic factors. Brief assessment only."
                
                fundamental_response = self.llm_client.generate_response([{"role": "user", "content": fundamental_prompt}])
                analysis_text = fundamental_response.get('content', str(fundamental_response)) if isinstance(fundamental_response, dict) else str(fundamental_response)
                
                agents_analysis['fundamental'] = {
                    'analysis': analysis_text,
                    'confidence': 70,
                    'signal': 'neutral'
                }
            except Exception as e:
                logger.error(f"Fundamental analysis error: {e}")
                agents_analysis['fundamental'] = {'error': str(e)}
            
            # Risk Analysis with concise approach
            try:
                # Determine risk level based on volatility
                risk_level = "low"
                if volatility > 2.0:
                    risk_level = "high"
                elif volatility > 1.0:
                    risk_level = "medium"
                
                market_session = context['market_status'].get('currencies', {}).get('fx', 'unknown')
                risk_prompt = f"Risk assessment for {symbol}: Volatility {volatility:.2f}%, Change {context['price_change_pct']:.2f}%, Session {market_session}. Provide brief risk level, position sizing, and stop-loss recommendations."
                
                risk_response = self.llm_client.generate_response([{"role": "user", "content": risk_prompt}])
                analysis_text = risk_response.get('content', str(risk_response)) if isinstance(risk_response, dict) else str(risk_response)
                
                agents_analysis['risk'] = {
                    'analysis': analysis_text,
                    'confidence': 85,
                    'risk_level': risk_level
                }
            except Exception as e:
                logger.error(f"Risk analysis error: {e}")
                agents_analysis['risk'] = {'error': str(e)}
            
            # Generate final recommendation with efficient synthesis
            try:
                # Determine final signal based on agent outputs
                signals = [agent.get('signal', 'neutral') for agent in agents_analysis.values() if 'signal' in agent]
                bullish_signals = signals.count('bullish')
                bearish_signals = signals.count('bearish')
                
                if bullish_signals > bearish_signals:
                    final_signal = 'BUY'
                elif bearish_signals > bullish_signals:
                    final_signal = 'SELL'
                else:
                    final_signal = 'HOLD'
                
                # Concise final recommendation prompt
                tech_signal = agents_analysis.get('technical', {}).get('signal', 'neutral')
                risk_level = agents_analysis.get('risk', {}).get('risk_level', 'medium')
                
                final_prompt = f"Final recommendation for {symbol}: Technical signal {tech_signal}, Risk {risk_level}, Price {context['current_price']:.5f}, Change {context['price_change_pct']:.2f}%. Provide concise {final_signal} recommendation with entry strategy and risk management."
                
                final_response = self.llm_client.generate_response([{"role": "user", "content": final_prompt}])
                final_analysis_text = final_response.get('content', str(final_response)) if isinstance(final_response, dict) else str(final_response)
                
                avg_confidence = sum(agent.get('confidence', 0) for agent in agents_analysis.values() if 'confidence' in agent) / max(len([a for a in agents_analysis.values() if 'confidence' in a]), 1)
                
                return {
                    'success': True,
                    'agents_analysis': agents_analysis,
                    'final_recommendation': final_analysis_text,
                    'final_signal': final_signal,
                    'confidence': avg_confidence
                }
                
            except Exception as e:
                logger.error(f"Final recommendation error: {e}")
                return {'success': False, 'error': str(e)}
            
        except Exception as e:
            logger.error(f"Forex LLM analysis error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _display_forex_analysis_results(self, symbol: str, analysis: Dict[str, Any]):
        """Display forex analysis results with agent output handling."""
        try:
            console.print(f"\n[bold magenta]🤖 AI Analysis Results for {symbol}:[/bold magenta]")
            
            # Display market data summary if available
            market_data = analysis.get('market_data', {})
            if market_data:
                ohlcv_data = market_data.get('ohlcv_30d', {})
                if ohlcv_data:
                    console.print(f"\n[bold cyan]📊 30-Day Technical Summary:[/bold cyan]")
                    console.print(f"Price Change: {ohlcv_data.get('price_change_30d_pct', 0):+.2f}%")
                    console.print(f"Volatility: {ohlcv_data.get('volatility_30d_annualized', 0):.2f}% (annualized)")
                    console.print(f"Trading Days: {ohlcv_data.get('trading_days', 0)}")
                    console.print(f"Volume Ratio: {ohlcv_data.get('volume_ratio', 1.0):.2f}x")
            
            # Display agent results (check both prediction engine and legacy formats)
            agent_results = analysis.get('agent_results', {})  # Prediction engine format
            agents_results = analysis.get('agents_results', {})  # Alternative format
            agents_analysis = analysis.get('agents_analysis', {})  # Legacy format
            
            # Debug logging to see what we're getting
            # Use prediction engine results if available, otherwise fall back to legacy format
            agent_data = agent_results or agents_results or agents_analysis
            
            if agent_data:
                for agent_name, agent_result in agent_data.items():
                    if isinstance(agent_result, dict):
                        # Check if it's prediction engine format (has 'success' key) or legacy format
                        if agent_result.get('success', False) or 'analysis' in agent_result or 'content' in agent_result:
                            self._display_agent_result(agent_name, agent_result)
            
            # Display final recommendation if available
            final_recommendation = analysis.get('final_recommendation')
            if final_recommendation:
                console.print(f"\n[bold green]🎯 Final Recommendation:[/bold green]")
                console.print(final_recommendation)
            
            # Display confidence score if available
            confidence = analysis.get('confidence')
            if confidence:
                # Fix confidence percentage display
                if confidence <= 1.0:
                    console.print(f"\n[cyan]Overall Confidence: {confidence*100:.1f}%[/cyan]")
                else:
                    console.print(f"\n[cyan]Overall Confidence: {confidence:.1f}%[/cyan]")
                
        except Exception as e:
            console.print(f"[red]Error displaying analysis results: {e}[/red]")
            logger.error(f"Display analysis results error: {e}")
    
    
    def _display_agent_result(self, agent_name: str, result: Dict[str, Any]):
        """Display individual agent result with proper formatting."""
        try:
            # Agent name formatting
            agent_display_name = agent_name.replace('_', ' ').title()
            
            # Agent-specific icons
            agent_icons = {
                'sentiment': '😊',
                'news': '📰', 
                'risk': '⚠️',
                'trading': '💹',
                'technical': '📊',
                'fundamental': '🌍'
            }
            
            icon = agent_icons.get(agent_name.lower(), '🤖')
            console.print(f"\n[bold blue]{icon} {agent_display_name} Agent:[/bold blue]")
            
            # Check if this is a sentiment, news, or risk agent for special handling
            is_detailed_agent = any(keyword in agent_name.lower() for keyword in ['sentiment', 'news', 'risk'])
            is_trading_agent = 'trading' in agent_name.lower()
            
            # Display analysis content - handle both prediction engine and legacy formats
            analysis_content = result.get('analysis', '')
            detailed_analysis = result.get('detailed_analysis', '')
            summary = result.get('summary', '')
            
            # Check for prediction engine format (content field)
            prediction_content = result.get('content', '')
            
            trading_strategy = result.get('trading_strategy', '')
            position_analysis = result.get('position_analysis', '')
            raw_analysis = result.get('raw_analysis', '')
            
            # Get the best available content
            content_to_show = detailed_analysis or analysis_content or prediction_content or trading_strategy or position_analysis or raw_analysis or summary
            
            # Truncate verbose agent responses to prevent token overflow
            if content_to_show and len(content_to_show) > 1500:
                # For sentiment and news agents, truncate more aggressively
                if 'sentiment' in agent_name.lower() or 'news' in agent_name.lower():
                    content_to_show = content_to_show[:800] + "..."
                else:
                    content_to_show = content_to_show[:1500] + "..."
            
            # Handle trading agent with special formatting
            if is_trading_agent:
                from rich.table import Table
                agent_table = Table(show_header=False, box=None, padding=(0, 1))
                agent_table.add_column("Metric", style="cyan", width=20)
                agent_table.add_column("Value", style="white")
                from analyzers.technical_context import AgentDisplayFormatter
                AgentDisplayFormatter.display_trading_agent_results(result, agent_table)
                console.print(agent_table)
            elif is_detailed_agent:
                # Handle specific agent types with custom formatting
                from analyzers.technical_context import AgentDisplayFormatter
                from rich.table import Table
                agent_table = Table(show_header=False, box=None, padding=(0, 1))
                agent_table.add_column("Metric", style="cyan", width=20)
                agent_table.add_column("Value", style="white")
                
                if 'sentiment' in agent_name.lower():
                    AgentDisplayFormatter.display_sentiment_agent_results(result, agent_table)
                elif 'news' in agent_name.lower():
                    AgentDisplayFormatter.display_news_agent_results(result, agent_table)
                elif 'risk' in agent_name.lower():
                    AgentDisplayFormatter.display_risk_agent_results(result, agent_table)
                else:
                    # Fallback to text display
                    if content_to_show:
                        console.print(f"[white]{content_to_show}[/white]")
                        return
                
                console.print(agent_table)
            else:
                # For other agents, use truncation with longer limit
                if content_to_show:
                    if len(content_to_show) > 500:
                        content_to_show = content_to_show[:500] + "..."
                    console.print(f"[white]{content_to_show}[/white]")
            
            # Note: Confidence is displayed in AgentDisplayFormatter tables, no need for duplicate display here
            
            # Display signal if available
            signal = result.get('signal')
            if signal:
                signal_color = {
                    'BUY': 'green',
                    'SELL': 'red', 
                    'HOLD': 'yellow',
                    'bullish': 'green',
                    'bearish': 'red',
                    'neutral': 'yellow'
                }.get(signal.upper(), 'white')
                console.print(f"[{signal_color}]Signal: {signal.upper()}[/{signal_color}]")
                
        except Exception as e:
            console.print(f"[red]Error displaying {agent_name} result: {e}[/red]")
            logger.error(f"Display {agent_name} result error: {e}")
    
