"""
Crypto analysis functionality for MarketResearcher web interface.
"""

import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
from typing import Dict, Any, Optional
from analysis_display_utils import WebAnalysisDisplayUtils


class CryptoAnalysis:
    """Crypto analysis functionality."""
    
    def __init__(self, api_base_url: str, make_request_func):
        """Initialize crypto analysis."""
        self.api_base_url = api_base_url
        self.make_request = make_request_func
    
    def crypto_analysis_page(self):
        """Display crypto analysis page."""
        st.title("₿ Cryptocurrency Analysis")
        
        # Popular cryptocurrencies list
        popular_cryptos = [
            "BTCUSDT - Bitcoin",
            "ETHUSDT - Ethereum", 
            "BNBUSDT - Binance Coin",
            "ADAUSDT - Cardano",
            "SOLUSDT - Solana",
            "XRPUSDT - Ripple",
            "DOTUSDT - Polkadot",
            "DOGEUSDT - Dogecoin",
            "AVAXUSDT - Avalanche",
            "SHIBUSDT - Shiba Inu",
            "MATICUSDT - Polygon",
            "LTCUSDT - Litecoin",
            "UNIUSDT - Uniswap",
            "LINKUSDT - Chainlink",
            "ATOMUSDT - Cosmos",
            "VETUSDT - VeChain",
            "FILUSDT - Filecoin",
            "TRXUSDT - TRON",
            "ETCUSDT - Ethereum Classic",
            "XLMUSDT - Stellar"
        ]
        
        # Crypto selection method
        selection_method = st.selectbox(
            "Choose selection method:",
            ["Popular Cryptocurrencies", "Enter Custom Symbol"],
            key="crypto_method"
        )
        
        symbol = None
        
        if selection_method == "Popular Cryptocurrencies":
            selected_crypto = st.selectbox(
                "Select Cryptocurrency:",
                popular_cryptos,
                key="crypto_dropdown"
            )
            if selected_crypto:
                symbol = selected_crypto.split(" - ")[0]
        else:
            symbol = st.text_input(
                "Crypto Symbol", 
                value="BTCUSDT", 
                help="Enter crypto pair (e.g., BTCUSDT, ETHUSDT)",
                key="crypto_input"
            )
        
        exchange = st.selectbox("Exchange", ["Binance", "Coinbase", "Kraken", "Bybit"])
        
        if symbol and st.button("🔍 Analyze Crypto", use_container_width=True, type="primary"):
            with st.spinner("Analyzing cryptocurrency..."):
                analysis_data = {
                    "asset_type": "crypto",
                    "symbol": symbol.upper(),
                    "exchange": exchange
                }
                
                # Check if user is authenticated before making request
                if not st.session_state.get('authenticated') or not st.session_state.get('token'):
                    st.error("Authentication required. Please log in first.")
                    st.stop()
                
                response = requests.post(
                    f"{self.api_base_url}/analysis/crypto",
                    json=analysis_data,
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "task_id" in result:
                        task_id = result["task_id"]
                        st.info(f"Analysis started. Task ID: {task_id}")
                        
                        # Poll for results with longer timeout
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for i in range(120):  # 120 second timeout to match stock analysis
                            time.sleep(1)
                            progress_bar.progress((i + 1) / 120)
                            
                            try:
                                status_response = requests.get(
                                    f"{self.api_base_url}/analysis/status/{task_id}",
                                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                                )
                                
                                if status_response.status_code == 200:
                                    status_data = status_response.json()
                                    if status_data.get("status") == "completed":
                                        result = status_data.get("result", {})
                                        self.display_crypto_results(result)
                                        break
                                    status_text.text(f"Status: {status_data.get('status', 'unknown')}")
                                else:
                                    st.error(f"Status check failed: {status_response.status_code}")
                                    break
                            except Exception as e:
                                st.error(f"API connection error: {e}")
                                break
                        else:
                            st.error("Analysis timed out after 2 minutes")
                    else:
                        st.error(f"Unexpected response format: {result}")
                else:
                    st.error(f"Analysis failed: {response.status_code}")
    
    def analyze_crypto(self, symbol: str) -> Dict[str, Any]:
        """Analyze cryptocurrency using the crypto analyzer with prediction engine."""
        try:
            # Initialize prediction engine and crypto analyzer
            from prediction.engine import PredictionEngine
            from agents import NewsAgent, TechnicalAgent, TradingAgent
            
            # Create agents with web-mode TradingAgent
            agents = {
                'news': NewsAgent(),
                'technical': TechnicalAgent(),
                'trading': TradingAgent(web_mode=True)  # LLM-free mode for web
            }
            
            # Initialize prediction engine
            prediction_engine = PredictionEngine(agents)
            
            # Get fresh price data from public API
            try:
                # Import the public crypto API
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from data.public_crypto_api import PublicCryptoAPI
                
                # Create a public crypto API client
                public_api = PublicCryptoAPI()
                
                # Get ticker data from public API
                ticker_data = public_api.get_ticker_data(symbol)
                
                # Create enriched data with public API data
                if ticker_data and ticker_data.get('price', 0) > 0:
                    enriched_data = {
                        'current_price': float(ticker_data.get('price', 0)),
                        'price_change': float(ticker_data.get('priceChange', 0)),
                        'price_change_percent': float(ticker_data.get('priceChangePercent', 0)),
                        'volume': float(ticker_data.get('volume', 0)),
                        'ticker': ticker_data
                    }
                    
                    # Use the crypto analyzer with prediction engine and enriched data
                    analyzer = CryptoAnalyzer(prediction_engine=prediction_engine)
                    result = analyzer.analyze_crypto(symbol, enriched_data=enriched_data)
                else:
                    # Fallback to standard analysis without enriched data
                    analyzer = CryptoAnalyzer(prediction_engine=prediction_engine)
                    result = analyzer.analyze_crypto(symbol)
            except Exception as e:
                # Fallback to standard analysis if public API fails
                print(f"Public API error: {e}, falling back to standard analysis")
                analyzer = CryptoAnalyzer(prediction_engine=prediction_engine)
                result = analyzer.analyze_crypto(symbol)
            
            # Add timestamp
            result['timestamp'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error in crypto analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def display_crypto_results(self, result: Dict[str, Any]):
        """Display crypto analysis results using common display utilities."""
        if not result:
            st.error("No analysis results received")
            return
        
        if result.get('error'):
            st.error(f"Analysis failed: {result.get('error')}")
            return
        
        # Get symbol from result
        symbol = result.get('symbol', 'N/A')
        st.subheader(f"Analysis Results for {symbol}")
        
        # Display market context
        market_context = result.get('market_context', {})
        WebAnalysisDisplayUtils.display_market_context(market_context, asset_type="crypto")
        
        # Display main metrics
        WebAnalysisDisplayUtils.display_main_metrics(result, asset_type="crypto")
        
        # Display agent results
        agent_results = result.get('agent_results', {})
        WebAnalysisDisplayUtils.display_agent_results(agent_results)
        
        # Display trading parameters
        trading_params = result.get('trading_parameters', {})
        WebAnalysisDisplayUtils.display_trading_parameters(trading_params, asset_type="crypto")
        
        # Display enhanced analysis
        enhanced_analysis = result.get('enhanced_analysis', '')
        WebAnalysisDisplayUtils.display_enhanced_analysis(enhanced_analysis)
        
        # Display price chart
        market_data = result.get('market_data', {})
        historical_data = market_data.get('historical_data')
        if historical_data is not None and not historical_data.empty:
            WebAnalysisDisplayUtils.display_price_chart(historical_data, symbol, asset_type="crypto")
        
        # Display technical indicators
        technical_indicators = market_data.get('technical_indicators', {})
        WebAnalysisDisplayUtils.display_technical_indicators(technical_indicators, asset_type="crypto")
