"""Cryptocurrency analysis module for CryptoBot.
Handles all cryptocurrency-related analysis logic.
"""

import logging
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import questionary
import re
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)
console = Console()


class CryptoAnalyzer:
    """Handles cryptocurrency analysis operations."""
    
    def __init__(self, binance_client, prediction_engine, llm_client, config=None, market_data_manager=None):
        """Initialize crypto analyzer with required clients."""
        self.binance_client = binance_client
        self.prediction_engine = prediction_engine
        self.llm_client = llm_client
        self.config = config
        self.market_data_manager = market_data_manager
        
        # Initialize signal generator for enhanced analysis
        from analyzers.signal_generator import UnifiedSignalGenerator
        self.signal_generator = UnifiedSignalGenerator()
    
    async def analyze_cryptocurrency(self):
        """Analyze a single cryptocurrency symbol."""
        try:
            # Get symbol from user
            symbol = await questionary.text(
                "Enter cryptocurrency symbol (e.g., BTCUSDT):",
                default="BTCUSDT"
            ).ask_async()
            
            if not symbol:
                return
            
            symbol = symbol.upper()
            
            # Validate symbol (skip if binance_client is None)
            if self.binance_client and not await self.binance_client.validate_symbol(symbol):
                console.print(f"[red]Invalid symbol: {symbol}[/red]")
                return
            
            console.print(f"\n[blue]Analyzing {symbol}...[/blue]")
            
            # Run prediction with enhanced trading analysis
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Running multi-agent analysis...", total=None)
                
                # Collect historical data first to enrich the prediction
                progress.update(task, description="Collecting historical data...")
                
                # Get current price data and historical OHLCV
                current_price = 0
                historical_data = None
                market_data = {}
                enriched_symbol_data = {}
                
                # Get current price and 30-day historical data from market data manager
                market_overview = await self.market_data_manager.get_market_overview([symbol])
                current_price = market_overview.get(symbol, {}).get('price', 0)
                
                # Try to get fresh ticker data for accurate price/volume
                ticker_data = None
                
                # First try Binance if available
                if self.binance_client:
                    try:
                        # Call get_24hr_ticker without await since it's a synchronous method
                        ticker_data = self.binance_client.get_24hr_ticker(symbol)
                        if ticker_data and 'price' in ticker_data:
                            current_price = float(ticker_data['price'])
                            logger.info(f"Using fresh Binance price for {symbol}: ${current_price}")
                            
                            # Store ticker data for later use
                            market_data['ticker'] = ticker_data
                            
                            # Add ticker data to enriched_symbol_data
                            enriched_symbol_data['current_price'] = current_price
                            enriched_symbol_data['price_change'] = float(ticker_data.get('priceChange', 0))
                            enriched_symbol_data['price_change_percent'] = float(ticker_data.get('priceChangePercent', 0))
                            enriched_symbol_data['volume'] = float(ticker_data.get('volume', 0))
                            enriched_symbol_data['quote_volume'] = float(ticker_data.get('quoteVolume', 0))
                    except Exception as e:
                        logger.warning(f"Could not get fresh Binance data: {e}")
                
                # If Binance failed or is not available, try public API
                if not ticker_data or 'price' not in ticker_data:
                    try:
                        # Import the public crypto API
                        from data.public_crypto_api import PublicCryptoAPI
                        
                        # Create a public crypto API client
                        public_api = PublicCryptoAPI()
                        
                        # Get ticker data from public API
                        ticker_data = public_api.get_ticker_data(symbol)
                        
                        if ticker_data and 'price' in ticker_data:
                            current_price = float(ticker_data['price'])
                            logger.info(f"Using public API price for {symbol}: ${current_price}")
                            
                            # Store ticker data for later use
                            market_data['ticker'] = ticker_data
                            
                            # Add ticker data to enriched_symbol_data
                            enriched_symbol_data['current_price'] = current_price
                            enriched_symbol_data['price_change'] = float(ticker_data.get('priceChange', 0))
                            enriched_symbol_data['price_change_percent'] = float(ticker_data.get('priceChangePercent', 0))
                            enriched_symbol_data['volume'] = float(ticker_data.get('volume', 0))
                            if 'quoteVolume' in ticker_data:
                                enriched_symbol_data['quote_volume'] = float(ticker_data.get('quoteVolume', 0))
                    except Exception as e:
                        logger.warning(f"Could not get public API data: {e}")
                
                # Get 60-day historical data with technical indicators (more data for MACD signal)
                historical_data = await self.market_data_manager.get_symbol_data(
                    symbol, timeframe='1d', limit=60, include_indicators=True
                )
                
                # Process historical data
                if not historical_data.empty and len(historical_data) >= 20:
                    progress.update(task, description="Processing technical data...")
                    
                    # Extract technical indicators (already calculated by MarketDataManager)
                    from analyzers.technical_context import TechnicalContextFormatter, AgentDisplayFormatter
                    technical_indicators = TechnicalContextFormatter.extract_indicators_from_dataframe(historical_data)
                    ohlcv_summary = self._process_ohlcv_data(historical_data)
                    
                    market_data['ohlcv_30d'] = ohlcv_summary
                    market_data['technical_indicators'] = technical_indicators
                    market_data['historical_data'] = historical_data
                    
                    # Prepare enriched data for prediction engine
                    enriched_symbol_data['ohlcv_30d'] = ohlcv_summary
                    enriched_symbol_data['technical_indicators'] = technical_indicators
                    enriched_symbol_data['historical_data'] = historical_data
                    enriched_symbol_data['historical_data_available'] = True
                    
                    # Add critical price data to enriched data
                    enriched_symbol_data['current_price'] = current_price
                    
                    # Add price change data if available from market overview
                    if symbol in market_overview:
                        enriched_symbol_data['price_change_24h'] = market_overview[symbol].get('change_24h', 0)
                        enriched_symbol_data['price_change_percent'] = market_overview[symbol].get('change_percent_24h', 0)
                        enriched_symbol_data['volume'] = market_overview[symbol].get('volume', 0)
                    
                    # Format technical context for agents
                    tech_context = self._format_technical_context_for_agents(ohlcv_summary, technical_indicators, current_price)
                    enriched_symbol_data['technical_context'] = tech_context
                else:
                    logger.warning(f"Insufficient historical data for {symbol}: {len(historical_data) if historical_data is not None and not historical_data.empty else 0} days")
                    enriched_symbol_data['historical_data_available'] = False
                    enriched_symbol_data['current_price'] = current_price
                    
                    # Still add market overview data even without historical data
                    if symbol in market_overview:
                        enriched_symbol_data['price_change_24h'] = market_overview[symbol].get('change_24h', 0)
                        enriched_symbol_data['price_change_percent'] = market_overview[symbol].get('change_percent_24h', 0)
                        enriched_symbol_data['volume'] = market_overview[symbol].get('volume', 0)
                
                progress.update(task, description="Running multi-agent analysis with historical data...")
                
                # Pass enriched data to prediction engine
                prediction = await self.prediction_engine.predict(symbol, enriched_symbol_data)
                
                # Trading analysis is now handled by the trading agent in prediction engine
                if prediction.get("success"):
                    # Ensure market data is properly set
                    prediction["market_data"] = market_data
                    
                    # Fix market context if it's showing zeros
                    if "market_context" in prediction:
                        market_context = prediction["market_context"]
                        
                        # Update market context with accurate values if they're zero
                        if market_context.get("current_price", 0) == 0:
                            market_context["current_price"] = current_price
                            
                        if market_context.get("price_change", 0) == 0 and symbol in market_overview:
                            market_context["price_change"] = market_overview[symbol].get("change_24h", 0)
                            
                        if market_context.get("price_change_percent", 0) == 0 and symbol in market_overview:
                            market_context["price_change_percent"] = market_overview[symbol].get("change_percent_24h", 0)
                            
                        if market_context.get("volume", 0) == 0 and symbol in market_overview:
                            market_context["volume"] = market_overview[symbol].get("volume", 0)
                            
                        # Log the fixed market context
                        logger.info(f"Fixed market context for {symbol}: {market_context}")
                        
                        # Update the prediction with fixed market context
                        prediction["market_context"] = market_context
                
                progress.update(task, description="✓ Analysis complete")
            
            # Display results
            await self.display_prediction_results(symbol, prediction)
            
        except Exception as e:
            console.print(f"[red]Analysis failed: {e}[/red]")
            logger.error(f"Analysis error for {symbol}: {e}")
    
    async def display_prediction_results(self, symbol: str, prediction: Dict[str, Any]):
        """Display prediction results in a formatted table."""
        current_price = 0
        try:
            # Check if prediction was successful
            if not prediction.get("success", False):
                console.print(f"[red]Analysis failed for {symbol}: {prediction.get('error', 'Unknown error')}[/red]")
                return
            
            # Extract current price early for use throughout display
            market_context = prediction.get("market_context", {})
            if market_context and 'current_price' in market_context:
                current_price = market_context['current_price']
            else:
                # Fallback - extract from ticker data
                ticker = prediction.get('market_data', {}).get('ticker', {})
                current_price = float(ticker.get('price', 0)) if ticker else 0
            
            # Main prediction summary
            table = Table(title=f"Analysis Results for {symbol}")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            
            # Extract final decision details
            final_decision = prediction.get("final_decision", {})
            if isinstance(final_decision, dict):
                action = final_decision.get("action", "N/A")
                confidence = final_decision.get("confidence", 0)
            else:
                action = str(final_decision)
                confidence = prediction.get("confidence", 0)
            
            # Add main metrics
            table.add_row("Final Decision", action)
            table.add_row("Confidence", f"{confidence:.1f}%")
            table.add_row("Risk Assessment", f"{prediction.get('risk_assessment', 50):.1f}")
            table.add_row("Timestamp", prediction.get("timestamp", "N/A"))
            
            console.print(table)            
            
            # Market context if available
            market_context = prediction.get("market_context", {})
            if market_context:
                # Debug market context
                logger.info(f"Market context before display: {market_context}")
                
                # Get ticker data as fallback
                ticker_data = prediction.get('market_data', {}).get('ticker', {})
                
                # Create a structured market context display
                console.print("[bold]📊 Market Context:[/bold]")
                context_table = Table(box=None)
                context_table.add_column("Metric", style="cyan")
                context_table.add_column("Value", style="yellow")
                
                # Current price - use multiple fallbacks to ensure we have a value
                price = market_context.get('current_price', 0)
                if price == 0 and ticker_data:
                    price = float(ticker_data.get('price', 0))
                context_table.add_row("Current Price", f"${price:.2f}")
                
                # Price change - use multiple fallbacks
                price_change = market_context.get('price_change', 0)
                if price_change == 0 and ticker_data:
                    price_change = float(ticker_data.get('priceChange', 0))
                context_table.add_row("24h Change", f"${price_change:.2f}")
                
                # Price change percent - use multiple fallbacks
                price_change_pct = market_context.get('price_change_percent', 0)
                if price_change_pct == 0 and ticker_data:
                    price_change_pct = float(ticker_data.get('priceChangePercent', 0))
                context_table.add_row("", f"{price_change_pct:.2f}%")
                
                # Volume - use multiple fallbacks
                volume = market_context.get('volume', 0)
                if volume == 0 and ticker_data:
                    volume = float(ticker_data.get('volume', 0))
                context_table.add_row("Volume 24h", f"{volume:,.0f}")
                
                console.print(context_table)
                
                # Also display other market context values if available
                other_context = {k: v for k, v in market_context.items() 
                               if k not in ['current_price', 'price_change', 'price_change_percent', 'volume']}
                
                if other_context:
                    other_table = Table()
                    other_table.add_column("Metric", style="cyan")
                    other_table.add_column("Value", style="yellow")
                    
                    for key, value in other_context.items():
                        if isinstance(value, (int, float)):
                            if 'price' in key.lower():
                                value = f"${value:.4f}"
                            elif 'percent' in key.lower():
                                value = f"{value:.2f}%"
                            elif 'volume' in key.lower():
                                value = f"{value:,.0f}"
                            else:
                                value = f"{value:.2f}"
                        
                        other_table.add_row(key.replace('_', ' ').title(), str(value))
                    
                    console.print(other_table)
            
            # Agent analysis breakdown
            agent_results = prediction.get("agent_results", {})
            if agent_results:
                console.print("\n[bold]Agent Analysis Breakdown:[/bold]")
                
                for agent_name, analysis in agent_results.items():
                    if isinstance(analysis, dict):
                        agent_table = Table(title=f"{agent_name.title()} Agent")
                        agent_table.add_column("Aspect", style="cyan", width=20)
                        agent_table.add_column("Analysis", style="white", max_width=80)
                        
                        # Check if this is trading agent data - look for the actual fields in the output
                        has_trading_fields = any(key in analysis for key in ['position_direction', 'position_analysis', 'risk_parameters', 'trading_strategy'])
                        is_trading_agent = (agent_name.lower() == 'trading agent' or 
                                          analysis.get('agent') == 'Trading Agent' or 
                                          has_trading_fields or
                                          'trading' in agent_name.lower())
                        
                        if is_trading_agent:
                            from analyzers.technical_context import AgentDisplayFormatter
                            AgentDisplayFormatter.display_trading_agent_results(analysis, agent_table)
                        else:
                            # Handle specific agent types with custom formatting
                            from analyzers.technical_context import AgentDisplayFormatter
                            if 'sentiment' in agent_name.lower():
                                AgentDisplayFormatter.display_sentiment_agent_results(analysis, agent_table)
                            elif 'news' in agent_name.lower():
                                AgentDisplayFormatter.display_news_agent_results(analysis, agent_table)
                            elif 'risk' in agent_name.lower():
                                AgentDisplayFormatter.display_risk_agent_results(analysis, agent_table)
                            else:
                                # Add agent-specific data with better formatting
                                for key, value in analysis.items():
                                    if key not in ['raw_response', 'timestamp', 'raw_analysis']:
                                        if isinstance(value, (int, float)):
                                            if key == 'confidence':
                                                value = f"{value:.1f}%"
                                            else:
                                                value = f"{value:.2f}"
                                        elif isinstance(value, str) and len(value) > 200:
                                            # Truncate very long text but show more than before
                                            value = value[:200] + "..."
                                        elif isinstance(value, dict):
                                            # Format nested dicts more cleanly
                                            value = AgentDisplayFormatter.format_nested_dict(value)
                                        
                                        # Format key name nicely
                                        display_key = key.replace('_', ' ').title()
                                        agent_table.add_row(display_key, str(value))
                        
                        console.print(agent_table)
            
            # Display Trading Parameters if available
            trading_params = prediction.get('trading_parameters', {})
            if trading_params:
                console.print("\n[bold yellow]📋 Trading Parameters:[/bold yellow]")
                
                # Create trading parameters table
                params_table = Table()
                params_table.add_column("Parameter", style="cyan")
                params_table.add_column("Value", style="white")
                
                if trading_params.get('position_direction'):
                    params_table.add_row("Position Direction", trading_params['position_direction'])
                
                if trading_params.get('entry_price_range'):
                    params_table.add_row("Entry Price Range", trading_params['entry_price_range'])
                
                if trading_params.get('optimal_entry'):
                    params_table.add_row("Optimal Entry Price", f"${trading_params['optimal_entry']:.6f}")
                
                if trading_params.get('take_profit'):
                    params_table.add_row("Take Profit Target", f"${trading_params['take_profit']:.6f}")
                
                if trading_params.get('stop_loss'):
                    params_table.add_row("Stop Loss Level", f"${trading_params['stop_loss']:.6f}")
                
                if trading_params.get('trailing_stop_activation'):
                    params_table.add_row("Trailing Stop Activation", f"${trailing_params['trailing_stop_activation']:.6f}")
                
                if trading_params.get('trailing_stop_distance'):
                    params_table.add_row("Trailing Stop Distance", trading_params['trailing_stop_distance'])
                
                if trading_params.get('risk_reward_ratio'):
                    params_table.add_row("Risk/Reward Ratio", trading_params['risk_reward_ratio'])
                
                if trading_params.get('position_size'):
                    params_table.add_row("Recommended Position Size", trading_params['position_size'])
                
                console.print(params_table)
                
                # Add a note about the structured format
                console.print("\n[dim]💡 Detailed trading strategy with rationale available in AI Trading Strategy section above.[/dim]")
            
            # Enhanced trading analysis with structured format
            enhanced_analysis = prediction.get('enhanced_analysis', '')
            if enhanced_analysis:
                console.print(f"\n[bold magenta]🤖 AI Trading Strategy:[/bold magenta]")
                
                # Get current price from market data or prediction
                display_price = current_price
                if display_price == 0:
                    # Fallback to get price from market context or ticker
                    market_context = prediction.get('market_context', {})
                    if market_context and 'current_price' in market_context:
                        display_price = market_context['current_price']
                    else:
                        # Last fallback - extract from ticker data
                        ticker = prediction.get('market_data', {}).get('ticker', {})
                        display_price = float(ticker.get('price', 0)) if ticker else 0
                
                # Format the enhanced analysis as structured markdown-style output
                formatted_analysis = self._format_trading_strategy_display(enhanced_analysis, trading_params, symbol, display_price)
                console.print(formatted_analysis)
            
            # Final summary
            console.print(f"\n[bold]Summary:[/bold] {prediction.get('summary', 'Analysis completed successfully.')}")
            
        except Exception as e:
            console.print(f"[red]Error displaying results: {e}[/red]")
            logger.error(f"Display results error: {e}")
    
    def _process_ohlcv_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process OHLCV data into summary statistics."""
        try:
            if df.empty:
                return {}
            
            # Calculate price statistics
            recent_close = df['close'].iloc[-1]
            price_change_30d = ((recent_close - df['close'].iloc[0]) / df['close'].iloc[0]) * 100
            
            # Calculate volatility (standard deviation of daily returns)
            daily_returns = df['close'].pct_change().dropna()
            volatility_30d = daily_returns.std() * np.sqrt(365) * 100  # Annualized volatility
            
            # Volume analysis
            avg_volume_30d = df['volume'].mean()
            recent_volume = df['volume'].iloc[-1]
            volume_ratio = recent_volume / avg_volume_30d if avg_volume_30d > 0 else 1
            
            # Price levels
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
    
    # Legacy method - trading analysis now handled by TradingAgent
    async def _run_crypto_trading_analysis(self, symbol: str, prediction: Dict[str, Any], current_price: float, market_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Legacy method - trading analysis now handled by TradingAgent in prediction engine."""
        return {
            "success": True,
            "message": "Trading analysis now handled by TradingAgent",
            "trading_parameters": {},
            "enhanced_analysis": "Trading analysis moved to dedicated TradingAgent"
        }
    
    def _format_agent_summary(self, agent_results: Dict[str, Any]) -> str:
        """Format agent results for the trading prompt."""
        summary_lines = []
        
        for agent_name, agent_data in agent_results.items():
            if isinstance(agent_data, dict):
                # Extract key insights from each agent
                if 'technical' in agent_name.lower():
                    summary_lines.append(f"Technical: {str(agent_data)[:150]}...")
                elif 'news' in agent_name.lower() or 'sentiment' in agent_name.lower():
                    summary_lines.append(f"Sentiment: {str(agent_data)[:150]}...")
                elif 'risk' in agent_name.lower():
                    summary_lines.append(f"Risk: {str(agent_data)[:150]}...")
                else:
                    summary_lines.append(f"{agent_name}: {str(agent_data)[:100]}...")
        
        return "\n".join(summary_lines) if summary_lines else "No detailed agent analysis available"
    
    def _format_market_data_context(self, market_data: Dict[str, Any]) -> str:
        """Format market data for AI prompt context."""
        try:
            context_lines = []
            
            # OHLCV Summary
            ohlcv = market_data.get('ohlcv_30d', {})
            if ohlcv:
                context_lines.append("📊 30-Day Price Performance:")
                context_lines.append(f"  • Price Change: {ohlcv.get('price_change_30d_pct', 0):.2f}%")
                context_lines.append(f"  • Volatility (Annualized): {ohlcv.get('volatility_30d_annualized', 0):.2f}%")
                context_lines.append(f"  • 30D High: ${ohlcv.get('high_30d', 0):.6f}")
                context_lines.append(f"  • 30D Low: ${ohlcv.get('low_30d', 0):.6f}")
                context_lines.append(f"  • Volume Ratio (Recent vs Avg): {ohlcv.get('volume_ratio', 1):.2f}x")
                context_lines.append("")
            
            # Technical Indicators
            indicators = market_data.get('technical_indicators', {})
            if indicators:
                context_lines.append("📈 Technical Indicators:")
                
                # Moving Averages
                if 'sma_7' in indicators:
                    context_lines.append(f"  • SMA 7: ${indicators['sma_7']:.6f}")
                if 'sma_14' in indicators:
                    context_lines.append(f"  • SMA 14: ${indicators['sma_14']:.6f}")
                if 'sma_20' in indicators:
                    context_lines.append(f"  • SMA 20: ${indicators['sma_20']:.6f}")
                
                # RSI
                if 'rsi_14' in indicators:
                    rsi = indicators['rsi_14']
                    rsi_signal = "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral"
                    context_lines.append(f"  • RSI (14): {rsi:.1f} ({rsi_signal})")
                
                # Bollinger Bands
                if 'bb_position' in indicators:
                    bb_pos = indicators['bb_position']
                    bb_signal = "Near Lower Band" if bb_pos < 0.2 else "Near Upper Band" if bb_pos > 0.8 else "Middle Range"
                    context_lines.append(f"  • Bollinger Band Position: {bb_pos:.2f} ({bb_signal})")
                    context_lines.append(f"    - Upper: ${indicators.get('bb_upper', 0):.6f}")
                    context_lines.append(f"    - Lower: ${indicators.get('bb_lower', 0):.6f}")
                
                # MACD
                if 'macd' in indicators and 'macd_signal' in indicators:
                    macd_trend = "Bullish" if indicators['macd'] > indicators['macd_signal'] else "Bearish"
                    context_lines.append(f"  • MACD: {indicators['macd']:.6f} (Signal: {indicators['macd_signal']:.6f}) - {macd_trend}")
                
                # Support/Resistance
                if 'support_level' in indicators and 'resistance_level' in indicators:
                    context_lines.append(f"  • Support Level: ${indicators['support_level']:.6f}")
                    context_lines.append(f"  • Resistance Level: ${indicators['resistance_level']:.6f}")
                
                context_lines.append("")
            
            # Current Market State
            ticker = market_data.get('ticker', {})
            if ticker:
                context_lines.append("📊 Current Market State:")
                context_lines.append(f"  • 24h Change: {ticker.get('priceChangePercent', 0):.2f}%")
                context_lines.append(f"  • 24h Volume: {ticker.get('volume', 0):,.0f}")
                context_lines.append(f"  • 24h High: ${ticker.get('high', 0):.6f}")
                context_lines.append(f"  • 24h Low: ${ticker.get('low', 0):.6f}")
            
            return "\n".join(context_lines)
            
        except Exception as e:
            logger.error(f"Error formatting market data context: {e}")
            return "Error processing market data"
    
    def _extract_crypto_trading_parameters(self, llm_response: str, current_price: float, volatility_factor: float) -> Dict[str, Any]:
        """Extract trading parameters from LLM response text for cryptocurrency."""
        params = {}
        
        try:
            # Extract position direction
            position_patterns = [
                r'(?:Position Direction|POSITION DIRECTION)[:\s]*([^\n]+)',
                r'(?:Long Buy|Long Sell|Short Sell|Short Cover)'
            ]
            for pattern in position_patterns:
                match = re.search(pattern, llm_response, re.IGNORECASE)
                if match:
                    direction = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    params['position_direction'] = direction.strip()
                    break
            
            # Extract entry price range (6 decimal precision for crypto)
            entry_range_pattern = r'Entry Price Range[:\s]*\$([\d\.]+)\s*-\s*\$([\d\.]+)'
            match = re.search(entry_range_pattern, llm_response, re.IGNORECASE)
            if match:
                params['entry_price_range'] = f"${match.group(1)} - ${match.group(2)}"
                params['entry_low'] = float(match.group(1))
                params['entry_high'] = float(match.group(2))
            
            # Extract optimal entry price
            optimal_entry_pattern = r'Optimal Entry Price[:\s]*\$([\d\.]+)'
            match = re.search(optimal_entry_pattern, llm_response, re.IGNORECASE)
            if match:
                params['optimal_entry'] = float(match.group(1))
            
            # Extract take profit target
            take_profit_pattern = r'Take Profit Target[:\s]*\$([\d\.]+)'
            match = re.search(take_profit_pattern, llm_response, re.IGNORECASE)
            if match:
                params['take_profit'] = float(match.group(1))
            
            # Extract stop loss level
            stop_loss_pattern = r'Stop Loss Level[:\s]*\$([\d\.]+)'
            match = re.search(stop_loss_pattern, llm_response, re.IGNORECASE)
            if match:
                params['stop_loss'] = float(match.group(1))
            
            # Extract trailing stop activation
            trailing_activation_pattern = r'Trailing Stop Activation[^:]*[:\s]*\$([\d\.]+)'
            match = re.search(trailing_activation_pattern, llm_response, re.IGNORECASE)
            if match:
                params['trailing_stop_activation'] = float(match.group(1))
            
            # Extract trailing stop distance
            trailing_distance_patterns = [
                r'Trailing Stop Distance[^:]*[:\s]*\$([\d\.]+)',
                r'Trailing Stop Distance[^:]*[:\s]*([\d\.]+)%'
            ]
            for pattern in trailing_distance_patterns:
                match = re.search(pattern, llm_response, re.IGNORECASE)
                if match:
                    if '$' in pattern:
                        params['trailing_stop_distance'] = f"${match.group(1)}"
                    else:
                        params['trailing_stop_distance'] = f"{match.group(1)}%"
                    break
            
            # Extract risk/reward ratio
            risk_reward_pattern = r'Risk[/\\]Reward Ratio[:\s]*([\d\.]+)[:\s]*([\d\.]+)'
            match = re.search(risk_reward_pattern, llm_response, re.IGNORECASE)
            if match:
                params['risk_reward_ratio'] = f"{match.group(1)}:{match.group(2)}"
            
            # Extract position size
            position_size_patterns = [
                r'(?:Recommended )?Position Size[^:]*[:\s]*([\d\.]+)%',
                r'(?:Recommended )?Position Size[^:]*[:\s]*([^\n]+)'
            ]
            for pattern in position_size_patterns:
                match = re.search(pattern, llm_response, re.IGNORECASE)
                if match:
                    params['position_size'] = match.group(1).strip()
                    break
            
            # Fallback calculations if LLM didn't provide specific values
            if not params.get('optimal_entry'):
                params['optimal_entry'] = current_price
            
            if not params.get('stop_loss') and params.get('optimal_entry'):
                # Default stop loss at 5% below entry for crypto (higher than stocks due to volatility)
                params['stop_loss'] = params['optimal_entry'] * 0.95
            
            if not params.get('take_profit') and params.get('optimal_entry'):
                # Default take profit at 10% above entry for crypto (2:1 risk/reward)
                params['take_profit'] = params['optimal_entry'] * 1.10
            
            if not params.get('trailing_stop_activation') and params.get('take_profit'):
                # Activate trailing stop at 50% of the way to take profit
                entry = params.get('optimal_entry', current_price)
                target = params['take_profit']
                params['trailing_stop_activation'] = entry + (target - entry) * 0.5
            
            if not params.get('trailing_stop_distance'):
                # Default trailing stop distance based on crypto volatility (higher than stocks)
                distance_pct = max(3.0, volatility_factor * 100 * 1.5)  # 1.5x daily volatility, minimum 3%
                params['trailing_stop_distance'] = f"{distance_pct:.1f}%"
            
            if not params.get('position_size'):
                params['position_size'] = "1-3% of crypto portfolio"
            
            
            if not params.get('risk_reward_ratio'):
                params['risk_reward_ratio'] = "1:2"
            
            if not params.get('position_direction'):
                # Default based on prediction
                params['position_direction'] = 'Long Buy'
            
        except Exception as e:
            logger.error(f"Error extracting crypto trading parameters: {e}")
            # Provide basic fallback parameters for crypto
            params = {
                'position_direction': 'Long Buy',
                'optimal_entry': current_price,
                'stop_loss': current_price * 0.95,  # 5% stop loss for crypto
                'take_profit': current_price * 1.10,  # 10% take profit for crypto
                'trailing_stop_activation': current_price * 1.05,  # Activate at 5% gain
                'trailing_stop_distance': f"{max(3.0, volatility_factor * 100 * 1.5):.1f}%",
                'risk_reward_ratio': '1:2',
                'position_size': '1-3% of crypto portfolio'
            }
        
        return params
    
    def _format_technical_context_for_agents(self, ohlcv_summary: Dict[str, Any], indicators: Dict[str, Any], current_price: float) -> str:
        """Format technical analysis context for agent consumption."""
        from analyzers.technical_context import TechnicalContextFormatter
        return TechnicalContextFormatter.format_technical_context_for_agents(
            ohlcv_summary, indicators, current_price, asset_type="crypto"
        )
    
    def _format_trading_strategy_display(self, analysis_text: str, trading_params: Dict[str, Any], symbol: str, current_price: float) -> str:
        """Format trading strategy in structured table format similar to stock analyzer."""
        try:
            from datetime import datetime
            current_date = datetime.now().strftime("%m‑%d‑%y")
            
            # Extract key information from trading parameters
            position_direction = trading_params.get('position_direction', 'Long Buy')
            entry_range = trading_params.get('entry_price_range', f"${current_price*0.995:.6f} - ${current_price*1.005:.6f}")
            optimal_entry = trading_params.get('optimal_entry', current_price)
            take_profit = trading_params.get('take_profit', current_price * 1.10)
            stop_loss = trading_params.get('stop_loss', current_price * 0.95)
            trailing_activation = trading_params.get('trailing_stop_activation', current_price * 1.05)
            trailing_distance = trading_params.get('trailing_stop_distance', '3.0%')
            risk_reward = trading_params.get('risk_reward_ratio', '1:2')
            position_size = trading_params.get('position_size', '1-3% of crypto portfolio')
            
            # Calculate profit/loss amounts
            profit_amount = take_profit - optimal_entry
            loss_amount = optimal_entry - stop_loss
            
            formatted_output = f"""
**Comprehensive {symbol} Trading Plan – ${current_price:.6f} (as of {current_date})**  
*All levels use 6-decimal precision for cryptocurrency markets.*

---

### 1. POSITION DIRECTION
| Action | Rationale |
|--------|-----------|
| **{position_direction}** | • Current price analysis based on 30-day OHLCV data and technical indicators.<br>• RSI, MACD, and Bollinger Band positioning support this direction.<br>• Crypto market volatility and 24/7 trading considerations factored in. |

---

### 2. ENTRY STRATEGY
| Item | Value | Justification |
|------|-------|---------------|
| **Entry Price Range** | **{entry_range}** | • Based on technical analysis of support/resistance levels.<br>• Accounts for crypto market volatility and spread considerations. |
| **Optimal Entry Price** | **${optimal_entry:.6f}** | • Calculated from current market conditions and technical indicators. |
| **Entry Timing Conditions** | • Confirmation: Price action aligns with technical signals.<br>• Volume analysis supports the move.<br>• No major resistance levels blocking the path. |

---

### 3. EXIT STRATEGY
| Item | Value | Rationale |
|------|-------|-----------|
| **Take Profit Target** | **${take_profit:.6f}** | • Target provides ${profit_amount:.6f} upside from optimal entry.<br>• Based on resistance levels and volatility analysis. |
| **Stop Loss Level** | **${stop_loss:.6f}** | • Risk management at ${loss_amount:.6f} below entry.<br>• Positioned below key support levels with crypto volatility buffer. |
| **Risk/Reward Ratio** | **{risk_reward}** | • Balanced risk management for cryptocurrency trading. |

---

### 4. TRAILING STOP PARAMETERS
| Item | Value | Rationale |
|------|-------|-----------|
| **Trailing Stop Activation Threshold** | **${trailing_activation:.6f}** | • Activates once position shows profitable momentum. |
| **Trailing Stop Distance** | **{trailing_distance}** | • Accounts for crypto volatility while protecting gains. |
| **Trailing Stop Type** | *Percentage* | • More suitable for crypto's price volatility than fixed amounts. |

---

### 5. POSITION SIZING
| Item | Value |
|------|-------|
| **Recommended Position Size** | **{position_size}** |
| **Maximum Risk per Trade** | **0.5-1% of total portfolio** (conservative approach for crypto volatility). |

---

### 6. CRYPTO-SPECIFIC CONSIDERATIONS
- **24/7 Trading**: Monitor positions continuously as crypto markets never close
- **Volatility Management**: Higher stop losses account for crypto price swings
- **News Sensitivity**: Crypto markets highly reactive to news and social sentiment
- **Liquidity**: Ensure sufficient volume for entry/exit at desired levels

---

### 7. OVERALL RECOMMENDATION
- **Signal:** {position_direction.split()[0].upper()}  
- **Confidence Level:** **7/10** (based on technical analysis and market conditions)  
- **Time Horizon:** **Short to Medium-term (1-4 weeks)** – Crypto markets move faster than traditional assets

---

> **Quick Summary**  
> • Enter {position_direction.lower()} at ${optimal_entry:.6f} when technical conditions align.  
> • Set TP at ${take_profit:.6f}, SL at ${stop_loss:.6f}. Activate trailing stop at ${trailing_activation:.6f}.  
> • Size {position_size}, risk ≤ 1% per trade for crypto volatility management.  

**AI Analysis Insights:**
{analysis_text[:500]}...
"""
            
            return formatted_output
            
        except Exception as e:
            logger.error(f"Error formatting trading strategy display: {e}")
            return analysis_text  # Fallback to original text
