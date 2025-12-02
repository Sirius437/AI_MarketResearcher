"""
Stock analysis module for MarketResearcher.
Handles all stock-related analysis logic using Finnhub API.
"""

import logging
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import questionary
import pandas as pd
import numpy as np

from data.stocks_database import StocksDatabase
from data.exchanges_database import ExchangesDatabase
from data.universal_cache import UniversalCache
from data.yahoo_client import YahooFinanceClient
from analyzers.technical_context import AgentDisplayFormatter

logger = logging.getLogger(__name__)
console = Console()


class StockAnalyzer:
    """Handles stock analysis operations."""
    
    def __init__(self, finnhub_client, llm_client, config=None, prediction_engine=None, market_data_manager=None):
        """Initialize stock analyzer with required clients."""
        self.finnhub_client = finnhub_client
        self.llm_client = llm_client
        self.config = config
        self.prediction_engine = prediction_engine
        self.stocks_db = StocksDatabase()
        self.exchanges_db = ExchangesDatabase()
        self.cache = UniversalCache(config) if config else UniversalCache()
        self.yahoo_client = YahooFinanceClient()
        self.market_data_manager = market_data_manager
        
        # Initialize signal generator for enhanced analysis
        from analyzers.signal_generator import UnifiedSignalGenerator
        self.signal_generator = UnifiedSignalGenerator()
        
        # Initialize market data manager if not provided
        if not self.market_data_manager and config:
            try:
                from data.market_data import MarketDataManager
                from data.binance_client import BinanceClient
                binance_client = BinanceClient(config)
                self.market_data_manager = MarketDataManager(binance_client, config)
                logger.info("MarketDataManager initialized for stock analyzer")
            except Exception as e:
                logger.warning(f"Failed to initialize MarketDataManager: {e}")
                self.market_data_manager = None
        
        # US exchanges for determining when to use Finnhub vs Yahoo Finance
        self.us_exchanges = {'NASDAQ', 'NYSE', 'AMEX', 'US', 'BATS'}
    
    async def analyze_stock(self):
        """Analyze a single stock symbol using Finnhub API."""
        try:
            # Check if Finnhub client is available
            if not self.finnhub_client:
                console.print("[red]Error: Finnhub API key not configured[/red]")
                console.print("[cyan]Please set FINNHUB_API_KEY in your .env file[/cyan]")
                return
            
            # Select stock market region first
            region_choices = [
                "North America - US, Canada",
                "Europe - UK, Germany, France, Netherlands, Switzerland, Italy",
                "MENA - Saudi Arabia, UAE, Egypt, South Africa",
                "Asia Pacific - Japan, China, Hong Kong, Singapore, Australia, India, Malaysia, Thailand, Philippines, Indonesia, Vietnam, South Korea, New Zealand",
                "search - Search stocks by name/symbol",
                "custom - Enter custom symbol"
            ]
            
            region = await questionary.select(
                "Select stock market region:",
                choices=region_choices
            ).ask_async()
            
            if not region:
                return
            
            region_code = region.split(" - ")[0]
            jurisdiction = None
            
            if region_code == "North America":
                jurisdiction_choices = [
                    "NYSE - New York Stock Exchange",
                    "NASDAQ - NASDAQ Stock Market",
                    "TSX - Toronto Stock Exchange"
                ]
                jurisdiction = await questionary.select(
                    "Select North American market:",
                    choices=jurisdiction_choices
                ).ask_async()
                
            elif region_code == "Europe":
                jurisdiction_choices = [
                    "LSE - London Stock Exchange",
                    "XETRA - Deutsche Börse",
                    "XPAR - Euronext Paris",
                    "XAMS - Euronext Amsterdam",
                    "SIX - SIX Swiss Exchange",
                    "MIL - Borsa Italiana"
                ]
                jurisdiction = await questionary.select(
                    "Select European market:",
                    choices=jurisdiction_choices
                ).ask_async()
                
            elif region_code == "MENA":
                jurisdiction_choices = [
                    "TADAWUL - Saudi Stock Exchange",
                    "DFM - Dubai Financial Market",
                    "EGX - Egyptian Exchange",
                    "JSE - Johannesburg Stock Exchange"
                ]
                jurisdiction = await questionary.select(
                    "Select MENA market:",
                    choices=jurisdiction_choices
                ).ask_async()
                
            elif region_code == "Asia Pacific":
                jurisdiction_choices = [
                    "TSE - Tokyo Stock Exchange",
                    "SSE - Shanghai Stock Exchange", 
                    "HKEX - Hong Kong Stock Exchange",
                    "TWSE - Taiwan Stock Exchange",
                    "SGX - Singapore Exchange",
                    "ASX - Australian Securities Exchange",
                    "BSE - Bombay Stock Exchange",
                    "KLSE - Bursa Malaysia",
                    "SET - Stock Exchange of Thailand",
                    "PSE - Philippine Stock Exchange",
                    "IDX - Indonesia Stock Exchange",
                    "VNX - Ho Chi Minh Stock Exchange",
                    "KRX - Korea Exchange",
                    "NZX - New Zealand Exchange"
                ]
                jurisdiction = await questionary.select(
                    "Select Asia Pacific market:",
                    choices=jurisdiction_choices
                ).ask_async()
            
            # Handle search and custom options at region level
            if region_code == "search":
                # Search functionality
                search_query = await questionary.text(
                    "Search for stocks (by name, symbol, or description):",
                    default=""
                ).ask_async()
                
                if search_query:
                    search_results = self.stocks_db.search_stocks(search_query)
                    if search_results:
                        choices = [f"{stock.symbol} - {stock.name} ({stock.jurisdiction})" 
                                 for stock in search_results[:20]]  # Limit to 20 results
                        selection = await questionary.select(
                            f"Found {len(search_results)} stocks:",
                            choices=choices
                        ).ask_async()
                        
                        if selection:
                            symbol = selection.split(" - ")[0]
                    else:
                        console.print("[yellow]No stocks found matching your search.[/yellow]")
                        return
                        
            elif region_code == "custom":
                symbol = await questionary.text(
                    "Enter stock symbol (e.g., AAPL, TSLA, ASML.AS):",
                    default="AAPL"
                ).ask_async()
                
            else:
                # Regional selection was made, now handle jurisdiction selection
                if not jurisdiction:
                    return
                
                exchange_code = jurisdiction.split(" - ")[0]
                symbol = None
                # Exchange-based selection using database
                jurisdiction_stocks = self.stocks_db.get_stocks_by_exchange(exchange_code)
                
                if not jurisdiction_stocks:
                    console.print(f"[yellow]No stocks found for exchange: {exchange_code}[/yellow]")
                    return
                
                # Show selection method for this exchange (exchange already selected)
                choice = await questionary.select(
                    f"Choose {exchange_code} stock selection method:",
                    choices=[
                        "popular - Popular stocks",
                        "sector - Browse by sector",
                        "all - View all stocks",
                        "custom - Enter custom symbol"
                    ]
                ).ask_async()
                
                if choice and choice.startswith("popular"):
                    # Get popular stocks from this specific exchange
                    popular_stocks = [stock for stock in jurisdiction_stocks if stock.market_cap_category in ["large", "mega"]][:15]
                    if not popular_stocks:
                        popular_stocks = jurisdiction_stocks[:15]  # Fallback to first 15
                    choices = [f"{stock.symbol} - {stock.name}" for stock in popular_stocks]
                    selection = await questionary.select(
                        f"Select popular {exchange_code} stock:",
                        choices=choices
                    ).ask_async()
                    
                    if selection:
                        symbol = selection.split(" - ")[0]
                        
                elif choice and choice.startswith("sector"):
                    # Get sectors from this specific exchange
                    sectors = list(set(stock.sector for stock in jurisdiction_stocks if stock.sector != "Unknown"))
                    if not sectors:
                        console.print(f"[yellow]No sector information available for {exchange_code}[/yellow]")
                        return
                    sector_selection = await questionary.select(
                        f"Select {exchange_code} sector:",
                        choices=sectors
                    ).ask_async()
                    
                    if sector_selection:
                        sector_stocks = [stock for stock in jurisdiction_stocks if stock.sector == sector_selection]
                        choices = [f"{stock.symbol} - {stock.name}" for stock in sector_stocks]
                        selection = await questionary.select(
                            f"Select {sector_selection} stock:",
                            choices=choices
                        ).ask_async()
                        
                        if selection:
                            symbol = selection.split(" - ")[0]
                            
                elif choice and choice.startswith("all"):
                    choices = [f"{stock.symbol} - {stock.name}" for stock in jurisdiction_stocks]
                    selection = await questionary.select(
                        f"Select {exchange_code} stock:",
                        choices=choices
                    ).ask_async()
                    
                    if selection:
                        symbol = selection.split(" - ")[0]
                        
                else:  # custom
                    symbol = await questionary.text(
                        f"Enter {exchange_code} stock symbol:",
                        default=""
                    ).ask_async()
            
            if not symbol:
                return
            
            symbol = symbol.upper().strip()
            
            console.print(f"[yellow]Analyzing stock: {symbol}[/yellow]")
            
            # Determine if this is a US stock or non-US stock
            stock_info = self.stocks_db.get_stock_by_symbol(symbol)
            is_us_stock = False
            exchange_code = None
            
            if stock_info:
                is_us_stock = stock_info.exchange in self.us_exchanges
                exchange_code = stock_info.exchange
                console.print(f"[blue]📊 Stock Information:[/blue]")
                console.print(f"Name: {stock_info.name}")
                console.print(f"Exchange: {stock_info.exchange}")
                console.print(f"Sector: {stock_info.sector}")
                console.print(f"Industry: {stock_info.industry}")
                console.print(f"Currency: {stock_info.currency}")
                console.print(f"Description: {stock_info.description}")
                
                # Display exchange information
                exchange_info = self.exchanges_db.get_exchange_by_code(stock_info.exchange)
                if exchange_info:
                    console.print(f"Trading Hours: {exchange_info.trading_hours}")
                    console.print(f"Timezone: {exchange_info.timezone}")
            else:
                # Try to determine if US stock based on symbol format
                is_us_stock = '.' not in symbol  # US stocks typically don't have dots
                exchange_code = "US" if is_us_stock else "UNKNOWN"
            
            # Check cache first
            if self.cache:
                cached_analysis = self.cache.get("stocks", symbol, symbol=symbol, exchange=exchange_code)
                if cached_analysis:
                    console.print(f"[cyan]Using cached stock data for {symbol}[/cyan]")
                    analysis = cached_analysis
                    data_source = "Cache"
                else:
                    analysis, data_source = await self._fetch_stock_data(symbol, is_us_stock)
                    # Cache the result
                    if analysis and 'error' not in analysis:
                        self.cache.set("stocks", symbol, analysis, symbol=symbol, exchange=exchange_code)
            else:
                analysis, data_source = await self._fetch_stock_data(symbol, is_us_stock)
            
            if not analysis or 'error' in analysis:
                console.print(f"[red]Error fetching data from both sources: {analysis.get('error', 'Unknown error') if analysis else 'No data available'}[/red]")
                return
            
            console.print(f"[green]✓ Data retrieved from {data_source}[/green]")
            
            # Display stock data
            await self._display_stock_data(symbol, analysis)
            
            # Add LLM Analysis
            console.print(f"\n[bold magenta]🤖 AI Analysis for {symbol}:[/bold magenta]")
            
            # Prepare data for LLM analysis
            llm_data = {
                'symbol': symbol,
                'profile': analysis.get('profile', {}),
                'quote': analysis.get('quote', {}),
                'news_count': len(analysis.get('news', [])),
                'recent_news': analysis.get('news', [])[:3],
                'financials': analysis.get('financials', {}).get('metric', {}),
                'recommendations': analysis.get('recommendations', [{}])[0] if analysis.get('recommendations') else {},
                'insider_transactions': analysis.get('insider_transactions', [])[:10]
            }
            
            # Run prediction engine analysis (includes trading agent)
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Running multi-agent analysis...", total=None)
                
                # Collect 30-day historical data for technical analysis
                progress.update(task, description="Collecting 30-day historical data...")
                
                current_price = analysis.get('quote', {}).get('c', 0)
                historical_data = None
                market_data = {}
                enriched_symbol_data = llm_data.copy()
                
                # Get 30 days of historical OHLCV data
                end_time = datetime.now()
                start_time = end_time - timedelta(days=30)
                
                # Get current price and 30-day historical data from market data manager
                market_overview = await self.market_data_manager.get_market_overview([symbol])
                current_price = market_overview.get(symbol, {}).get('price', 0)
                
                # Get 60-day historical data with technical indicators (more data for MACD signal)
                historical_data = await self.market_data_manager.get_symbol_data(
                    symbol, timeframe='1d', limit=60, include_indicators=True
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
                    market_data['historical_data'] = historical_data
                    
                    # Prepare enriched data for prediction engine
                    enriched_symbol_data['ohlcv_30d'] = ohlcv_summary
                    enriched_symbol_data['technical_indicators'] = technical_indicators
                    enriched_symbol_data['historical_data'] = historical_data
                    enriched_symbol_data['historical_data_available'] = True
                    enriched_symbol_data['current_price'] = current_price
                else:
                    logger.warning(f"No historical data available for {symbol}")
                    market_data['ohlcv_30d'] = {}
                    market_data['technical_indicators'] = {}
                    enriched_symbol_data['historical_data_available'] = False
                    enriched_symbol_data['current_price'] = current_price
                
                progress.update(task, description="Running multi-agent analysis with technical data...")
                
                # Use prediction engine with all agents including trading agent
                if hasattr(self, 'prediction_engine') and self.prediction_engine:
                    stock_analysis = await self.prediction_engine.predict(symbol, enriched_symbol_data)
                    
                    # Add market data to analysis results
                    if stock_analysis.get("success") and market_data:
                        stock_analysis["market_data"] = market_data
                else:
                    # Fallback to legacy analysis if prediction engine not available
                    stock_analysis = await self._run_stock_llm_analysis(symbol, enriched_symbol_data)
                
                progress.update(task, description="✓ Multi-agent analysis complete")
            
            # Display analysis results
            if stock_analysis.get("success", False):
                if hasattr(self, 'prediction_engine') and self.prediction_engine:
                    await self._display_prediction_results(symbol, stock_analysis)
                else:
                    # Use the same prediction results display for consistency
                    await self._display_prediction_results(symbol, stock_analysis)
            else:
                console.print(f"[red]AI analysis failed: {stock_analysis.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error analyzing stock: {e}[/red]")
            logger.error(f"Stock analysis error: {e}")
    
    async def _fetch_stock_data(self, symbol: str, is_us_stock: bool) -> tuple:
        """Fetch stock data using optimized data source priorities."""
        analysis = None
        data_source = None
        
        # Use market data manager for comprehensive data fetching
        if self.market_data_manager:
            console.print("[cyan]Fetching data using market data manager (Finnhub → IB → Polygon → others)...[/cyan]")
            try:
                # Get market overview data for current price
                market_overview = await self.market_data_manager.get_market_overview([symbol])
                if market_overview and symbol in market_overview:
                    ticker_data = market_overview[symbol]
                    
                    # Build comprehensive analysis using Finnhub client if available
                    if self.finnhub_client:
                        analysis = self.finnhub_client.get_comprehensive_analysis(symbol)
                        data_source = "Finnhub + Market Data Manager"
                        
                        # If Finnhub comprehensive fails, use market data + Yahoo fallback
                        if 'error' in analysis:
                            analysis = await self._get_yahoo_analysis(symbol)
                            data_source = "Market Data Manager + Yahoo"
                        
                        # Merge/update quote data from market data manager
                        if analysis and ticker_data.get('price', 0) > 0:
                            if 'quote' not in analysis:
                                analysis['quote'] = {}
                            
                            # Use market data manager price if available and valid
                            analysis['quote'].update({
                                'c': ticker_data.get('price', analysis['quote'].get('c', 0)),
                                'd': ticker_data.get('change_24h', 0) * ticker_data.get('price', 0) / 100 if ticker_data.get('change_24h') else analysis['quote'].get('d', 0),
                                'dp': ticker_data.get('change_24h', analysis['quote'].get('dp', 0)),
                                'h': ticker_data.get('high_24h', analysis['quote'].get('h', 0)),
                                'l': ticker_data.get('low_24h', analysis['quote'].get('l', 0))
                            })
                        
                        # Fetch financial metrics using market data manager (IB → Finnhub → Yahoo priority)
                        try:
                            financial_metrics = await self.market_data_manager.get_financial_metrics(symbol)
                            if financial_metrics and not financial_metrics.get('error'):
                                # Update financials section with prioritized data
                                if 'financials' not in analysis:
                                    analysis['financials'] = {}
                                analysis['financials'].update(financial_metrics)
                                console.print(f"[green]Financial metrics fetched from {financial_metrics.get('source', 'unknown')}[/green]")
                        except Exception as e:
                            console.print(f"[yellow]Failed to fetch financial metrics: {e}[/yellow]")
                    else:
                        # No Finnhub, use Yahoo with market data manager quote data
                        analysis = await self._get_yahoo_analysis(symbol)
                        if analysis and ticker_data.get('price', 0) > 0:
                            if 'quote' not in analysis:
                                analysis['quote'] = {}
                            
                            analysis['quote'].update({
                                'c': ticker_data.get('price', 0),
                                'd': ticker_data.get('change_24h', 0) * ticker_data.get('price', 0) / 100 if ticker_data.get('change_24h') else 0,
                                'dp': ticker_data.get('change_24h', 0),
                                'h': ticker_data.get('high_24h', 0),
                                'l': ticker_data.get('low_24h', 0)
                            })
                        
                        # Fetch financial metrics using market data manager (IB → Finnhub → Yahoo priority)
                        try:
                            financial_metrics = await self.market_data_manager.get_financial_metrics(symbol)
                            if financial_metrics and not financial_metrics.get('error'):
                                # Update financials section with prioritized data
                                if 'financials' not in analysis:
                                    analysis['financials'] = {}
                                analysis['financials'].update(financial_metrics)
                                console.print(f"[green]Financial metrics fetched from {financial_metrics.get('source', 'unknown')}[/green]")
                        except Exception as e:
                            console.print(f"[yellow]Failed to fetch financial metrics: {e}[/yellow]")
                        
                        data_source = "Market Data Manager + Yahoo"
                else:
                    # Fallback to legacy method if market overview fails
                    return await self._fetch_stock_data_legacy(symbol, is_us_stock)
            except Exception as e:
                console.print(f"[yellow]Market data manager failed: {e}, using legacy method...[/yellow]")
                return await self._fetch_stock_data_legacy(symbol, is_us_stock)
        else:
            # No market data manager, use legacy method
            return await self._fetch_stock_data_legacy(symbol, is_us_stock)
        
        return analysis, data_source
    
    async def _fetch_stock_data_legacy(self, symbol: str, is_us_stock: bool) -> tuple:
        """Legacy stock data fetching method."""
        analysis = None
        data_source = None
        
        if is_us_stock and self.finnhub_client:
            console.print("[cyan]Fetching live data from Finnhub API...[/cyan]")
            analysis = self.finnhub_client.get_comprehensive_analysis(symbol)
            data_source = "Finnhub"
            
            if 'error' in analysis:
                console.print(f"[yellow]Finnhub failed, trying Yahoo Finance fallback...[/yellow]")
                analysis = await self._get_yahoo_analysis(symbol)
                data_source = "Yahoo Finance"
        else:
            console.print("[cyan]Fetching live data from Yahoo Finance (non-US stock)...[/cyan]")
            analysis = await self._get_yahoo_analysis(symbol)
            data_source = "Yahoo Finance"
        
        return analysis, data_source
    
    async def _display_stock_data(self, symbol: str, analysis: Dict[str, Any]):
        """Display basic stock data from Finnhub API."""
        # Get stock info for currency formatting
        stock_info = self.stocks_db.get_stock_by_symbol(symbol)
        currency_symbol = "$"  # Default to USD
        
        if stock_info and stock_info.currency:
            currency_map = {
                # Major currencies
                'USD': '$',   # US Dollar
                'EUR': '€',   # Euro
                'GBP': '£',   # British Pound
                'JPY': '¥',   # Japanese Yen
                'CHF': 'CHF ', # Swiss Franc
                'CAD': 'C$',  # Canadian Dollar
                'AUD': 'A$',  # Australian Dollar
                'NZD': 'NZ$', # New Zealand Dollar
                
                # Asian currencies
                'CNY': '¥',   # Chinese Yuan
                'HKD': 'HK$', # Hong Kong Dollar
                'SGD': 'S$',  # Singapore Dollar
                'KRW': '₩',   # South Korean Won
                'INR': '₹',   # Indian Rupee
                'IDR': 'Rp',  # Indonesian Rupiah
                'THB': '฿',   # Thai Baht
                'MYR': 'RM',  # Malaysian Ringgit
                'PHP': '₱',   # Philippine Peso
                'VND': '₫',   # Vietnamese Dong
                'TWD': 'NT$', # Taiwan Dollar
                
                # European currencies
                'SEK': 'kr',  # Swedish Krona
                'NOK': 'kr',  # Norwegian Krone
                'DKK': 'kr',  # Danish Krone
                'PLN': 'zł',  # Polish Zloty
                'CZK': 'Kč',  # Czech Koruna
                'HUF': 'Ft',  # Hungarian Forint
                'RUB': '₽',   # Russian Ruble
                
                # Middle East & Africa
                'SAR': 'SR',  # Saudi Riyal
                'AED': 'د.إ', # UAE Dirham
                'EGP': 'E£',  # Egyptian Pound
                'ZAR': 'R',   # South African Rand
                'ILS': '₪',   # Israeli Shekel
                'TRY': '₺',   # Turkish Lira
                
                # Americas
                'BRL': 'R$',  # Brazilian Real
                'MXN': '$',   # Mexican Peso
                'ARS': '$',   # Argentine Peso
                'CLP': '$',   # Chilean Peso
                'COP': '$',   # Colombian Peso
                'PEN': 'S/',  # Peruvian Sol
            }
            currency_symbol = currency_map.get(stock_info.currency, stock_info.currency + ' ')
        
        # Display company profile
        profile = analysis.get('profile', {})
        if profile:
            console.print(f"\n[bold blue]{profile.get('name', symbol)} ({symbol})[/bold blue]")
            console.print(f"Industry: {profile.get('finnhubIndustry', 'N/A')}")
            
            # Format market cap with correct currency
            market_cap = profile.get('marketCapitalization', 0)
            if stock_info and stock_info.currency == 'IDR':
                # For IDR, market cap might be in millions, so display in trillions
                console.print(f"Market Cap: {currency_symbol}{market_cap:,.0f}M")
            else:
                console.print(f"Market Cap: {currency_symbol}{market_cap:,.0f}M")
            console.print(f"Website: {profile.get('weburl', 'N/A')}")
        
        # Display current quote
        quote = analysis.get('quote', {})
        if quote:
            current_price = quote.get('c', 0)
            change = quote.get('d', 0)
            change_pct = quote.get('dp', 0)
            
            color = "green" if change >= 0 else "red"
            console.print(f"[bold]Current Price: {currency_symbol}{current_price:,.2f}[/bold]")
            
            # Fix percentage calculation - ensure it's calculated correctly
            if change != 0 and current_price != 0:
                # Recalculate percentage to ensure accuracy
                prev_close = quote.get('pc', current_price - change)
                if prev_close != 0:
                    calculated_pct = (change / prev_close) * 100
                    change_pct = calculated_pct
            
            console.print(f"[{color}]Change: {currency_symbol}{change:,.2f} ({change_pct:.2f}%)[/{color}]")
            console.print(f"High: {currency_symbol}{quote.get('h', 0):,.2f} | Low: {currency_symbol}{quote.get('l', 0):,.2f}")
            console.print(f"Previous Close: {currency_symbol}{quote.get('pc', 0):,.2f}")
        
        # Display recent news
        news = analysis.get('news', [])
        if news and len(news) > 0:
            # Filter out invalid news articles
            valid_news = []
            for article in news[:5]:
                headline = article.get('headline', '')
                if headline and headline != 'N/A' and len(headline.strip()) > 0:
                    # Handle timestamps
                    datetime_val = article.get('datetime', 0)
                    if datetime_val and datetime_val > 0:
                        try:
                            # Check if timestamp is reasonable (not in far future)
                            current_time = int(time.time())
                            if datetime_val > current_time + 86400:  # More than 1 day in future
                                date = 'Recent'
                            else:
                                date = datetime.fromtimestamp(datetime_val).strftime('%Y-%m-%d')
                        except (ValueError, OSError):
                            date = 'Recent'
                    else:
                        date = 'Recent'
                    
                    valid_news.append({
                        'date': date,
                        'headline': headline[:60] + "..." if len(headline) > 60 else headline,
                        'source': article.get('source', 'Yahoo Finance')
                    })
            
            if valid_news:
                console.print(f"\n[bold yellow]Recent News ({len(valid_news)} articles):[/bold yellow]")
                news_table = Table()
                news_table.add_column("Date", style="cyan")
                news_table.add_column("Headline", style="white")
                news_table.add_column("Source", style="magenta")
                
                for article in valid_news:
                    news_table.add_row(article['date'], article['headline'], article['source'])
                
                console.print(news_table)
            else:
                console.print(f"\n[bold yellow]Recent News:[/bold yellow]")
                console.print("[dim]No recent news available for this stock[/dim]")
        
        # Display financials
        financials = analysis.get('financials', {})
        if financials and 'metric' in financials:
            metrics = financials['metric']
            console.print(f"\n[bold green]Key Financial Metrics:[/bold green]")
            
            fin_table = Table()
            fin_table.add_column("Metric", style="cyan")
            fin_table.add_column("Value", style="magenta")
            
            key_metrics = {
                'peNormalizedAnnual': 'P/E Ratio',
                'pbAnnual': 'P/B Ratio',
                'roaAnnual': 'ROA (%)',
                'roeAnnual': 'ROE (%)',
                'revenueGrowthAnnual': 'Revenue Growth (%)',
                'epsAnnual': 'EPS'
            }
            
            for key, label in key_metrics.items():
                value = metrics.get(key, 'N/A')
                if isinstance(value, (int, float)):
                    if 'Growth' in label or 'ROA' in label or 'ROE' in label:
                        value = f"{value:.2f}%"
                    else:
                        value = f"{value:.2f}"
                
                fin_table.add_row(label, str(value))
            
            console.print(fin_table)
        
        # Display recommendations
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            latest_rec = recommendations[0] if recommendations else {}
            console.print(f"\n[bold cyan]Analyst Recommendations:[/bold cyan]")
            
            rec_table = Table()
            rec_table.add_column("Rating", style="cyan")
            rec_table.add_column("Count", style="magenta")
            
            rec_table.add_row("Strong Buy", str(latest_rec.get('strongBuy', 0)))
            rec_table.add_row("Buy", str(latest_rec.get('buy', 0)))
            rec_table.add_row("Hold", str(latest_rec.get('hold', 0)))
            rec_table.add_row("Sell", str(latest_rec.get('sell', 0)))
            rec_table.add_row("Strong Sell", str(latest_rec.get('strongSell', 0)))
            
            console.print(rec_table)
        
        # Display insider transactions
        insider_trans = analysis.get('insider_transactions', [])
        if insider_trans:
            console.print(f"\n[bold red]Recent Insider Transactions ({len(insider_trans)}):[/bold red]")
            
            insider_table = Table()
            insider_table.add_column("Date", style="cyan")
            insider_table.add_column("Name", style="white")
            insider_table.add_column("Transaction", style="magenta")
            insider_table.add_column("Shares", style="yellow")
            
            for trans in insider_trans[:5]:  # Show top 5
                # Handle timestamp conversion for date
                date_raw = trans.get('transactionDate', 'N/A')
                if date_raw != 'N/A':
                    try:
                        # Convert timestamp to string if it's a pandas Timestamp or datetime
                        if hasattr(date_raw, 'strftime'):
                            date = date_raw.strftime('%Y-%m-%d')
                        else:
                            date = str(date_raw)
                    except Exception:
                        date = str(date_raw)
                else:
                    date = 'N/A'
                
                # Handle name with proper None checking
                raw_name = trans.get('name', 'N/A')
                if raw_name and raw_name != 'N/A' and len(str(raw_name)) > 20:
                    name = str(raw_name)[:20] + "..."
                else:
                    name = str(raw_name) if raw_name else 'N/A'
                
                transaction_code = trans.get('transactionCode', 'N/A') or 'N/A'
                shares_raw = trans.get('share', 0)
                shares = f"{shares_raw:,}" if shares_raw is not None else "0"
                
                insider_table.add_row(date, name, transaction_code, shares)
            
            console.print(insider_table)
    
    async def _run_stock_llm_analysis(self, symbol: str, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run LLM analysis on stock data using existing agents."""
        try:
            # Prepare stock analysis context
            context = {
                'symbol': symbol,
                'asset_type': 'stock',
                'current_price': stock_data['quote'].get('c', 0),
                'price_change': stock_data['quote'].get('d', 0),
                'price_change_pct': stock_data['quote'].get('dp', 0),
                'market_cap': stock_data['profile'].get('marketCapitalization', 0),
                'pe_ratio': stock_data['financials'].get('peNormalizedAnnual', 0),
                'news_sentiment': 'neutral',  # Could be enhanced with sentiment analysis
                'analyst_recommendations': stock_data['recommendations'],
                'insider_transactions_data': stock_data['insider_transactions']
            }
            
            # Use existing agents to analyze stock
            agents_analysis = {}
            
            # Technical Analysis (comprehensive but token-conscious)
            try:
                # Get additional financial metrics for better analysis
                financials = stock_data['financials']
                
                technical_prompt = f"""
                Analyze stock {symbol} technically:
                
                Current Metrics:
                - Price: ${context['current_price']:.2f} (Daily change: {context['price_change_pct']:.2f}%)
                - Market Cap: ${context['market_cap']:,.0f}M
                - P/E Ratio: {context['pe_ratio']:.2f}
                - P/B Ratio: {financials.get('pbAnnual', 'N/A')}
                - ROE: {financials.get('roeAnnual', 'N/A')}%
                - Revenue Growth: {financials.get('revenueGrowthAnnual', 'N/A')}%
                
                Provide technical analysis covering:
                1. Valuation assessment (P/E, P/B relative to sector)
                2. Growth metrics evaluation
                3. Price momentum and trend analysis
                4. Overall technical outlook
                
                Keep response under 300 words.
                """
                
                technical_response = self.llm_client.generate_response([{"role": "user", "content": technical_prompt}])
                if isinstance(technical_response, dict) and 'content' in technical_response:
                    analysis_text = technical_response['content']
                else:
                    analysis_text = str(technical_response)
                
                # Determine signal from metrics
                pe_signal = "overvalued" if context['pe_ratio'] > 25 else "undervalued" if context['pe_ratio'] < 15 else "fairly valued"
                price_signal = "bullish" if context['price_change_pct'] > 2 else "bearish" if context['price_change_pct'] < -2 else "neutral"
                
                agents_analysis['technical'] = {
                    'analysis': analysis_text,
                    'confidence': 75,
                    'signal': 'positive' if price_signal == 'bullish' and pe_signal != 'overvalued' else 'negative' if price_signal == 'bearish' or pe_signal == 'overvalued' else 'neutral'
                }
            except Exception as e:
                logger.error(f"Technical analysis error: {e}")
                agents_analysis['technical'] = {'error': str(e)}
            
            # Sentiment Analysis (comprehensive market sentiment)
            try:
                recommendations = stock_data['recommendations']
                news_headlines = [article.get('headline', '') for article in stock_data['recent_news'][:3]]
                
                # Calculate analyst consensus metrics
                strong_buy = recommendations.get('strongBuy', 0)
                buy = recommendations.get('buy', 0)
                hold = recommendations.get('hold', 0)
                sell = recommendations.get('sell', 0)
                strong_sell = recommendations.get('strongSell', 0)
                total_analysts = strong_buy + buy + hold + sell + strong_sell
                
                sentiment_prompt = f"""
                Analyze sentiment for {symbol}:
                
                Analysts ({total_analysts}): Strong Buy: {strong_buy}, Buy: {buy}, Hold: {hold}, Sell: {sell}, Strong Sell: {strong_sell}
                
                Recent News:
                {chr(10).join([f"- {headline[:100]}" for headline in news_headlines[:2]]) if news_headlines else "- No recent news"}
                
                Provide brief analysis:
                1. Analyst consensus trend
                2. News sentiment impact
                3. Overall market confidence
                
                Keep under 150 words.
                """
                
                sentiment_response = self.llm_client.generate_response([{"role": "user", "content": sentiment_prompt}])
                if isinstance(sentiment_response, dict) and 'content' in sentiment_response:
                    analysis_text = sentiment_response['content']
                else:
                    analysis_text = str(sentiment_response)
                
                # Calculate sentiment signal
                sentiment_signal = "positive" if (strong_buy + buy) > (sell + strong_sell) else "negative" if (sell + strong_sell) > (strong_buy + buy) else "neutral"
                
                agents_analysis['sentiment'] = {
                    'analysis': analysis_text,
                    'confidence': 80,
                    'signal': sentiment_signal
                }
            except Exception as e:
                logger.error(f"Sentiment analysis error: {e}")
                agents_analysis['sentiment'] = {'error': str(e)}
            
            # Risk Analysis (comprehensive risk assessment)
            try:
                insider_data = context['insider_transactions_data']
                
                # Format key insider transactions
                insider_details = []
                if insider_data:
                    for trans in insider_data[:5]:
                        name = trans.get('name', 'Unknown')[:25]
                        code = trans.get('transactionCode', 'Unknown')
                        shares = trans.get('share', 0)
                        if code == 'S' and shares > 10000:  # Significant sales only
                            insider_details.append(f"{name}: Sold {shares:,} shares")
                
                risk_prompt = f"""
                Risk analysis for {symbol}:
                
                Metrics:
                - Market Cap: ${context['market_cap']:,.0f}M
                - P/E: {context['pe_ratio']:.2f}
                - Volatility: {abs(context['price_change_pct']):.2f}%
                - ROE: {stock_data['financials'].get('roeAnnual', 'N/A')}%
                
                Insider Activity:
                {chr(10).join([f"- {detail}" for detail in insider_details[:3]]) if insider_details else "- No significant sales"}
                
                Brief assessment:
                1. Valuation risk level
                2. Volatility concerns
                3. Insider activity impact
                4. Overall risk rating
                
                Keep under 120 words.
                """
                
                risk_response = self.llm_client.generate_response([{"role": "user", "content": risk_prompt}])
                if isinstance(risk_response, dict) and 'content' in risk_response:
                    analysis_text = risk_response['content']
                else:
                    analysis_text = str(risk_response)
                
                # Determine risk level
                volatility_risk = "high" if abs(context['price_change_pct']) > 5 else "medium" if abs(context['price_change_pct']) > 2 else "low"
                insider_risk_flag = len(insider_details) > 0
                
                agents_analysis['risk'] = {
                    'analysis': analysis_text,
                    'confidence': 85,
                    'risk_level': 'high' if insider_risk_flag else volatility_risk
                }
            except Exception as e:
                logger.error(f"Risk analysis error: {e}")
                agents_analysis['risk'] = {'error': str(e)}
                        # Generate enhanced trading strategy with algorithmic insights
            try:
                # Prepare market data for signal generation
                market_data = {
                    "current_price": context['current_price'],
                    "volume": context.get('volume', 0),
                    "price_change_1d": context['price_change_pct'],
                    "price_change_5d": context.get('price_change_5d', 0),
                    "volatility": abs(context['price_change_pct']) / 100,
                    "high": context.get('high', context['current_price']),
                    "low": context.get('low', context['current_price'])
                }
                
                # Calculate technical indicators if historical data available
                indicators = {}
                if 'historical_data' in context and context['historical_data'] is not None:
                    try:
                        indicators = self.signal_generator.calculate_technical_indicators(context['historical_data'])
                    except Exception as e:
                        logger.warning(f"Failed to calculate indicators: {e}")
                
                # Generate enhanced signal with algorithmic insights
                try:
                    enhanced_signal = self.signal_generator.generate_enhanced_signal(
                        symbol, market_data, indicators, position_size=100
                    )
                    
                    # Add enhanced signal to analysis
                    agents_analysis['enhanced_signal'] = enhanced_signal
                    
                    # Use enhanced signal for trading strategy
                    algo_recommendation = enhanced_signal.get('recommended_algorithm', 'VWAP')
                    execution_insights = enhanced_signal.get('execution_insights', {})
                    signal_strength = enhanced_signal.get('strength', 0.5)
                    
                except Exception as e:
                    logger.warning(f"Enhanced signal generation failed: {e}")
                    enhanced_signal = None
                
                # Summarize key insights from each analysis
                tech_summary = agents_analysis.get('technical', {}).get('analysis', 'Technical analysis unavailable')[:200]
                sentiment_summary = agents_analysis.get('sentiment', {}).get('analysis', 'Sentiment analysis unavailable')[:200]
                risk_summary = agents_analysis.get('risk', {}).get('analysis', 'Risk analysis unavailable')[:200]
                
                # Check for critical insider activity
                insider_alert = ""
                if context['insider_transactions_data']:
                    ceo_sales = any('CEO' in trans.get('name', '').upper() for trans in context['insider_transactions_data'] if trans.get('transactionCode') == 'S')
                    if ceo_sales:
                        insider_alert = "\n⚠️ CRITICAL: CEO insider selling detected - major red flag!"
                
                # Calculate key price levels for trading strategy
                current_price = context['current_price']
                daily_change_pct = abs(context['price_change_pct'])
                volatility_factor = max(0.02, daily_change_pct / 100)  # Minimum 2% volatility
                
                # Include algorithmic insights in prompt
                algo_insights = ""
                if enhanced_signal:
                    algo_insights = f"""
                
                ALGORITHMIC EXECUTION INSIGHTS:
                - Recommended Algorithm: {algo_recommendation}
                - Signal Strength: {signal_strength:.2f}
                - Execution Time: {execution_insights.get('estimated_execution_time', 'N/A')}
                - Market Impact: {execution_insights.get('market_impact_bps', 0)} bps
                - Risk Profile: {execution_insights.get('risk_profile', 'MODERATE')}
                """
                
                final_prompt = f"""
                Comprehensive trading strategy analysis for {symbol} at ${current_price:.2f}:
                
                Technical Analysis Summary:
                {tech_summary}
                
                Market Sentiment Summary:
                {sentiment_summary}
                
                Risk Assessment Summary:
                {risk_summary}
                {insider_alert}
                {algo_insights}
                
                CRITICAL TRADING PARAMETERS REQUIRED:
                Based on current price ${current_price:.2f} and algorithmic analysis, provide specific:
                
                1. POSITION DIRECTION:
                   - Long Buy (new long position)
                   - Long Sell (close existing long position) 
                   - Short Sell (new short position)
                   - Short Cover (close existing short position)
                
                2. ENTRY STRATEGY:
                   - Entry Price Range: $X.XX - $X.XX (specific prices)
                   - Optimal Entry Price: $X.XX
                   - Entry Timing Conditions
                
                3. EXIT STRATEGY:
                   - Take Profit Target: $X.XX (specific price)
                   - Stop Loss Level: $X.XX (specific price)
                   - Risk/Reward Ratio: X:X
                
                4. TRAILING STOP PARAMETERS:
                   - Trailing Stop Activation Threshold: $X.XX (price level to activate)
                   - Trailing Stop Distance: $X.XX or X% (distance from peak)
                   - Trailing Stop Type: Fixed dollar amount or percentage
                
                5. POSITION SIZING:
                   - Recommended position size as % of portfolio
                   - Maximum risk per trade recommendation
                
                6. OVERALL RECOMMENDATION:
                   - Clear BUY/HOLD/SELL signal
                   - Confidence level (1-10)
                   - Time horizon (short/medium/long term)
                
                Provide specific numerical values for all price levels and percentages. Use technical analysis to justify entry/exit levels based on support/resistance, moving averages, or volatility bands.
                
                Keep total response under 600 words but ensure all trading parameters are specified.
                """
                
                final_response = self.llm_client.generate_response([{"role": "user", "content": final_prompt}])
                if isinstance(final_response, dict) and 'content' in final_response:
                    final_analysis_text = final_response['content']
                else:
                    final_analysis_text = str(final_response)
                
                # Parse trading parameters from LLM response
                trading_params = self._extract_trading_parameters(final_analysis_text, current_price, volatility_factor)
                
                # Determine final signal based on agent outputs
                signals = [agent.get('signal', 'neutral') for agent in agents_analysis.values() if 'signal' in agent]
                positive_signals = signals.count('positive')
                negative_signals = signals.count('negative')
                
                if positive_signals > negative_signals:
                    final_signal = 'BUY'
                elif negative_signals > positive_signals:
                    final_signal = 'SELL'
                else:
                    final_signal = 'HOLD'
                
                return {
                    'success': True,
                    'agents_analysis': agents_analysis,
                    'final_recommendation': final_analysis_text,
                    'final_signal': final_signal,
                    'confidence': sum(agent.get('confidence', 0) for agent in agents_analysis.values() if 'confidence' in agent) / len([a for a in agents_analysis.values() if 'confidence' in a]),
                    'trading_parameters': trading_params
                }
                
            except Exception as e:
                logger.error(f"Final recommendation error: {e}")
                return {'success': False, 'error': str(e)}
            
        except Exception as e:
            logger.error(f"Stock LLM analysis error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _display_prediction_results(self, symbol: str, prediction: Dict[str, Any]):
        """Display prediction results from the prediction engine (includes trading agent)."""
        try:
            # Check if prediction was successful
            if not prediction.get("success", False):
                console.print(f"[red]Prediction failed: {prediction.get('error', 'Unknown error')}[/red]")
                return
            
            console.print(f"\n[bold blue]📊 Stock Analysis Results for {symbol}:[/bold blue]")
            
            # Main results table
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
            
            # Agent analysis breakdown
            agent_results = prediction.get("agent_results", {})
            
            if agent_results and isinstance(agent_results, dict) and len(agent_results) > 0:
                console.print("\n[bold]Agent Analysis Breakdown:[/bold]")
                
                for agent_name, analysis in agent_results.items():
                    console.print(f"\n[bold cyan]{agent_name.title()} Agent:[/bold cyan]")
                    
                    if isinstance(analysis, dict):
                        agent_table = Table()
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
                                # For other agents, use generic formatting
                                for key, value in analysis.items():
                                    if key not in ['raw_response', 'timestamp', 'raw_analysis']:
                                        if isinstance(value, (int, float)):
                                            if key == 'confidence':
                                                value = f"{value:.1f}%"
                                            else:
                                                value = f"{value:.2f}"
                                        elif isinstance(value, str):
                                            # For other agents, use standard truncation
                                            if len(value) > 200:
                                                value = value[:200] + "..."
                                        elif len(value) > 500:
                                            # For other agents, use longer truncation limit
                                            value = value[:500] + "..."
                                    elif isinstance(value, dict):
                                        # Format nested dicts more cleanly
                                        value = self._format_nested_dict(value)
                                    
                                    # Format key name nicely
                                    display_key = key.replace('_', ' ').title()
                                    agent_table.add_row(display_key, str(value))
                        
                        console.print(agent_table)
                    else:
                        # Handle non-dict analysis results
                        console.print(f"[white]{str(analysis)[:300]}...[/white]")
                    
                    console.print()
            else:
                # Show a simple message that agent analysis is running in background
                console.print("\n[bold]Agent Analysis Breakdown:[/bold]")
                console.print("[dim]Multi-agent analysis completed. Individual agent details available in logs.[/dim]")
            
            # Market context if available
            market_context = prediction.get("market_context", {})
            if market_context:
                console.print("[bold]Market Context:[/bold]")
                context_table = Table()
                context_table.add_column("Metric", style="cyan")
                context_table.add_column("Value", style="yellow")
                
                for key, value in market_context.items():
                    if isinstance(value, (int, float)):
                        if 'price' in key.lower():
                            value = f"${value:.2f}"
                        elif 'percent' in key.lower():
                            value = f"{value:.2f}%"
                        else:
                            value = f"{value:.2f}"
                    
                    display_key = key.replace('_', ' ').title()
                    context_table.add_row(display_key, str(value))
                
                console.print(context_table)
                
        except Exception as e:
            console.print(f"[red]Error displaying prediction results: {e}[/red]")
            logger.error(f"Display error: {e}")
    
    
    def _format_nested_dict(self, data: Dict[str, Any]) -> str:
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
                        formatted_items.append(f"{key}: ${value:.2f}")
                    else:
                        formatted_items.append(f"{key}: {value:.2f}")
                elif isinstance(value, str) and len(value) < 50:
                    formatted_items.append(f"{key}: {value}")
                elif isinstance(value, bool):
                    formatted_items.append(f"{key}: {'Yes' if value else 'No'}")
            
            return " | ".join(formatted_items[:3])  # Limit to 3 items for readability
        except:
            return str(data)[:100]
    
    
    async def _get_yahoo_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get stock analysis using Yahoo Finance client for non-US stocks."""
        try:
            # Use centralized Yahoo Finance client
            comprehensive_data = await self.yahoo_client.get_comprehensive_analysis(symbol)
            
            if 'error' in comprehensive_data:
                return comprehensive_data
            
            info = comprehensive_data.get('info', {})
            if 'error' in info:
                return {'error': f'Stock {symbol} not found on Yahoo Finance'}
            
            hist_dict = comprehensive_data.get('historical_data', {})
            if not hist_dict:
                return {'error': f'No historical data available for {symbol}'}
            
            news = comprehensive_data.get('news', [])
            
            # Format data to match Finnhub structure
            analysis = {
                'profile': {
                    'name': info.get('longName', info.get('shortName', symbol)),
                    'finnhubIndustry': info.get('industry', 'N/A'),
                    'marketCapitalization': info.get('marketCap', 0) / 1_000_000 if info.get('marketCap') else 0,  # Convert to millions
                    'weburl': info.get('website', 'N/A'),
                    'country': info.get('country', 'N/A'),
                    'currency': info.get('currency', 'N/A'),
                    'exchange': info.get('exchange', 'N/A'),
                    'sector': info.get('sector', 'N/A')
                },
                'quote': {
                    'c': info.get('currentPrice', info.get('regularMarketPrice', 0)),  # Current price
                    'd': info.get('regularMarketChange', 0),  # Change
                    'dp': info.get('regularMarketChangePercent', 0) * 100 if info.get('regularMarketChangePercent') else 0,  # Change percent
                    'h': info.get('dayHigh', info.get('regularMarketDayHigh', 0)),  # Day high
                    'l': info.get('dayLow', info.get('regularMarketDayLow', 0)),  # Day low
                    'pc': info.get('previousClose', info.get('regularMarketPreviousClose', 0))  # Previous close
                },
                'news': news,
                'financials': {
                    'metric': {
                        'peNormalizedAnnual': info.get('trailingPE', info.get('forwardPE', 0)),
                        'pbAnnual': info.get('priceToBook', 0),
                        'roaAnnual': info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else 0,
                        'roeAnnual': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
                        'revenueGrowthAnnual': info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0,
                        'epsAnnual': info.get('trailingEps', info.get('forwardEps', 0))
                    }
                },
                'recommendations': [{
                    'strongBuy': 0,
                    'buy': 0,
                    'hold': 0,
                    'sell': 0,
                    'strongSell': 0
                }],
                'insider_transactions': [],
                'data_source': 'Yahoo Finance'
            }
            
            # Process news data - news already comes from yahoo_client.get_news()
            # No need to reprocess, just use it directly
            analysis['news'] = news
            
            # Try to get analyst recommendations if available
            try:
                ticker = yf.Ticker(symbol)
                recommendations = ticker.recommendations
                if recommendations is not None and not recommendations.empty:
                    latest_rec = recommendations.iloc[-1]
                    analysis['recommendations'] = [{
                        'strongBuy': int(latest_rec.get('strongBuy', 0)),
                        'buy': int(latest_rec.get('buy', 0)),
                        'hold': int(latest_rec.get('hold', 0)),
                        'sell': int(latest_rec.get('sell', 0)),
                        'strongSell': int(latest_rec.get('strongSell', 0))
                    }]
            except:
                pass
            
            # Try to get insider transactions if available
            try:
                insider_trades = ticker.insider_transactions
                if insider_trades is not None and not insider_trades.empty:
                    for _, trade in insider_trades.head(10).iterrows():
                        analysis['insider_transactions'].append({
                            'name': trade.get('Insider', 'N/A'),
                            'transactionDate': trade.get('Start Date', 'N/A'),
                            'transactionCode': 'S' if trade.get('Transaction', '').lower() == 'sale' else 'P',
                            'share': int(trade.get('Shares', 0))
                        })
            except:
                pass
            
            return analysis
            
        except Exception as e:
            logger.error(f"Yahoo Finance analysis error for {symbol}: {e}")
            return {'error': f'Yahoo Finance analysis failed: {e}'}
    
    def _extract_trading_parameters(self, llm_response: str, current_price: float, volatility_factor: float) -> Dict[str, Any]:
        """Extract trading parameters from LLM response text."""
        import re
        
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
            
            # Extract entry price range
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
                # Default stop loss at 3% below entry for long positions
                params['stop_loss'] = params['optimal_entry'] * 0.97
            
            if not params.get('take_profit') and params.get('optimal_entry'):
                # Default take profit at 6% above entry for 2:1 risk/reward
                params['take_profit'] = params['optimal_entry'] * 1.06
            
            if not params.get('trailing_stop_activation') and params.get('take_profit'):
                # Activate trailing stop at 50% of the way to take profit
                entry = params.get('optimal_entry', current_price)
                target = params['take_profit']
                params['trailing_stop_activation'] = entry + (target - entry) * 0.5
            
            if not params.get('trailing_stop_distance'):
                # Default trailing stop distance based on volatility
                distance_pct = max(2.0, volatility_factor * 100 * 2)  # 2x daily volatility, minimum 2%
                params['trailing_stop_distance'] = f"{distance_pct:.1f}%"
            
            if not params.get('position_size'):
                params['position_size'] = "2-5% of portfolio"
            
            if not params.get('risk_reward_ratio'):
                params['risk_reward_ratio'] = "1:2"
            
        except Exception as e:
            logger.error(f"Error extracting trading parameters: {e}")
            # Provide basic fallback parameters
            params = {
                'position_direction': 'Long Buy',
                'optimal_entry': current_price,
                'stop_loss': current_price * 0.97,
                'take_profit': current_price * 1.06,
                'trailing_stop_activation': current_price * 1.03,
                'trailing_stop_distance': f"{max(2.0, volatility_factor * 100 * 2):.1f}%",
                'risk_reward_ratio': '1:2',
                'position_size': '2-5% of portfolio'
            }
        
        return params
    
    def _process_ohlcv_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Process OHLCV data into summary statistics."""
        try:
            if df.empty:
                return {}
            
            # Ensure all numeric columns are float type to avoid Decimal/float errors
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').astype(float)
            
            # Calculate price statistics
            recent_close = float(df['close'].iloc[-1])
            first_close = float(df['close'].iloc[0])
            price_change_30d = ((recent_close - first_close) / first_close) * 100
            
            # Calculate volatility (standard deviation of daily returns)
            daily_returns = df['close'].pct_change().dropna()
            volatility_30d = float(daily_returns.std() * np.sqrt(365) * 100)  # Annualized volatility
            
            # Volume analysis
            avg_volume_30d = float(df['volume'].mean())
            recent_volume = float(df['volume'].iloc[-1])
            volume_ratio = recent_volume / avg_volume_30d if avg_volume_30d > 0 else 1.0
            
            # Price levels
            high_30d = float(df['high'].max())
            low_30d = float(df['low'].min())
            
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
