#!/usr/bin/env python3
"""
AI Market Research Platform - Main CLI Interface
A local LLM-powered financial market research and educational analysis system.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

# Third-party imports
import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

# Local imports
from config import MarketResearcherConfig, get_config
from data.market_data import MarketDataManager
from llm.local_client import LocalLLMClient
from llm.prompt_manager import PromptManager
from agents.technical_agent import TechnicalAgent
from agents.sentiment_agent import SentimentAgent
from agents.news_agent import NewsAgent
from agents.risk_agent import RiskAgent
from agents.trading_agent import TradingAgent
from agents.scanner_agent import ScannerAgent
from prediction.engine import PredictionEngine
from prediction.decision_maker import DecisionMaker
from portfolio.manager import PortfolioManager
from config.settings import MarketResearcherConfig
from dataflows.finnhub_utils import get_data_in_range
from data.finnhub_client import FinnhubClient
from data.binance_client import BinanceClient
from analyzers.crypto_analyzer import CryptoAnalyzer
from analyzers.stock_analyzer import StockAnalyzer
from analyzers.forex_analyzer import ForexAnalyzer
from analyzers.commodity_futures_analyzer import CommodityFuturesAnalyzer
from data.polygon_client import PolygonClient
from data.commodity_client import CommodityClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/marketresearcher.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

console = Console()


class MarketResearcherCLI:
    """Command-line interface AI ai driven market research platform."""
    
    def __init__(self):
        """Initialize CLI components."""
        self.config = None
        self.market_data = None
        self.llm_client = None
        self.prompt_manager = None
        self.agents = {}
        self.prediction_engine = None
        self.decision_maker = None
        self.portfolio_manager = None
        self.crypto_analyzer = None
        self.stock_analyzer = None
        self.forex_analyzer = None
        self.commodity_analyzer = None
        self.bonds_analyzer = None
        self.derivatives_analyzer = None
        self.alpha_vantage_client = None
        self.commodity_client = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize all system components."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                
                # Load configuration
                task = progress.add_task("Loading configuration...", total=None)
                self.config = get_config()
                progress.update(task, description="✓ Configuration loaded")
                
                # Initialize portfolio manager
                task = progress.add_task("Setting up portfolio manager...", total=None)
                self.portfolio_manager = PortfolioManager(self.config)
                progress.update(task, description="✓ Portfolio manager ready")
                
                # Initialize Binance client if API keys are available
                self.binance_client = None
                if (hasattr(self.config, 'binance_api_key') and self.config.binance_api_key and 
                    hasattr(self.config, 'binance_secret_key') and self.config.binance_secret_key):
                    self.binance_client = BinanceClient(self.config)
                    await self.binance_client.initialize()
                
                # Initialize Finnhub client if API key is available
                self.finnhub_client = None
                if hasattr(self.config, 'finnhub_api_key') and self.config.finnhub_api_key:
                    self.finnhub_client = FinnhubClient(self.config.finnhub_api_key)
                
                # Initialize Polygon client if API key is available
                self.polygon_client = None
                if hasattr(self.config, 'polygon_api_key') and self.config.polygon_api_key:
                    self.polygon_client = PolygonClient(self.config.polygon_api_key)
                    await self.polygon_client.initialize()
                
                # Initialize Alpha Vantage client if API key is available
                self.alpha_vantage_client = None
                if hasattr(self.config, 'alpha_vantage_api_key') and self.config.alpha_vantage_api_key:
                    from data.alpha_vantage_client import AlphaVantageClient
                    self.alpha_vantage_client = AlphaVantageClient(self.config.alpha_vantage_api_key)
                    await self.alpha_vantage_client.initialize()
                
                # Initialize Commodity client
                self.commodity_client = None
                alpha_vantage_key = getattr(self.config, 'alpha_vantage_api_key', None)
                polygon_key = getattr(self.config, 'polygon_api_key', None)
                if alpha_vantage_key or polygon_key:
                    self.commodity_client = CommodityClient(
                        alpha_vantage_key=alpha_vantage_key,
                        polygon_key=polygon_key
                    )
                    await self.commodity_client.initialize()
                
                # Initialize market data manager
                task = progress.add_task("Setting up market data manager...", total=None)
                self.market_data = MarketDataManager(self.binance_client, self.config)
                progress.update(task, description="✓ Market data manager ready")
                
                # Initialize LLM client
                task = progress.add_task("Connecting to local LLM...", total=None)
                self.llm_client = LocalLLMClient(self.config)
                await self.llm_client.initialize()
                progress.update(task, description="✓ Local LLM connected")
                
                # Initialize prompt manager
                task = progress.add_task("Setting up prompt manager...", total=None)
                self.prompt_manager = PromptManager(self.config)
                progress.update(task, description="✓ Prompt manager ready")
                
                # Initialize agents
                task = progress.add_task("Initializing trading agents...", total=None)
                self.agents = {
                    'technical': TechnicalAgent(self.llm_client, self.prompt_manager, self.config),
                    'sentiment': SentimentAgent(self.llm_client, self.prompt_manager, self.config),
                    'news': NewsAgent(self.llm_client, self.prompt_manager, self.config),
                    'risk': RiskAgent(self.llm_client, self.prompt_manager, self.config),
                    'trading': TradingAgent(self.llm_client, self.prompt_manager, self.config),  # CLI mode with LLM
                    'scanner': ScannerAgent(self.llm_client, self.prompt_manager, self.config)
                }
                progress.update(task, description="✓ Trading agents initialized")
                
                # Initialize prediction engine
                task = progress.add_task("Setting up prediction engine...", total=None)
                self.prediction_engine = PredictionEngine(
                    self.agents, self.market_data, self.llm_client, self.prompt_manager, self.config
                )
                progress.update(task, description="✓ Prediction engine ready")
                
                # Initialize decision maker
                task = progress.add_task("Setting up decision maker...", total=None)
                self.decision_maker = DecisionMaker(self.config)
                progress.update(task, description="✓ Decision maker ready")
                
                # Initialize portfolio manager
                task = progress.add_task("Loading portfolio manager...", total=None)
                self.portfolio_manager = PortfolioManager(self.config)
                await self.portfolio_manager.initialize()
                progress.update(task, description="✓ Portfolio manager loaded")
                
                # Initialize analyzers
                task = progress.add_task("Setting up analyzers...", total=None)
                self.crypto_analyzer = CryptoAnalyzer(self.binance_client, self.prediction_engine, self.llm_client, config=self.config, market_data_manager=self.market_data)
                self.stock_analyzer = StockAnalyzer(self.finnhub_client, self.llm_client, config=self.config, prediction_engine=self.prediction_engine, market_data_manager=self.market_data)
                self.forex_analyzer = ForexAnalyzer(self.polygon_client, self.llm_client, config=self.config, prediction_engine=self.prediction_engine, market_data_manager=self.market_data)
                # Pass Alpha Vantage client to forex analyzer if available
                if hasattr(self, 'alpha_vantage_client') and self.alpha_vantage_client:
                    self.forex_analyzer.alpha_vantage_client = self.alpha_vantage_client
                # Initialize commodity futures analyzer
                self.commodity_analyzer = CommodityFuturesAnalyzer(self.commodity_client, self.llm_client, config=self.config)
                # Initialize bonds analyzer
                from analyzers.bonds_analyzer import BondsAnalyzer
                self.bonds_analyzer = BondsAnalyzer(llm_client=self.llm_client, config=self.config)
                # Initialize derivatives analyzer
                from analyzers.derivatives_analyzer import DerivativesAnalyzer
                self.derivatives_analyzer = DerivativesAnalyzer(llm_client=self.llm_client, config=self.config)
                progress.update(task, description="✓ Analyzers ready")
            
            self.initialized = True
            console.print("\n[green]✓ MarketResearcher initialization complete![/green]")
            
        except Exception as e:
            console.print(f"\n[red]✗ Initialization failed: {e}[/red]")
            logger.error(f"Initialization error: {e}")
            raise
    
    async def run(self):
        """Main CLI loop."""
        if not self.initialized:
            await self.initialize()
        
        # Display welcome message with regulatory disclaimer
        console.print(Panel.fit(
            "[bold blue]AI Market Research Platform[/bold blue]\n"
            "Educational financial market analysis powered by local LLM\n\n"
            "[bold yellow]DISCLAIMER:[/bold yellow] This platform provides automated analysis generated by AI.\n"
            "It is for educational and informational purposes only, and is NOT financial advice.\n"
            "Always conduct your own research and consult qualified financial professionals.\n"
            "[dim]All investments carry risk of loss. Past performance does not guarantee future results.[/dim]",
            title="Welcome"
        ))
        
        while True:
            try:
                action = await self._show_main_menu()
                
                if action == "analyze":
                    await self._analyze_symbol()
                elif action == "scanner":
                    await self._scanner_menu()
                elif action == "portfolio":
                    await self._portfolio_menu()
                elif action == "batch":
                    await self._batch_analysis()
                elif action == "settings":
                    await self._settings_menu()
                elif action == "history":
                    await self._view_history()
                elif action == "quit":
                    break
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Operation cancelled by user[/yellow]")
            except Exception as e:
                console.print(f"\n[red]Error: {e}[/red]")
                logger.error(f"CLI error: {e}")
        
        # Display regulatory disclaimer before exit
        console.print(Panel.fit(
            "[bold yellow]IMPORTANT DISCLAIMER[/bold yellow]\n\n"
            "This AI Market Research Platform provides automated analysis generated by AI.\n"
            "It is for educational and informational purposes only, and is NOT financial advice.\n\n"
            "[dim]• All analysis is educational market commentary\n"
            "• Past performance does not guarantee future results\n"
            "• Always conduct your own research\n"
            "• Consult qualified financial professionals before making investment decisions\n"
            "• All investments carry risk of loss[/dim]",
            title="Regulatory Compliance"
        ))
        console.print("\n[blue]Thank you for using the AI Market Research Platform![/blue]")
        await self._cleanup()
    
    async def _cleanup(self):
        """Clean up resources and close HTTP sessions."""
        try:
            # Close all HTTP client sessions
            if hasattr(self, 'polygon_client') and self.polygon_client:
                await self.polygon_client.close()
            
            if hasattr(self, 'alpha_vantage_client') and self.alpha_vantage_client:
                await self.alpha_vantage_client.close()
            
            if hasattr(self, 'commodity_client') and self.commodity_client:
                await self.commodity_client.close()
            
            # Close LLM client if it has a close method
            if hasattr(self, 'llm_client') and self.llm_client and hasattr(self.llm_client, 'close'):
                self.llm_client.close()
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def _show_main_menu(self) -> str:
        """Display main menu and get user choice."""
        choices = [
            "analyze - Market research & analysis",
            "scanner - Trading opportunity scanner",
            "portfolio - Portfolio research tools",
            "batch - Batch market analysis",
            "settings - View/modify settings",
            "history - View analysis history",
            "quit - Exit platform"
        ]      
        choice = await questionary.select(
            "What would you like to do?",
            choices=choices
        ).ask_async()
        
        return choice.split(" - ")[0] if choice else "quit"
    
    async def _analyze_symbol(self):
        """Analyze a single asset (cryptocurrency or stock)."""
        try:
            # Asset type selection
            asset_type = await questionary.select(
                "What type of asset would you like to analyze?",
                choices=[
                    "cryptocurrency - Cryptocurrency (Bitcoin, Ethereum, etc.)",
                    "stock - Stock (Apple, Tesla, etc.)",
                    "forex - Forex (EUR/USD, GBP/JPY, etc.)",
                    "commodity - Commodity Futures (Oil, Gas, Heating Oil, Cattle, Hogs Corn Wheat, Soybeans, etc.)",
                    "bonds - Government Bonds & Gilts (US Treasury, UK Gilts, EU Bonds, etc.)",
                    "derivatives - Derivatives (Options, Futures, Currency Derivatives, etc.)"
                ]
            ).ask_async()
            
            if not asset_type:
                return
            
            asset_type = asset_type.split(" - ")[0]
            
            if asset_type == "cryptocurrency":
                await self.crypto_analyzer.analyze_cryptocurrency()
            elif asset_type == "stock":
                await self.stock_analyzer.analyze_stock()
            elif asset_type == "forex":
                await self.forex_analyzer.analyze_forex()
            elif asset_type == "commodity":
                await self.commodity_analyzer.analyze_commodity()
            elif asset_type == "bonds":
                await self._analyze_bonds()
            elif asset_type == "derivatives":
                await self._analyze_derivatives()
                
        except Exception as e:
            console.print(f"[red]Error in asset analysis: {e}[/red]")
            logger.error(f"Asset analysis error: {e}")
    
    async def _scanner_menu(self):
        """Trading opportunity scanner menu."""
        while True:
            try:
                scanner_choices = [
                    "run - Run market scanners",
                    "specific - Run specific scanner",
                    "available - View available scanners",
                    "results - View recent scanner results",
                    "back - Return to main menu"
                ]
                
                choice = await questionary.select(
                    "Scanner Options:",
                    choices=scanner_choices
                ).ask_async()
                
                if not choice:
                    break
                    
                action = choice.split(" - ")[0]
                
                if action == "run":
                    await self._run_market_scanners()
                elif action == "specific":
                    await self._run_specific_scanner()
                elif action == "available":
                    await self._show_available_scanners()
                elif action == "results":
                    await self._show_scanner_results()
                elif action == "back":
                    break
                    
            except Exception as e:
                console.print(f"[red]Error in scanner menu: {e}[/red]")
                logger.error(f"Scanner menu error: {e}")
    
    async def _run_market_scanners(self):
        """Run comprehensive market scanners."""
        try:
            console.print("\n[blue]🔍 Running Market Scanners...[/blue]")
            
            # Scanner type selection
            scanner_types = await questionary.checkbox(
                "Select scanners to run (use SPACE to select, ENTER when done):",
                choices=[
                    questionary.Choice("Hot US Stocks by Volume", "hot_us_volume"),
                    questionary.Choice("Top % Gainers (IBIS)", "top_gainers_ibis"),
                    questionary.Choice("Most Active Futures (EUREX)", "active_futures_eurex"),
                    questionary.Choice("High Option Volume P/C Ratio", "high_option_volume"),
                    questionary.Choice("Complex Orders and Trades", "complex_orders")
                ]
            ).ask_async()
            
            if not scanner_types:
                console.print("[yellow]No scanners selected. Please select at least one scanner to run.[/yellow]")
                console.print("[dim]Tip: Use SPACE to select scanners, then ENTER to confirm[/dim]")
                return
            
            # Max results selection
            max_results = await questionary.text(
                "Maximum results per scanner (default: 20):",
                default="20"
            ).ask_async()
            
            try:
                max_results = int(max_results)
            except ValueError:
                max_results = 20
            
            # Run scanner analysis
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Running market scanners...", total=None)
                
                analysis_data = {
                    'scanner_types': scanner_types,
                    'max_results': max_results,
                    'use_cache': True
                }
                
                result = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    self.agents['scanner'].analyze,
                    None,  # symbol (not used for scanner)
                    analysis_data
                )
                
                progress.update(task, description="✓ Scanner analysis complete")
            
            # Display results
            if result.get('success'):
                await self._display_scanner_analysis(result)
            else:
                console.print(f"[red]Scanner analysis failed: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error running market scanners: {e}[/red]")
            logger.error(f"Market scanner error: {e}")
    
    async def _run_specific_scanner(self):
        """Run a specific scanner."""
        try:
            # Get available scanners
            available_scanners = self.agents['scanner'].get_available_scanners()
            
            scanner_choices = [
                questionary.Choice(f"{config['name']} - {config['description']}", key)
                for key, config in available_scanners.items()
            ]
            
            scanner_type = await questionary.select(
                "Select scanner to run:",
                choices=scanner_choices
            ).ask_async()
            
            if not scanner_type:
                return
            
            # Max results
            max_results = await questionary.text(
                "Maximum results (default: 20):",
                default="20"
            ).ask_async()
            
            try:
                max_results = int(max_results)
            except ValueError:
                max_results = 20
            
            # Run specific scanner
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"Running {available_scanners[scanner_type]['name']}...", total=None)
                
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.agents['scanner'].run_specific_scanner,
                    scanner_type,
                    max_results
                )
                
                progress.update(task, description="✓ Scanner complete")
            
            # Display results
            if result.get('success'):
                await self._display_specific_scanner_results(result)
            else:
                console.print(f"[red]Scanner failed: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error running specific scanner: {e}[/red]")
            logger.error(f"Specific scanner error: {e}")
    
    async def _show_available_scanners(self):
        """Show available scanner configurations."""
        try:
            available_scanners = self.agents['scanner'].get_available_scanners()
            
            table = Table(title="Available Market Scanners")
            table.add_column("Scanner ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Market", style="yellow")
            table.add_column("Asset Type", style="blue")
            table.add_column("Description", style="white")
            
            for scanner_id, config in available_scanners.items():
                table.add_row(
                    scanner_id,
                    config['name'],
                    config['market'],
                    config['asset_type'],
                    config['description']
                )
            
            console.print(table)
            
            # Wait for user to continue
            await questionary.press_any_key_to_continue().ask_async()
            
        except Exception as e:
            console.print(f"[red]Error showing available scanners: {e}[/red]")
            logger.error(f"Show scanners error: {e}")
    
    async def _show_scanner_results(self):
        """Show recent scanner results."""
        try:
            scanner_agent = self.agents['scanner']
            
            if not scanner_agent.last_analysis:
                console.print("[yellow]No recent scanner results available.[/yellow]")
                return
            
            result = scanner_agent.last_analysis
            await self._display_scanner_analysis(result)
            
        except Exception as e:
            console.print(f"[red]Error showing scanner results: {e}[/red]")
            logger.error(f"Show results error: {e}")
    
    async def _display_scanner_analysis(self, result: Dict[str, Any]):
        """Display comprehensive scanner analysis results."""
        try:
            console.print(f"\n[bold green]🎯 Trading Opportunity Scanner Results[/bold green]")
            console.print(f"[dim]Generated: {result.get('timestamp', 'Unknown')}[/dim]\n")
            
            # Scanner summary
            scanner_results = result.get('scanner_results', {})
            if scanner_results:
                summary_table = Table(title="Scanner Summary")
                summary_table.add_column("Scanner", style="cyan")
                summary_table.add_column("Results", style="green")
                summary_table.add_column("Description", style="white")
                
                for scanner_name, scanner_data in scanner_results.items():
                    results_count = scanner_data.get('results_count', 0)
                    description = scanner_data.get('description', 'N/A')
                    summary_table.add_row(scanner_name, str(results_count), description)
                
                console.print(summary_table)
            
            # Top opportunities
            top_opportunities = result.get('top_opportunities', [])
            if top_opportunities:
                console.print(f"\n[bold yellow]🏆 Top Trading Opportunities ({len(top_opportunities)})[/bold yellow]")
                
                opportunities_table = Table()
                opportunities_table.add_column("Rank", style="cyan")
                opportunities_table.add_column("Symbol", style="bold green")
                opportunities_table.add_column("Score", style="yellow")
                opportunities_table.add_column("Change %", style="red")
                opportunities_table.add_column("Volume", style="blue")
                opportunities_table.add_column("Market Cap", style="white")
                
                for i, opp in enumerate(top_opportunities[:10], 1):
                    symbol = opp.get('symbol', 'N/A')
                    score = opp.get('opportunity_score', 0)
                    change_pct = opp.get('changePercent', 0)
                    volume = opp.get('volume', 0)
                    market_cap = opp.get('marketCap', 0)
                    
                    # Format values
                    score_str = f"{score:.1f}/100"
                    change_str = f"{change_pct:+.2f}%"
                    volume_str = f"{volume:,.0f}" if volume > 0 else "N/A"
                    mcap_str = f"${market_cap/1e9:.1f}B" if market_cap > 1e9 else f"${market_cap/1e6:.0f}M" if market_cap > 1e6 else "N/A"
                    
                    opportunities_table.add_row(
                        str(i),
                        symbol,
                        score_str,
                        change_str,
                        volume_str,
                        mcap_str
                    )
                
                console.print(opportunities_table)
            
            # LLM Analysis
            llm_analysis = result.get('llm_analysis', {})
            if llm_analysis.get('success') and llm_analysis.get('analysis'):
                analysis_data = llm_analysis['analysis']
                console.print(f"\n[bold blue]🤖 AI Analysis Summary[/bold blue]")
                console.print(Panel(
                    analysis_data.get('summary', analysis_data.get('full_text', 'No analysis available')),
                    title="Market Scanner Analysis",
                    border_style="blue"
                ))
            
            # Statistics
            total_opportunities = result.get('opportunities_count', 0)
            console.print(f"\n[dim]Total opportunities found: {total_opportunities}[/dim]")
            
            # Wait for user to continue
            await questionary.press_any_key_to_continue().ask_async()
            
        except Exception as e:
            console.print(f"[red]Error displaying scanner analysis: {e}[/red]")
            logger.error(f"Display analysis error: {e}")
    
    async def _display_specific_scanner_results(self, result: Dict[str, Any]):
        """Display results from a specific scanner."""
        try:
            scanner_name = result.get('scanner_name', 'Unknown Scanner')
            results_count = result.get('results_count', 0)
            results = result.get('results', [])
            
            console.print(f"\n[bold green]📊 {scanner_name} Results[/bold green]")
            console.print(f"[dim]Found {results_count} opportunities[/dim]\n")
            
            if results:
                table = Table()
                table.add_column("Rank", style="cyan")
                table.add_column("Symbol", style="bold green")
                table.add_column("Score", style="yellow")
                table.add_column("Change %", style="red")
                table.add_column("Volume", style="blue")
                table.add_column("Price", style="white")
                
                for i, result_item in enumerate(results[:15], 1):
                    symbol = result_item.get('symbol', 'N/A')
                    score = result_item.get('opportunity_score', 0)
                    change_pct = result_item.get('changePercent', 0)
                    volume = result_item.get('volume', 0)
                    price = result_item.get('price', 0)
                    
                    # Format values
                    score_str = f"{score:.1f}/100"
                    change_str = f"{change_pct:+.2f}%"
                    volume_str = f"{volume:,.0f}" if volume > 0 else "N/A"
                    price_str = f"${price:.2f}" if price > 0 else "N/A"
                    
                    table.add_row(
                        str(i),
                        symbol,
                        score_str,
                        change_str,
                        volume_str,
                        price_str
                    )
                
                console.print(table)
            else:
                console.print("[yellow]No results to display.[/yellow]")
            
            # Wait for user to continue
            await questionary.press_any_key_to_continue().ask_async()
            
        except Exception as e:
            console.print(f"[red]Error displaying specific scanner results: {e}[/red]")
            logger.error(f"Display specific results error: {e}")
    
    async def _portfolio_menu(self):
        """Portfolio management menu."""
        while True:
            choices = [
                "view - View current portfolio",
                "add - Add position",
                "remove - Remove position",
                "cash - Adjust cash balance",
                "performance - View performance metrics",
                "risk - Risk analysis",
                "back - Return to main menu"
            ]
            
            choice = await questionary.select(
                "Portfolio Management:",
                choices=choices
            ).ask_async()
            
            if not choice:
                break
            
            action = choice.split(" - ")[0]
            
            if choice.startswith("view"):
                await self._view_portfolio()
            elif choice.startswith("add"):
                await self._add_position()
            elif choice.startswith("remove"):
                await self._remove_position()
            elif choice.startswith("cash"):
                await self._adjust_cash_balance()
            elif choice.startswith("performance"):
                await self._view_performance()
            elif choice.startswith("risk"):
                await self._view_risk_analysis()
            elif choice.startswith("back"):
                break
    
    async def _view_portfolio(self):
        """Display current portfolio positions."""
        try:
            positions_result = self.portfolio_manager.get_positions()
            
            if not positions_result.get("success", False):
                console.print(f"[red]Error getting positions: {positions_result.get('error', 'Unknown error')}[/red]")
                return
            
            positions = positions_result.get("positions", {})
            
            if not positions:
                console.print("[yellow]No positions in portfolio[/yellow]")
                # Show portfolio summary even with no positions
                cash_balance = positions_result.get("cash_balance", 0)
                total_value = positions_result.get("total_value", 0)
                
                summary_table = Table(title="Portfolio Summary")
                summary_table.add_column("Metric", style="cyan")
                summary_table.add_column("Value", style="magenta")
                
                summary_table.add_row("Cash Balance", f"${cash_balance:.2f}")
                summary_table.add_row("Total Portfolio Value", f"${total_value:.2f}")
                
                console.print(summary_table)
                return
            
            table = Table(title="Current Portfolio Positions")
            table.add_column("Symbol", style="cyan")
            table.add_column("Quantity", style="magenta")
            table.add_column("Avg Price", style="green")
            table.add_column("Current Price", style="yellow")
            table.add_column("P&L", style="red")
            table.add_column("P&L %", style="red")
            
            total_value = 0
            total_pnl = 0
            
            for symbol, position in positions.items():
                # Note: Price updates would need to be implemented via other data sources
                current_price = position.get("current_price", position["avg_price"])
                position_value = position["quantity"] * current_price
                pnl = (current_price - position["avg_price"]) * position["quantity"]
                pnl_pct = (pnl / (position["avg_price"] * position["quantity"])) * 100
                
                total_value += position_value
                total_pnl += pnl
                
                pnl_color = "green" if pnl >= 0 else "red"
                
                table.add_row(
                    symbol,
                    f"{position['quantity']:.4f}",
                    f"${position['avg_price']:.2f}",
                    f"${current_price:.2f}",
                    f"[{pnl_color}]${pnl:.2f}[/{pnl_color}]",
                    f"[{pnl_color}]{pnl_pct:.2f}%[/{pnl_color}]"
                )
            
            console.print(table)
            
            # Portfolio summary
            cash_balance = self.portfolio_manager.get_cash_balance()
            total_portfolio_value = total_value + cash_balance
            
            summary_table = Table(title="Portfolio Summary")
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", style="magenta")
            
            summary_table.add_row("Total Position Value", f"${total_value:.2f}")
            summary_table.add_row("Cash Balance", f"${cash_balance:.2f}")
            summary_table.add_row("Total Portfolio Value", f"${total_portfolio_value:.2f}")
            summary_table.add_row("Total P&L", f"${total_pnl:.2f}")
            
            console.print(summary_table)
            
        except Exception as e:
            console.print(f"[red]Error viewing portfolio: {e}[/red]")
            logger.error(f"Portfolio view error: {e}")
    
    async def _add_position(self):
        """Add a position to the portfolio."""
        try:
            # Get symbol
            symbol = await questionary.text(
                "Enter symbol (e.g., ETHUSDT):",
                validate=lambda x: len(x) > 0
            ).ask_async()
            
            if not symbol:
                return
            
            # Get quantity
            quantity_str = await questionary.text(
                "Enter quantity:",
                validate=lambda x: x.replace('.', '').isdigit() and float(x) > 0
            ).ask_async()
            
            if not quantity_str:
                return
            
            quantity = float(quantity_str)
            
            # Get average price
            price_str = await questionary.text(
                "Enter average price:",
                validate=lambda x: x.replace('.', '').isdigit() and float(x) > 0
            ).ask_async()
            
            if not price_str:
                return
            
            price = float(price_str)
            
            # Add position
            result = self.portfolio_manager.add_position(symbol, quantity, price)
            
            if result.get("success", False):
                console.print(f"[green]Successfully added position: {quantity} {symbol} at ${price}[/green]")
                console.print(f"[cyan]Remaining cash: ${result.get('remaining_cash', 0):.2f}[/cyan]")
            else:
                console.print(f"[red]Error adding position: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error adding position: {e}[/red]")
            logger.error(f"Add position error: {e}")
    
    
    async def _batch_analysis(self):
        """Run batch analysis on multiple symbols."""
        try:
            # Get symbols from user
            symbols_input = await questionary.text(
                "Enter symbols separated by commas (e.g., BTCUSDT,ETHUSDT,ADAUSDT):",
                default="BTCUSDT,ETHUSDT,ADAUSDT"
            ).ask_async()
            
            if not symbols_input:
                return
            
            symbols = [s.strip().upper() for s in symbols_input.split(",")]
            
            console.print(f"\n[blue]Running batch analysis on {len(symbols)} symbols...[/blue]")
            
            # Run batch prediction
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Running batch analysis...", total=None)
                
                results = await self.prediction_engine.batch_predict(symbols)
                
                progress.update(task, description="✓ Batch analysis complete")
            
            # Display batch results
            table = Table(title="Batch Analysis Results")
            table.add_column("Symbol", style="cyan")
            table.add_column("Decision", style="magenta")
            table.add_column("Confidence", style="green")
            table.add_column("Risk Level", style="yellow")
            table.add_column("Position Size", style="white")
            
            for symbol, result in results.items():
                if "error" not in result:
                    table.add_row(
                        symbol,
                        result.get("final_decision", "N/A"),
                        f"{result.get('confidence', 0):.1f}%",
                        result.get("risk_level", "N/A"),
                        f"{result.get('position_size', 0):.4f}"
                    )
                else:
                    table.add_row(symbol, "ERROR", "0%", "N/A", "0")
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Batch analysis failed: {e}[/red]")
            logger.error(f"Batch analysis error: {e}")
    
    async def _settings_menu(self):
        """Display and modify settings."""
        try:
            settings_table = Table(title="Current Settings")
            settings_table.add_column("Setting", style="cyan")
            settings_table.add_column("Value", style="magenta")
            
            # Display key settings
            settings_table.add_row("LLM Endpoint", self.config.llm_endpoint)
            settings_table.add_row("LLM Model", self.config.llm_model)
            settings_table.add_row("Risk Tolerance", f"{self.config.risk_tolerance:.2%}")
            settings_table.add_row("Max Position Size", f"{self.config.max_position_size:.2%}")
            settings_table.add_row("Default Symbols", ", ".join(self.config.default_symbols))
            
            console.print(settings_table)
            
        except Exception as e:
            console.print(f"[red]Error displaying settings: {e}[/red]")
            logger.error(f"Settings error: {e}")
    
    async def _view_history(self):
        """View analysis and trading history."""
        try:
            # Get recent predictions
            predictions = self.prediction_engine.get_prediction_history(limit=10)
            
            if not predictions:
                console.print("[yellow]No prediction history available[/yellow]")
                return
            
            table = Table(title="Recent Predictions")
            table.add_column("Timestamp", style="cyan")
            table.add_column("Symbol", style="magenta")
            table.add_column("Decision", style="green")
            table.add_column("Confidence", style="yellow")
            
            for pred in predictions:
                table.add_row(
                    pred.get("timestamp", "N/A"),
                    pred.get("symbol", "N/A"),
                    pred.get("final_decision", "N/A"),
                    f"{pred.get('confidence', 0):.1f}%"
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error viewing history: {e}[/red]")
            logger.error(f"History error: {e}")
    
    async def _view_performance(self):
        """View portfolio performance metrics."""
        try:
            performance = self.portfolio_manager.get_performance_metrics()
            
            table = Table(title="Portfolio Performance")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            
            for key, value in performance.items():
                if isinstance(value, float):
                    if "percentage" in key.lower() or "return" in key.lower():
                        table.add_row(key.replace("_", " ").title(), f"{value:.2%}")
                    else:
                        table.add_row(key.replace("_", " ").title(), f"${value:.2f}")
                else:
                    table.add_row(key.replace("_", " ").title(), str(value))
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error viewing performance: {e}[/red]")
            logger.error(f"Performance error: {e}")
    
    async def _analyze_portfolio_risk(self):
        """Analyze portfolio risk metrics."""
        try:
            risk_analysis = self.portfolio_manager.analyze_risk()
            
            if not risk_analysis.get("success", False):
                console.print(f"[red]Error: {risk_analysis.get('error', 'Unknown error')}[/red]")
                return
            
            risk_metrics = risk_analysis.get("risk_metrics", {})
            
            # Risk Analysis Table
            table = Table(title="Portfolio Risk Analysis")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            
            table.add_row("Portfolio Risk Level", str(risk_metrics.get("portfolio_risk", "Unknown")))
            table.add_row("Concentration Risk", f"{risk_metrics.get('concentration_risk', 0):.2f}%")
            table.add_row("Volatility Risk", str(risk_metrics.get("volatility_risk", "Unknown")))
            table.add_row("Diversification Score", f"{risk_metrics.get('diversification_score', 0):.2f}/100")
            table.add_row("Number of Positions", str(risk_metrics.get("num_positions", 0)))
            
            if risk_metrics.get("largest_position"):
                table.add_row("Largest Position", risk_metrics.get("largest_position", "N/A"))
                table.add_row("Largest Position Weight", f"{risk_metrics.get('largest_position_weight', 0):.2f}%")
            
            console.print(table)
            
            # Position Weights Table
            position_weights = risk_analysis.get("position_weights", {})
            if position_weights:
                weights_table = Table(title="Position Weights")
                weights_table.add_column("Symbol", style="cyan")
                weights_table.add_column("Weight %", style="magenta")
                
                # Sort by weight descending
                sorted_weights = sorted(position_weights.items(), key=lambda x: x[1], reverse=True)
                for symbol, weight in sorted_weights[:10]:  # Show top 10
                    weights_table.add_row(symbol, f"{weight:.2f}%")
                
                console.print(weights_table)
            
            # Display recommendations
            recommendations = risk_analysis.get('recommendations', [])
            if recommendations:
                console.print("\n[bold yellow]Risk Management Recommendations:[/bold yellow]")
                for i, rec in enumerate(recommendations, 1):
                    console.print(f"{i}. {rec}")
            
        except Exception as e:
            console.print(f"[red]Error analyzing portfolio risk: {e}[/red]")
            logger.error(f"Risk analysis error: {e}")
    
    async def _remove_position(self):
        """Remove a position from the portfolio."""
        try:
            # Get current positions
            positions_result = self.portfolio_manager.get_positions()
            
            if not positions_result.get("success", False):
                console.print(f"[red]Error getting positions: {positions_result.get('error', 'Unknown error')}[/red]")
                return
            
            positions = positions_result.get("positions", {})
            
            if not positions:
                console.print("[yellow]No positions to remove[/yellow]")
                return
            
            # Show current positions and let user select which to remove
            position_choices = []
            for symbol, position in positions.items():
                current_price = position.get("current_price", position["avg_price"])
                position_value = position["quantity"] * current_price
                position_choices.append(f"{symbol} - {position['quantity']} @ ${position['avg_price']:.4f} (Value: ${position_value:.2f})")
            
            position_choices.append("Cancel - Go back")
            
            choice = await questionary.select(
                "Select position to remove:",
                choices=position_choices
            ).ask_async()
            
            if not choice or choice.startswith("Cancel"):
                return
            
            symbol = choice.split(" - ")[0]
            position = positions[symbol]
            
            # Ask for quantity to remove (default to full position)
            max_quantity = position["quantity"]
            quantity_input = await questionary.text(
                f"Enter quantity to remove (max: {max_quantity}, press Enter for full position):",
                default=str(max_quantity)
            ).ask_async()
            
            if not quantity_input:
                return
            
            try:
                quantity = float(quantity_input)
            except ValueError:
                console.print("[red]Invalid quantity entered[/red]")
                return
            
            if quantity <= 0 or quantity > max_quantity:
                console.print(f"[red]Quantity must be between 0 and {max_quantity}[/red]")
                return
            
            # Ask for current price (optional)
            current_price = position.get("current_price", position["avg_price"])
            price_input = await questionary.text(
                f"Enter current price (press Enter to use stored price: ${current_price:.4f}):",
                default=""
            ).ask_async()
            
            if price_input:
                try:
                    current_price = float(price_input)
                except ValueError:
                    console.print("[red]Invalid price entered, using stored price[/red]")
            
            # Confirm removal
            position_value = quantity * current_price
            confirm = await questionary.confirm(
                f"Remove {quantity} {symbol} at ${current_price:.4f} (Value: ${position_value:.2f})?"
            ).ask_async()
            
            if not confirm:
                return
            
            # Remove the position
            result = self.portfolio_manager.close_position(
                symbol=symbol,
                quantity=quantity,
                price=current_price
            )
            
            if result.get("success", False):
                pnl = result.get("pnl", 0)
                pnl_pct = result.get("pnl_pct", 0)
                pnl_color = "green" if pnl >= 0 else "red"
                
                console.print(f"[green]Successfully removed {quantity} {symbol} at ${current_price:.4f}[/green]")
                console.print(f"[{pnl_color}]P&L: ${pnl:.2f} ({pnl_pct:.2f}%)[/{pnl_color}]")
                console.print(f"[cyan]Cash balance: ${result.get('remaining_cash', 0):.2f}[/cyan]")
                
                # Show updated portfolio
                await self._view_portfolio()
            else:
                console.print(f"[red]Error removing position: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error removing position: {e}[/red]")
            logger.error(f"Remove position error: {e}")

    async def _adjust_cash_balance(self):
        """Adjust the cash balance in the portfolio."""
        try:
            # Get current cash balance
            current_balance = self.portfolio_manager.get_cash_balance()
            console.print(f"[cyan]Current cash balance: ${current_balance:.2f}[/cyan]")
            
            # Ask for adjustment type
            adjustment_type = await questionary.select(
                "How would you like to adjust your cash balance?",
                choices=[
                    "add - Add cash (deposit)",
                    "subtract - Remove cash (withdrawal)",
                    "set - Set specific amount",
                    "cancel - Cancel adjustment"
                ]
            ).ask_async()
            
            if not adjustment_type or adjustment_type.startswith("cancel"):
                return
            
            if adjustment_type.startswith("set"):
                # Set specific amount
                new_balance_input = await questionary.text(
                    f"Enter new cash balance (current: ${current_balance:.2f}):"
                ).ask_async()
                
                if not new_balance_input:
                    return
                
                try:
                    new_balance = float(new_balance_input)
                    if new_balance < 0:
                        console.print("[red]Cash balance cannot be negative[/red]")
                        return
                    
                    adjustment_amount = new_balance - current_balance
                    reason = f"Set balance to ${new_balance:.2f}"
                    
                except ValueError:
                    console.print("[red]Invalid amount entered[/red]")
                    return
            
            else:
                # Add or subtract cash
                amount_input = await questionary.text(
                    "Enter amount to adjust:"
                ).ask_async()
                
                if not amount_input:
                    return
                
                try:
                    amount = float(amount_input)
                    if amount <= 0:
                        console.print("[red]Amount must be positive[/red]")
                        return
                    
                    if adjustment_type.startswith("subtract"):
                        adjustment_amount = -amount
                        reason = f"Withdrawal of ${amount:.2f}"
                    else:
                        adjustment_amount = amount
                        reason = f"Deposit of ${amount:.2f}"
                        
                except ValueError:
                    console.print("[red]Invalid amount entered[/red]")
                    return
            
            # Ask for reason/description
            reason_input = await questionary.text(
                f"Enter reason for adjustment (optional, default: '{reason}'):",
                default=""
            ).ask_async()
            
            if reason_input:
                reason = reason_input
            
            # Show preview and confirm
            new_balance = current_balance + adjustment_amount
            console.print(f"\n[yellow]Adjustment Preview:[/yellow]")
            console.print(f"Current balance: ${current_balance:.2f}")
            console.print(f"Adjustment: ${adjustment_amount:+.2f}")
            console.print(f"New balance: ${new_balance:.2f}")
            console.print(f"Reason: {reason}")
            
            confirm = await questionary.confirm(
                "Proceed with this cash adjustment?"
            ).ask_async()
            
            if not confirm:
                return
            
            # Apply the adjustment
            result = self.portfolio_manager.adjust_cash_balance(adjustment_amount, reason)
            
            if result.get("success", False):
                console.print(f"[green]✓ Cash balance successfully adjusted[/green]")
                console.print(f"[cyan]Old balance: ${result['old_balance']:.2f}[/cyan]")
                console.print(f"[cyan]New balance: ${result['new_balance']:.2f}[/cyan]")
                console.print(f"[cyan]Adjustment: ${result['adjustment']:+.2f}[/cyan]")
                console.print(f"[dim]Reason: {result['reason']}[/dim]")
                
                # Show updated portfolio
                await self._view_portfolio()
            else:
                console.print(f"[red]Error adjusting cash balance: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error adjusting cash balance: {e}[/red]")
            logger.error(f"Cash adjustment error: {e}")

    async def _analyze_bonds(self):
        """Analyze government bonds and gilts."""
        try:
            while True:
                analysis_type = await questionary.select(
                    "What type of bonds analysis would you like to perform?",
                    choices=[
                        "market - Analyze specific market bonds",
                        "curve - View yield curve",
                        "compare - Compare international bonds",
                        "trends - Analyze bond trends",
                        "back - Return to asset selection"
                    ]
                ).ask_async()
                
                if not analysis_type or analysis_type.startswith("back"):
                    break
                
                analysis_type = analysis_type.split(" - ")[0]
                
                if analysis_type == "market":
                    await self._analyze_market_bonds()
                elif analysis_type == "curve":
                    await self._view_yield_curve()
                elif analysis_type == "compare":
                    await self._compare_international_bonds()
                elif analysis_type == "trends":
                    await self._analyze_bond_trends()
                    
        except Exception as e:
            console.print(f"[red]Error in bonds analysis: {e}[/red]")
            logger.error(f"Bonds analysis error: {e}")
    
    async def _analyze_market_bonds(self):
        """Analyze bonds from a specific market."""
        try:
            markets = self.bonds_analyzer.get_available_markets()
            market_choices = [
                f"{market} - {market.replace('_', ' ').title()}" 
                for market in markets
            ]
            market_choices.append("back - Return to bonds menu")
            
            market_choice = await questionary.select(
                "Select bond market to analyze:",
                choices=market_choices
            ).ask_async()
            
            if not market_choice or market_choice.startswith("back"):
                return
            
            market = market_choice.split(" - ")[0]
            
            # Ask for analysis period
            period = await questionary.select(
                "Select analysis period:",
                choices=[
                    "1d - 1 Day",
                    "1mo - 1 Month", 
                    "3mo - 3 Months",
                    "6mo - 6 Months",
                    "1y - 1 Year"
                ]
            ).ask_async()
            
            if not period:
                return
            
            period = period.split(" - ")[0]
            
            console.print(f"\n[cyan]Analyzing {market.replace('_', ' ')} bonds...[/cyan]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Fetching bond data...", total=None)
                
                result = await self.bonds_analyzer.analyze_market_bonds(market, period)
                
                progress.update(task, description="✓ Analysis complete")
            
            if result.get("success", False):
                # Display market summary
                summary = result["summary"]
                console.print(f"\n[bold green]📊 {market.replace('_', ' ').title()} Bonds Analysis[/bold green]")
                console.print(f"[cyan]Average Yield: {summary['average_yield']:.3f}%[/cyan]")
                console.print(f"[cyan]Average Change: {summary['average_change']:+.3f}%[/cyan]")
                console.print(f"[dim]Bonds Analyzed: {summary['bonds_analyzed']}/{summary['total_bonds']}[/dim]")
                
                # Display individual bonds
                console.print(f"\n[bold]Individual Bond Details:[/bold]")
                
                for bond_data in result["bonds"]:
                    if bond_data.get("success", False):
                        bond = bond_data["bond_info"]
                        current_yield = bond_data["current_yield"]
                        change = bond_data["change"]
                        change_pct = bond_data["change_pct"]
                        
                        change_color = "green" if change >= 0 else "red"
                        
                        console.print(f"• [bold]{bond.name}[/bold] ({bond.maturity})")
                        console.print(f"  Yield: {current_yield:.3f}% [{change_color}]({change:+.3f}, {change_pct:+.2f}%)[/{change_color}]")
                        console.print(f"  52W Range: {bond_data['low_52w']:.3f}% - {bond_data['high_52w']:.3f}%")
                    else:
                        bond = bond_data["bond_info"]
                        console.print(f"• [dim]{bond.name}: {bond_data.get('error', 'No data')}[/dim]")
                
                console.print(f"\n[dim]Last updated: {result['last_updated']}[/dim]")
                
                # Add AI analysis for bonds market
                console.print(f"\n[cyan]Generating AI market analysis...[/cyan]")
                ai_result = await self.bonds_analyzer.analyze_bonds_with_ai(result)
                
                if ai_result.get("success", False):
                    console.print(f"\n[bold yellow]🤖 AI Market Analysis - {market.replace('_', ' ').title()}[/bold yellow]")
                    console.print(f"[white]{ai_result['ai_analysis']}[/white]")
                else:
                    console.print(f"[yellow]AI analysis unavailable: {ai_result.get('error', 'Unknown error')}[/yellow]")
                
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error analyzing bonds market: {e}[/red]")
            logger.error(f"Bonds market analysis error: {e}")
    
    async def _view_yield_curve(self):
        """View yield curve for a country."""
        try:
            country_choice = await questionary.select(
                "Select country for yield curve:",
                choices=[
                    "US - United States Treasury",
                    "UK - United Kingdom Gilts",
                    "back - Return to bonds menu"
                ]
            ).ask_async()
            
            if not country_choice or country_choice.startswith("back"):
                return
            
            country = country_choice.split(" - ")[0]
            
            console.print(f"\n[cyan]Fetching {country} yield curve...[/cyan]")
            
            result = await self.bonds_analyzer.get_yield_curve_data(country)
            
            if result.get("success", False):
                console.print(f"\n[bold green]📈 {country} Yield Curve[/bold green]")
                
                curve_data = result["curve_data"]
                if curve_data:
                    console.print("\n[bold]Maturity vs Yield:[/bold]")
                    for point in curve_data:
                        maturity = point["maturity"]
                        yield_val = point["yield"]
                        name = point["name"]
                        
                        if maturity < 1:
                            maturity_str = f"{int(maturity * 12)}M"
                        else:
                            maturity_str = f"{int(maturity)}Y"
                        
                        console.print(f"  {maturity_str:>4} | {yield_val:>6.3f}% | {name}")
                    
                    console.print(f"\n[dim]Last updated: {result['last_updated']}[/dim]")
                    
                    # Add AI analysis for yield curve
                    console.print(f"\n[cyan]Generating AI yield curve analysis...[/cyan]")
                    ai_result = await self.bonds_analyzer.analyze_yield_curve_with_ai(result)
                    
                    if ai_result.get("success", False):
                        console.print(f"\n[bold yellow]🤖 AI Yield Curve Analysis - {country}[/bold yellow]")
                        console.print(f"[white]{ai_result['ai_analysis']}[/white]")
                    else:
                        console.print(f"[yellow]AI analysis unavailable: {ai_result.get('error', 'Unknown error')}[/yellow]")
                else:
                    console.print("[yellow]No yield curve data available[/yellow]")
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error viewing yield curve: {e}[/red]")
            logger.error(f"Yield curve error: {e}")
    
    async def _compare_international_bonds(self):
        """Compare bonds across different countries."""
        try:
            maturity = await questionary.select(
                "Select maturity to compare:",
                choices=[
                    "2Y - 2 Year",
                    "5Y - 5 Year", 
                    "10Y - 10 Year",
                    "30Y - 30 Year"
                ]
            ).ask_async()
            
            if not maturity:
                return
            
            maturity = maturity.split(" - ")[0]
            
            console.print(f"\n[cyan]Comparing international {maturity} bonds...[/cyan]")
            
            result = await self.bonds_analyzer.compare_international_bonds(maturity)
            
            if result.get("success", False):
                console.print(f"\n[bold green]🌍 International {maturity} Bond Comparison[/bold green]")
                
                comparison = result["comparison"]
                if comparison:
                    console.print(f"\n[bold]Ranked by Yield (Highest to Lowest):[/bold]")
                    
                    for i, bond in enumerate(comparison, 1):
                        yield_val = bond["yield"]
                        change = bond["change"]
                        change_pct = bond["change_pct"]
                        country = bond["country"]
                        currency = bond["currency"]
                        
                        change_color = "green" if change >= 0 else "red"
                        
                        console.print(f"{i:>2}. [bold]{country}[/bold] ({currency})")
                        console.print(f"    Yield: {yield_val:.3f}% [{change_color}]({change:+.3f}, {change_pct:+.2f}%)[/{change_color}]")
                    
                    console.print(f"\n[dim]Last updated: {result['last_updated']}[/dim]")
                    
                    # Add AI analysis for international bonds
                    console.print(f"\n[cyan]Generating AI international bonds analysis...[/cyan]")
                    ai_result = await self.bonds_analyzer.analyze_international_bonds_with_ai(result)
                    
                    if ai_result.get("success", False):
                        console.print(f"\n[bold yellow]🤖 AI International Bonds Analysis - {maturity}[/bold yellow]")
                        console.print(f"[white]{ai_result['ai_analysis']}[/white]")
                    else:
                        console.print(f"[yellow]AI analysis unavailable: {ai_result.get('error', 'Unknown error')}[/yellow]")
                else:
                    console.print("[yellow]No comparison data available[/yellow]")
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error comparing international bonds: {e}[/red]")
            logger.error(f"International bonds comparison error: {e}")
    
    async def _analyze_bond_trends(self):
        """Analyze bond yield trends over time."""
        try:
            markets = self.bonds_analyzer.get_available_markets()
            market_choices = [
                f"{market} - {market.replace('_', ' ').title()}" 
                for market in markets
            ]
            
            market_choice = await questionary.select(
                "Select market for trend analysis:",
                choices=market_choices
            ).ask_async()
            
            if not market_choice:
                return
            
            market = market_choice.split(" - ")[0]
            
            period = await questionary.select(
                "Select analysis period:",
                choices=[
                    "1mo - 1 Month",
                    "3mo - 3 Months", 
                    "6mo - 6 Months",
                    "1y - 1 Year"
                ]
            ).ask_async()
            
            if not period:
                return
            
            period = period.split(" - ")[0]
            
            console.print(f"\n[cyan]Analyzing {market.replace('_', ' ')} bond trends over {period}...[/cyan]")
            
            result = await self.bonds_analyzer.analyze_bond_trends(market, period)
            
            if result.get("success", False):
                console.print(f"\n[bold green]📊 {market.replace('_', ' ').title()} Bond Trends ({period})[/bold green]")
                
                trends = result["trends"]
                if trends:
                    for trend in trends:
                        bond_name = trend["bond"]
                        maturity = trend["maturity"]
                        start_yield = trend["start_yield"]
                        end_yield = trend["end_yield"]
                        total_change = trend["total_change"]
                        total_change_pct = trend["total_change_pct"]
                        trend_direction = trend["trend"]
                        volatility = trend["volatility"]
                        
                        # Color based on trend
                        if trend_direction == "Rising":
                            trend_color = "red"
                        elif trend_direction == "Falling":
                            trend_color = "green"
                        else:
                            trend_color = "yellow"
                        
                        console.print(f"\n[bold]{bond_name}[/bold] ({maturity})")
                        console.print(f"  Start: {start_yield:.3f}% → End: {end_yield:.3f}%")
                        console.print(f"  Change: {total_change:+.3f}% ({total_change_pct:+.2f}%)")
                        console.print(f"  Trend: [{trend_color}]{trend_direction}[/{trend_color}]")
                        console.print(f"  Volatility: {volatility:.3f}%")
                    
                    console.print(f"\n[dim]Last updated: {result['last_updated']}[/dim]")
                    
                    # Add AI analysis for bond trends
                    console.print(f"\n[cyan]Generating AI bond trends analysis...[/cyan]")
                    ai_result = await self.bonds_analyzer.analyze_bond_trends_with_ai(result)
                    
                    if ai_result.get("success", False):
                        console.print(f"\n[bold yellow]🤖 AI Bond Trends Analysis - {market.replace('_', ' ').title()}[/bold yellow]")
                        console.print(f"[white]{ai_result['ai_analysis']}[/white]")
                    else:
                        console.print(f"[yellow]AI analysis unavailable: {ai_result.get('error', 'Unknown error')}[/yellow]")
                else:
                    console.print("[yellow]No trend data available[/yellow]")
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error analyzing bond trends: {e}[/red]")
            logger.error(f"Bond trends analysis error: {e}")

    async def _analyze_derivatives(self):
        """Analyze derivatives instruments."""
        try:
            while True:
                derivative_type = await questionary.select(
                    "What type of derivatives would you like to analyze?",
                    choices=[
                        "stock_options - Stock Options (calls, puts, Greeks)",
                        "index_futures - Equity Index Futures (SPX, NDX, RUT)",
                        "index_options - Equity Index Options (SPX, NDX, VIX)",
                        "currency - Currency Derivatives (FX futures, options)",
                        "rates - Interest Rate Derivatives (bond futures, rates)",
                        "crypto - Crypto Derivatives (BTC/ETH futures)",
                        "volatility - Volatility Surface Analysis",
                        "back - Return to asset selection"
                    ]
                ).ask_async()
                
                if not derivative_type or derivative_type.startswith("back"):
                    break
                
                derivative_type = derivative_type.split(" - ")[0]
                
                if derivative_type == "stock_options":
                    await self._analyze_stock_options()
                elif derivative_type == "index_futures":
                    await self._analyze_index_futures()
                elif derivative_type == "index_options":
                    await self._analyze_index_options()
                elif derivative_type == "currency":
                    await self._analyze_currency_derivatives()
                elif derivative_type == "rates":
                    await self._analyze_rates_derivatives()
                elif derivative_type == "crypto":
                    await self._analyze_crypto_derivatives()
                elif derivative_type == "volatility":
                    await self._analyze_volatility_surface()
                    
        except Exception as e:
            console.print(f"[red]Error in derivatives analysis: {e}[/red]")
            logger.error(f"Derivatives analysis error: {e}")
    
    async def _analyze_stock_options(self):
        """Analyze stock options."""
        try:
            # Get symbol from user
            symbol = await questionary.text(
                "Enter stock symbol for options analysis (e.g., AAPL, TSLA):"
            ).ask_async()
            
            if not symbol:
                return
            
            symbol = symbol.upper().strip()
            
            console.print(f"\n[cyan]Analyzing options for {symbol}...[/cyan]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Fetching options data...", total=None)
                
                result = await self.derivatives_analyzer.analyze_stock_options(symbol)
                
                progress.update(task, description="✓ Analysis complete")
            
            if result.get("success", False):
                current_price = result["current_price"]
                console.print(f"\n[bold green]📊 {symbol} Options Analysis[/bold green]")
                console.print(f"[cyan]Current Stock Price: ${current_price:.2f}[/cyan]")
                
                # Group options by expiry
                options_by_expiry = {}
                for option in result["options_data"]:
                    expiry = option["expiry"]
                    if expiry not in options_by_expiry:
                        options_by_expiry[expiry] = {"calls": [], "puts": []}
                    
                    if option["type"] == "call":
                        options_by_expiry[expiry]["calls"].append(option)
                    else:
                        options_by_expiry[expiry]["puts"].append(option)
                
                for expiry, expiry_data in options_by_expiry.items():
                    # Calculate days to expiry
                    try:
                        expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
                        days_to_expiry = (expiry_date - datetime.now()).days
                    except:
                        days_to_expiry = 0
                    
                    console.print(f"\n[bold]Expiry: {expiry} ({days_to_expiry} days)[/bold]")
                    
                    # Show top 5 calls and puts by volume
                    calls = sorted(expiry_data["calls"], key=lambda x: x["volume"], reverse=True)[:5]
                    puts = sorted(expiry_data["puts"], key=lambda x: x["volume"], reverse=True)[:5]
                    
                    if calls:
                        console.print("\n[bold cyan]Top Calls by Volume:[/bold cyan]")
                        for call in calls:
                            strike = call["strike"]
                            last_price = call["last_price"]
                            volume = call["volume"]
                            iv = call["implied_vol"]
                            delta = call["greeks"]["delta"]
                            
                            itm_indicator = "ITM" if strike < current_price else "OTM"
                            itm_color = "green" if strike < current_price else "yellow"
                            
                            console.print(f"  ${strike:>7.2f} | ${last_price:>6.2f} | Vol: {volume:>6} | IV: {iv:>5.1%} | Δ: {delta:>5.3f} | [{itm_color}]{itm_indicator}[/{itm_color}]")
                    
                    if puts:
                        console.print("\n[bold magenta]Top Puts by Volume:[/bold magenta]")
                        for put in puts:
                            strike = put["strike"]
                            last_price = put["last_price"]
                            volume = put["volume"]
                            iv = put["implied_vol"]
                            delta = put["greeks"]["delta"]
                            
                            itm_indicator = "ITM" if strike > current_price else "OTM"
                            itm_color = "green" if strike > current_price else "yellow"
                            
                            console.print(f"  ${strike:>7.2f} | ${last_price:>6.2f} | Vol: {volume:>6} | IV: {iv:>5.1%} | Δ: {delta:>6.3f} | [{itm_color}]{itm_indicator}[/{itm_color}]")
                
                console.print(f"\n[dim]Last updated: {result['last_updated']}[/dim]")
                
                # Add AI analysis
                console.print(f"\n[cyan]Generating AI analysis...[/cyan]")
                ai_result = await self.derivatives_analyzer.analyze_options_with_ai(result)
                
                if ai_result.get("success", False):
                    console.print(f"\n[bold yellow]🤖 AI Analysis for {symbol} Options[/bold yellow]")
                    console.print(f"[white]{ai_result['ai_analysis']}[/white]")
                else:
                    console.print(f"[yellow]AI analysis unavailable: {ai_result.get('error', 'Unknown error')}[/yellow]")
                
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error analyzing stock options: {e}[/red]")
            logger.error(f"Stock options analysis error: {e}")
    
    async def _analyze_index_futures(self):
        """Analyze equity index futures."""
        try:
            console.print(f"\n[cyan]Analyzing equity index futures...[/cyan]")
            
            result = await self.derivatives_analyzer.analyze_index_futures("INDEX_FUTURES")
            
            if result.get("success", False):
                console.print(f"\n[bold green]📈 Equity Index Futures Analysis[/bold green]")
                console.print(f"[cyan]Contracts Analyzed: {result['contracts_analyzed']}/{result['total_contracts']}[/cyan]")
                
                for future in result["futures_data"]:
                    if future.get("success", False):
                        name = future["name"]
                        current_price = future["current_price"]
                        change = future["change"]
                        change_pct = future["change_pct"]
                        volatility = future["volatility"]
                        volume = future["volume"]
                        
                        change_color = "green" if change >= 0 else "red"
                        
                        console.print(f"\n[bold]{name}[/bold]")
                        console.print(f"  Price: {current_price:>8.2f} [{change_color}]({change:+.2f}, {change_pct:+.2f}%)[/{change_color}]")
                        console.print(f"  Volatility: {volatility:>5.1f}% | Volume: {volume:>10,.0f}")
                        console.print(f"  Contract: {future['contract_size']} | Exchange: {future['exchange']}")
                    else:
                        console.print(f"\n[dim]{future['name']}: {future.get('error', 'No data')}[/dim]")
                
                console.print(f"\n[dim]Last updated: {result['last_updated']}[/dim]")
                
                # Add AI analysis for futures
                console.print(f"\n[cyan]Generating AI market analysis...[/cyan]")
                ai_result = await self.derivatives_analyzer.analyze_futures_with_ai(result, "INDEX_FUTURES")
                
                if ai_result.get("success", False):
                    console.print(f"\n[bold yellow]🤖 AI Market Analysis - Index Futures[/bold yellow]")
                    console.print(f"[white]{ai_result['ai_analysis']}[/white]")
                else:
                    console.print(f"[yellow]AI analysis unavailable: {ai_result.get('error', 'Unknown error')}[/yellow]")
                
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error analyzing index futures: {e}[/red]")
            logger.error(f"Index futures analysis error: {e}")
    
    async def _analyze_index_options(self):
        """Analyze equity index options."""
        try:
            index_choice = await questionary.select(
                "Select index for options analysis:",
                choices=[
                    "SPX - S&P 500 Index Options",
                    "NDX - NASDAQ 100 Index Options", 
                    "RUT - Russell 2000 Index Options",
                    "VIX - VIX Options"
                ]
            ).ask_async()
            
            if not index_choice:
                return
            
            symbol = index_choice.split(" - ")[0]
            
            console.print(f"\n[cyan]Analyzing {symbol} options...[/cyan]")
            
            result = await self.derivatives_analyzer.analyze_stock_options(symbol)
            
            if result.get("success", False):
                await self._display_options_analysis(result, f"{symbol} Index Options")
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error analyzing index options: {e}[/red]")
            logger.error(f"Index options analysis error: {e}")
    
    async def _analyze_currency_derivatives(self):
        """Analyze currency derivatives."""
        try:
            console.print(f"\n[cyan]Analyzing currency derivatives...[/cyan]")
            
            result = await self.derivatives_analyzer.analyze_currency_derivatives()
            
            if result.get("success", False):
                console.print(f"\n[bold green]💱 Currency Derivatives Analysis[/bold green]")
                console.print(f"[cyan]Contracts Analyzed: {result['contracts_analyzed']}/{result['total_contracts']}[/cyan]")
                
                for future in result["futures_data"]:
                    if future.get("success", False):
                        name = future["name"]
                        underlying = future["underlying"]
                        current_price = future["current_price"]
                        change = future["change"]
                        change_pct = future["change_pct"]
                        volatility = future["volatility"]
                        
                        change_color = "green" if change >= 0 else "red"
                        
                        console.print(f"\n[bold]{underlying}[/bold] - {name}")
                        console.print(f"  Price: {current_price:>8.4f} [{change_color}]({change:+.4f}, {change_pct:+.2f}%)[/{change_color}]")
                        console.print(f"  Volatility: {volatility:>5.1f}% | Contract: {future['contract_size']}")
                    else:
                        console.print(f"\n[dim]{future['name']}: {future.get('error', 'No data')}[/dim]")
                
                console.print(f"\n[dim]Last updated: {result['last_updated']}[/dim]")
                
                # Add AI analysis for currency derivatives
                console.print(f"\n[cyan]Generating AI market analysis...[/cyan]")
                ai_result = await self.derivatives_analyzer.analyze_futures_with_ai(result, "CURRENCY_DERIVATIVES")
                
                if ai_result.get("success", False):
                    console.print(f"\n[bold yellow]🤖 AI Market Analysis - Currency Derivatives[/bold yellow]")
                    console.print(f"[white]{ai_result['ai_analysis']}[/white]")
                else:
                    console.print(f"[yellow]AI analysis unavailable: {ai_result.get('error', 'Unknown error')}[/yellow]")
                
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error analyzing currency derivatives: {e}[/red]")
            logger.error(f"Currency derivatives analysis error: {e}")
    
    async def _analyze_rates_derivatives(self):
        """Analyze interest rate derivatives."""
        try:
            console.print(f"\n[cyan]Analyzing interest rate derivatives...[/cyan]")
            
            result = await self.derivatives_analyzer.analyze_rates_derivatives()
            
            if result.get("success", False):
                console.print(f"\n[bold green]📊 Interest Rate Derivatives Analysis[/bold green]")
                console.print(f"[cyan]Contracts Analyzed: {result['contracts_analyzed']}/{result['total_contracts']}[/cyan]")
                
                for future in result["futures_data"]:
                    if future.get("success", False):
                        name = future["name"]
                        underlying = future["underlying"]
                        current_price = future["current_price"]
                        change = future["change"]
                        change_pct = future["change_pct"]
                        volatility = future["volatility"]
                        
                        change_color = "green" if change >= 0 else "red"
                        
                        console.print(f"\n[bold]{underlying}[/bold] - {name}")
                        console.print(f"  Price: {current_price:>8.3f} [{change_color}]({change:+.3f}, {change_pct:+.2f}%)[/{change_color}]")
                        console.print(f"  Volatility: {volatility:>5.1f}% | Contract: {future['contract_size']}")
                    else:
                        console.print(f"\n[dim]{future['name']}: {future.get('error', 'No data')}[/dim]")
                
                console.print(f"\n[dim]Last updated: {result['last_updated']}[/dim]")
                
                # Add AI analysis for rates derivatives
                console.print(f"\n[cyan]Generating AI market analysis...[/cyan]")
                ai_result = await self.derivatives_analyzer.analyze_futures_with_ai(result, "RATES_DERIVATIVES")
                
                if ai_result.get("success", False):
                    console.print(f"\n[bold yellow]🤖 AI Market Analysis - Interest Rate Derivatives[/bold yellow]")
                    console.print(f"[white]{ai_result['ai_analysis']}[/white]")
                else:
                    console.print(f"[yellow]AI analysis unavailable: {ai_result.get('error', 'Unknown error')}[/yellow]")
                
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error analyzing rates derivatives: {e}[/red]")
            logger.error(f"Rates derivatives analysis error: {e}")
    
    async def _analyze_crypto_derivatives(self):
        """Analyze cryptocurrency derivatives."""
        try:
            console.print(f"\n[cyan]Analyzing crypto derivatives...[/cyan]")
            
            result = await self.derivatives_analyzer.analyze_crypto_derivatives()
            
            if result.get("success", False):
                console.print(f"\n[bold green]₿ Crypto Derivatives Analysis[/bold green]")
                console.print(f"[cyan]Contracts Analyzed: {result['contracts_analyzed']}/{result['total_contracts']}[/cyan]")
                
                for future in result["futures_data"]:
                    if future.get("success", False):
                        name = future["name"]
                        underlying = future["underlying"]
                        current_price = future["current_price"]
                        change = future["change"]
                        change_pct = future["change_pct"]
                        volatility = future["volatility"]
                        
                        change_color = "green" if change >= 0 else "red"
                        
                        console.print(f"\n[bold]{underlying}[/bold] - {name}")
                        console.print(f"  Price: ${current_price:>10,.2f} [{change_color}]({change:+,.2f}, {change_pct:+.2f}%)[/{change_color}]")
                        console.print(f"  Volatility: {volatility:>5.1f}% | Contract: {future['contract_size']}")
                    else:
                        console.print(f"\n[dim]{future['name']}: {future.get('error', 'No data')}[/dim]")
                
                console.print(f"\n[dim]Last updated: {result['last_updated']}[/dim]")
                
                # Add AI analysis for crypto derivatives
                console.print(f"\n[cyan]Generating AI market analysis...[/cyan]")
                ai_result = await self.derivatives_analyzer.analyze_futures_with_ai(result, "CRYPTO_DERIVATIVES")
                
                if ai_result.get("success", False):
                    console.print(f"\n[bold yellow]🤖 AI Market Analysis - Crypto Derivatives[/bold yellow]")
                    console.print(f"[white]{ai_result['ai_analysis']}[/white]")
                else:
                    console.print(f"[yellow]AI analysis unavailable: {ai_result.get('error', 'Unknown error')}[/yellow]")
                
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error analyzing crypto derivatives: {e}[/red]")
            logger.error(f"Crypto derivatives analysis error: {e}")
    
    async def _analyze_volatility_surface(self):
        """Analyze implied volatility surface."""
        try:
            symbol = await questionary.text(
                "Enter symbol for volatility surface analysis (e.g., AAPL, SPY):"
            ).ask_async()
            
            if not symbol:
                return
            
            symbol = symbol.upper().strip()
            
            console.print(f"\n[cyan]Analyzing volatility surface for {symbol}...[/cyan]")
            
            result = await self.derivatives_analyzer.get_volatility_surface(symbol)
            
            if result.get("success", False):
                current_price = result["current_price"]
                console.print(f"\n[bold green]📊 {symbol} Volatility Surface[/bold green]")
                console.print(f"[cyan]Current Price: ${current_price:.2f}[/cyan]")
                
                for surface_data in result["volatility_surface"]:
                    expiry = surface_data["expiry"]
                    days_to_expiry = surface_data["days_to_expiry"]
                    options = surface_data["options"]
                    
                    console.print(f"\n[bold]Expiry: {expiry} ({days_to_expiry} days)[/bold]")
                    
                    # Group by moneyness ranges
                    atm_options = [opt for opt in options if 0.95 <= opt["moneyness"] <= 1.05]
                    otm_calls = [opt for opt in options if opt["moneyness"] > 1.05 and opt["option_type"] == "call"]
                    otm_puts = [opt for opt in options if opt["moneyness"] < 0.95 and opt["option_type"] == "put"]
                    
                    if atm_options:
                        avg_atm_iv = sum(opt["implied_vol"] for opt in atm_options) / len(atm_options)
                        console.print(f"  ATM IV: {avg_atm_iv:.1%}")
                    
                    if otm_calls:
                        avg_otm_call_iv = sum(opt["implied_vol"] for opt in otm_calls[:3]) / min(3, len(otm_calls))
                        console.print(f"  OTM Calls IV: {avg_otm_call_iv:.1%}")
                    
                    if otm_puts:
                        avg_otm_put_iv = sum(opt["implied_vol"] for opt in otm_puts[:3]) / min(3, len(otm_puts))
                        console.print(f"  OTM Puts IV: {avg_otm_put_iv:.1%}")
                
                console.print(f"\n[dim]Last updated: {result['last_updated']}[/dim]")
                
                # Add AI analysis for volatility surface
                console.print(f"\n[cyan]Generating AI volatility analysis...[/cyan]")
                ai_result = await self.derivatives_analyzer.analyze_volatility_with_ai(result)
                
                if ai_result.get("success", False):
                    console.print(f"\n[bold yellow]🤖 AI Volatility Analysis for {symbol}[/bold yellow]")
                    console.print(f"[white]{ai_result['ai_analysis']}[/white]")
                else:
                    console.print(f"[yellow]AI analysis unavailable: {ai_result.get('error', 'Unknown error')}[/yellow]")
                
            else:
                console.print(f"[red]Error: {result.get('error', 'Unknown error')}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error analyzing volatility surface: {e}[/red]")
            logger.error(f"Volatility surface analysis error: {e}")


async def main():
    """Main entry point."""
    try:
        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)
        
        # Create and run CLI
        cli = MarketResearcherCLI()
        try:
            await cli.run()
        finally:
            # Ensure cleanup happens even if interrupted
            await cli._cleanup()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]AI Market Research Platform interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
