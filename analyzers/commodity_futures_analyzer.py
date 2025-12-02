"""
Commodity futures analysis module for CryptoBot.
Handles all commodity futures-related analysis logic.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import questionary

from data.universal_cache import UniversalCache

logger = logging.getLogger(__name__)
console = Console()


class CommodityFuturesAnalyzer:
    """Handles commodity futures analysis operations."""
    
    def __init__(self, commodity_client, llm_client, config=None):
        """Initialize commodity futures analyzer with required clients."""
        self.commodity_client = commodity_client
        self.llm_client = llm_client
        self.config = config
        self.cache = UniversalCache(config) if config else None
    
    async def analyze_commodity(self):
        """Analyze a single commodity futures contract."""
        try:
            # Check if commodity client is available
            if not self.commodity_client:
                console.print("[red]Error: Commodity data client not configured[/red]")
                console.print("[cyan]Please set ALPHA_VANTAGE_API_KEY in your .env file[/cyan]")
                return
            
            # Show commodity selection options
            choice = await questionary.select(
                "Choose commodity analysis method:",
                choices=[
                    "category - Browse by commodity category",
                    "major - Select from major commodities",
                    "custom - Enter custom commodity symbol"
                ]
            ).ask_async()
            
            if not choice:
                return
            
            symbol = None
            commodity_name = None
            
            if choice.startswith("category"):
                # Browse by category
                category = await questionary.select(
                    "Select commodity category:",
                    choices=[
                        "Energy - Oil, Gas, Heating Oil",
                        "Precious Metals - Gold, Silver, Platinum",
                        "Base Metals - Copper, Aluminum",
                        "Agriculture - Corn, Wheat, Soybeans",
                        "Livestock - Cattle, Hogs"
                    ]
                ).ask_async()
                
                if not category:
                    return
                
                category_name = category.split(" - ")[0]
                commodities = [c for c in self.commodity_client.get_major_commodities() 
                             if c["category"] == category_name]
                
                if commodities:
                    choices = [f"{c['name']} ({c['symbol']})" for c in commodities]
                    selection = await questionary.select(
                        f"Select {category_name} commodity:",
                        choices=choices
                    ).ask_async()
                    
                    if selection:
                        commodity_name = selection.split(" (")[0]
                        symbol = selection.split("(")[1].replace(")", "")
                        
            elif choice.startswith("major"):
                # Show all major commodities
                commodities = self.commodity_client.get_major_commodities()
                choices = [f"{c['name']} ({c['symbol']}) - {c['category']}" for c in commodities]
                
                selection = await questionary.select(
                    "Select a major commodity:",
                    choices=choices
                ).ask_async()
                
                if selection:
                    commodity_name = selection.split(" (")[0]
                    symbol = selection.split("(")[1].split(")")[0]
                    
            else:
                # Custom symbol entry
                symbol = await questionary.text(
                    "Enter commodity symbol (e.g., GC=F for Gold, CL=F for Crude Oil):",
                    default="GC=F"
                ).ask_async()
                commodity_name = symbol
            
            if not symbol:
                return
            
            console.print(f"[yellow]Analyzing commodity: {commodity_name or symbol}[/yellow]")
            console.print(f"[cyan]Using Interactive Brokers priority for commodity data...[/cyan]")
            
            # Check cache first
            if self.cache:
                cached_analysis = self.cache.get("commodities", symbol, symbol=symbol, name=commodity_name)
                if cached_analysis:
                    console.print(f"[cyan]Using cached commodity data for {symbol}[/cyan]")
                    # Debug: Print cached pricing data
                    quote = cached_analysis.get('quote', {})
                    daily_data = cached_analysis.get('daily_data', [])
                    console.print(f"[yellow]DEBUG - Cached quote data: {quote}[/yellow]")
                    console.print(f"[yellow]DEBUG - Cached daily data length: {len(daily_data)}[/yellow]")
                    
                    # If cached data is empty, clear cache and fetch fresh data
                    if not quote and not daily_data:
                        console.print(f"[red]Cached data is empty, clearing cache and fetching fresh data[/red]")
                        self.cache.invalidate("commodities", symbol)
                        analysis = await self._fetch_commodity_data(symbol)
                        # Cache the fresh result
                        if analysis and 'error' not in analysis:
                            self.cache.set("commodities", symbol, analysis, symbol=symbol, name=commodity_name)
                    else:
                        analysis = cached_analysis
                        if daily_data:
                            console.print(f"[yellow]DEBUG - First daily entry: {daily_data[0]}[/yellow]")
                else:
                    console.print(f"[green]Fetching fresh data with IB-first approach...[/green]")
                    analysis = await self._fetch_commodity_data(symbol)
                    # Debug: Print fresh data after fetch
                    if analysis:
                        quote = analysis.get('quote', {})
                        daily_data = analysis.get('daily_data', [])
                        console.print(f"[green]DEBUG - Fresh quote data: {quote}[/green]")
                        console.print(f"[green]DEBUG - Fresh daily data length: {len(daily_data)}[/green]")
                        if daily_data:
                            console.print(f"[green]DEBUG - First fresh daily entry: {daily_data[0]}[/green]")
                    # Cache the result
                    if analysis and 'error' not in analysis:
                        self.cache.set("commodities", symbol, analysis, symbol=symbol, name=commodity_name)
            else:
                console.print(f"[green]Fetching data with IB-first approach (no cache)...[/green]")
                analysis = await self._fetch_commodity_data(symbol)
            
            if 'error' in analysis:
                console.print(f"[red]Error fetching data: {analysis['error']}[/red]")
                return
            
            # Display commodity data
            await self._display_commodity_data(symbol, commodity_name, analysis)
            
            # Add LLM Analysis
            console.print(f"\n[bold magenta]🤖 AI Analysis for {commodity_name or symbol}:[/bold magenta]")
            
            # Prepare data for LLM analysis
            llm_data = {
                'symbol': symbol,
                'name': commodity_name,
                'quote': analysis.get('quote', {}),
                'daily_data': analysis.get('daily_data', [])[:10],  # Last 10 days
                'hourly_data': analysis.get('hourly_data', [])[:24],  # Last 24 hours
                'news': analysis.get('news', [])[:3]  # Top 3 news
            }
            
            # Run LLM analysis
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Running AI analysis...", total=None)
                
                commodity_analysis = await self._run_commodity_llm_analysis(symbol, commodity_name, llm_data)
                
                progress.update(task, description="✓ AI analysis complete")
            
            # Display LLM analysis results
            if commodity_analysis.get("success", False):
                await self._display_commodity_llm_results(symbol, commodity_name, commodity_analysis)
            else:
                console.print("[red]LLM analysis failed or returned no results[/red]")
        
        except Exception as e:
            console.print(f"[red]Error in commodity analysis: {e}[/red]")
    
    async def _fetch_commodity_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch commodity data from available APIs."""
        console.print("[cyan]Fetching live data from commodity APIs...[/cyan]")
        
        try:
            console.print(f"[blue]Starting API fetch for {symbol}...[/blue]")
            analysis = await self.commodity_client.get_comprehensive_commodity_analysis(symbol)
            console.print(f"[blue]API fetch completed. Analysis keys: {list(analysis.keys()) if analysis else 'None'}[/blue]")
            if analysis and 'error' not in analysis:
                quote = analysis.get('quote', {})
                daily_data = analysis.get('daily_data', [])
                console.print(f"[blue]Quote data received: {bool(quote)}[/blue]")
                console.print(f"[blue]Daily data count: {len(daily_data) if daily_data else 0}[/blue]")
                # Debug: Print the actual quote and daily data content
                console.print(f"[magenta]DEBUG - Quote content: {quote}[/magenta]")
                if daily_data:
                    console.print(f"[magenta]DEBUG - First daily entry: {daily_data[0]}[/magenta]")
                else:
                    console.print(f"[magenta]DEBUG - Daily data is empty list[/magenta]")
            return analysis
        except Exception as e:
            console.print(f"[red]Error fetching commodity data: {e}[/red]")
            return {"error": str(e)}
    
    async def _display_commodity_data(self, symbol: str, name: str, analysis: Dict[str, Any]):
        """Display basic commodity data."""
        # Display current quote
        quote = analysis.get('quote', {})
        if quote and quote.get('price'):
            console.print(f"\n[bold blue]{name or symbol} - Current Quote[/bold blue]")
            
            price = quote.get('price', 0)
            change = quote.get('change', 0)
            change_percent = quote.get('change_percent', '0')
            
            color = "green" if change >= 0 else "red"
            console.print(f"[bold]Current Price: ${price:.2f}[/bold]")
            console.print(f"[{color}]Change: ${change:.2f} ({change_percent}%)[/{color}]")
            console.print(f"Volume: {quote.get('volume', 0):,}")
            console.print(f"Previous Close: ${quote.get('previous_close', 0):.2f}")
            console.print(f"Latest Trading Day: {quote.get('latest_trading_day', 'N/A')}")
        
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
                    f"${day.get('o', 0):.2f}",
                    f"${day.get('h', 0):.2f}",
                    f"${day.get('l', 0):.2f}",
                    f"${day.get('c', 0):.2f}",
                    f"{day.get('v', 0):,}"
                )
            
            console.print(daily_table)
        
        # Display recent news
        news = analysis.get('news', [])
        if news:
            console.print(f"\n[bold yellow]Recent Commodity News ({len(news)} articles):[/bold yellow]")
            news_table = Table()
            news_table.add_column("Date", style="cyan")
            news_table.add_column("Title", style="white")
            news_table.add_column("Source", style="magenta")
            news_table.add_column("Sentiment", style="yellow")
            
            for article in news[:3]:  # Show top 3 news
                pub_date = article.get('time_published', '')
                if pub_date and len(pub_date) >= 8:
                    try:
                        date = f"{pub_date[:4]}-{pub_date[4:6]}-{pub_date[6:8]}"
                    except:
                        date = pub_date[:10]
                else:
                    date = 'N/A'
                
                title = article.get('title', 'N/A')[:60] + "..." if len(article.get('title', '')) > 60 else article.get('title', 'N/A')
                source = article.get('source', 'N/A')
                sentiment = article.get('sentiment', 'neutral').title()
                
                news_table.add_row(date, title, source, sentiment)
            
            console.print(news_table)
    
    async def _run_commodity_llm_analysis(self, symbol: str, name: str, commodity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run LLM analysis on commodity data."""
        try:
            # Calculate basic metrics from daily data or quote data
            daily_data = commodity_data.get('daily_data', [])
            quote_data = commodity_data.get('quote', {})
            
            current_price = 0
            price_change = 0
            price_change_pct = 0
            
            # Try to get price from quote data first, then daily data
            if quote_data and quote_data.get('price'):
                current_price = quote_data.get('price', 0)
                price_change = quote_data.get('change', 0)
                change_percent_str = quote_data.get('change_percent', '0')
                try:
                    price_change_pct = float(str(change_percent_str).replace('%', ''))
                except:
                    price_change_pct = 0
            elif daily_data and len(daily_data) >= 2:
                current_price = daily_data[0].get('c', 0)
                previous_price = daily_data[1].get('c', 0)
                if previous_price > 0:
                    price_change = current_price - previous_price
                    price_change_pct = (price_change / previous_price) * 100
            
            # Determine commodity category for context
            commodity_category = "Unknown"
            major_commodities = [
                {"name": "Crude Oil WTI", "symbol": "CL=F", "category": "Energy"},
                {"name": "Brent Crude Oil", "symbol": "BZ=F", "category": "Energy"},
                {"name": "Natural Gas", "symbol": "NG=F", "category": "Energy"},
                {"name": "Gold", "symbol": "GC=F", "category": "Precious Metals"},
                {"name": "Silver", "symbol": "SI=F", "category": "Precious Metals"},
                {"name": "Copper", "symbol": "HG=F", "category": "Base Metals"},
                {"name": "Corn", "symbol": "ZC=F", "category": "Agriculture"},
                {"name": "Wheat", "symbol": "ZW=F", "category": "Agriculture"},
            ]
            
            for commodity in major_commodities:
                if commodity["symbol"] == symbol:
                    commodity_category = commodity["category"]
                    break
            
            # Prepare commodity analysis context
            context = {
                'symbol': symbol,
                'name': name,
                'category': commodity_category,
                'asset_type': 'commodity_futures',
                'current_price': current_price,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'daily_data': daily_data,
                'hourly_data': commodity_data['hourly_data'],
                'news': commodity_data['news']
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
                # Use actual price data if available, otherwise use placeholder text
                if current_price > 0:
                    price_text = f"${current_price:.2f}"
                    change_text = f"{price_change_pct:+.2f}%"
                else:
                    price_text = "Price data unavailable"
                    change_text = "Change data unavailable"
                
                technical_prompt = f"Analyze {name or symbol} ({commodity_category}) futures: Price {price_text}, Change {change_text}, Volatility {volatility:.2f}%, Trend {trend_direction}. Brief technical outlook on momentum, seasonal patterns, and key levels."
                
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
                news_headlines = [article.get('title', '')[:80] for article in commodity_data['news'][:2]]  # Limit to 2 headlines, 80 chars each
                news_sentiment = [article.get('sentiment', 'neutral') for article in commodity_data['news'][:2]]
                news_text = '; '.join(news_headlines) if news_headlines else "No recent news"
                sentiment_text = ', '.join(news_sentiment) if news_sentiment else 'neutral'
                
                fundamental_prompt = f"Fundamental outlook for {name or symbol} ({commodity_category}): News: {news_text}. Sentiment: {sentiment_text}. Analyze supply/demand, geopolitical factors, USD impact, and seasonal patterns. Brief assessment only."
                
                fundamental_response = self.llm_client.generate_response([{"role": "user", "content": fundamental_prompt}])
                analysis_text = fundamental_response.get('content', str(fundamental_response)) if isinstance(fundamental_response, dict) else str(fundamental_response)
                
                # Determine signal based on news sentiment
                positive_sentiment = news_sentiment.count('positive') + news_sentiment.count('Positive')
                negative_sentiment = news_sentiment.count('negative') + news_sentiment.count('Negative')
                
                if positive_sentiment > negative_sentiment:
                    signal = 'bullish'
                elif negative_sentiment > positive_sentiment:
                    signal = 'bearish'
                else:
                    signal = 'neutral'
                
                agents_analysis['fundamental'] = {
                    'analysis': analysis_text,
                    'confidence': 70,
                    'signal': signal
                }
            except Exception as e:
                logger.error(f"Fundamental analysis error: {e}")
                agents_analysis['fundamental'] = {'error': str(e)}
            
            # Risk Analysis with concise approach
            try:
                # Determine risk level based on volatility and category
                risk_level = "medium"
                if commodity_category == "Energy" and volatility > 3.0:
                    risk_level = "high"
                elif commodity_category == "Precious Metals" and volatility > 2.0:
                    risk_level = "high"
                elif volatility > 4.0:
                    risk_level = "high"
                elif volatility < 1.5:
                    risk_level = "low"
                
                risk_prompt = f"Risk assessment for {name or symbol} ({commodity_category}) futures: Volatility {volatility:.2f}%, Change {context['price_change_pct']:.2f}%. Provide brief risk level, margin requirements, contango/backwardation risks, and position sizing for futures contracts."
                
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
                fund_signal = agents_analysis.get('fundamental', {}).get('signal', 'neutral')
                risk_level = agents_analysis.get('risk', {}).get('risk_level', 'medium')
                
                final_prompt = f"Final recommendation for {name or symbol} ({commodity_category}) futures: Technical {tech_signal}, Fundamental {fund_signal}, Risk {risk_level}, Price ${context['current_price']:.2f}, Change {context['price_change_pct']:.2f}%. Provide concise {final_signal} recommendation with futures-specific entry strategy, contract expiration considerations, and risk management."
                
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
            logger.error(f"Commodity LLM analysis error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _display_commodity_llm_results(self, symbol: str, name: str, analysis: Dict[str, Any]):
        """Display commodity LLM analysis results."""
        try:
            # Final recommendation
            final_signal = analysis.get('final_signal', 'HOLD')
            confidence = analysis.get('confidence', 0)
            
            signal_color = {
                'BUY': 'green',
                'SELL': 'red',
                'HOLD': 'yellow'
            }.get(final_signal, 'white')
            
            console.print(f"\n[bold {signal_color}]🎯 Final Recommendation: {final_signal}[/bold {signal_color}]")
            console.print(f"[cyan]Confidence: {confidence:.1f}%[/cyan]")
            
            # Agent analyses
            agents_analysis = analysis.get('agents_analysis', {})
            
            if 'technical' in agents_analysis and 'error' not in agents_analysis['technical']:
                console.print(f"\n[bold blue]📊 Technical Analysis:[/bold blue]")
                console.print(agents_analysis['technical']['analysis'])
            
            if 'fundamental' in agents_analysis and 'error' not in agents_analysis['fundamental']:
                console.print(f"\n[bold green]🌍 Fundamental Analysis:[/bold green]")
                console.print(agents_analysis['fundamental']['analysis'])
            
            if 'risk' in agents_analysis and 'error' not in agents_analysis['risk']:
                console.print(f"\n[bold red]⚠️ Risk Analysis:[/bold red]")
                console.print(agents_analysis['risk']['analysis'])
            
            # Final recommendation details
            final_rec = analysis.get('final_recommendation', '')
            if final_rec:
                console.print(f"\n[bold magenta]🤖 AI Summary:[/bold magenta]")
                console.print(final_rec)
                
        except Exception as e:
            console.print(f"[red]Error displaying LLM results: {e}[/red]")
            logger.error(f"Display LLM results error: {e}")
