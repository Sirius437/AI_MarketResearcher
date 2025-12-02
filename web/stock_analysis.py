"""
Stock analysis functionality for MarketResearcher web interface.
"""

import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
from typing import Dict, Any, Optional
from analysis_display_utils import WebAnalysisDisplayUtils


class StockAnalysis:
    """Stock analysis functionality."""
    
    def __init__(self, api_base_url: str, make_request_func):
        """Initialize stock analysis."""
        self.api_base_url = api_base_url
        self.make_request = make_request_func
    
    def stock_analysis_page(self):
        """Display stock analysis page."""
        st.title("📈 Stock Analysis")
        
        symbol = None
        
        # Step 1: Region Selection
        region_options = [
            "Select Region...",
            "North America - US, Canada",
            "Europe - UK, Germany, France, Netherlands, Switzerland, Italy", 
            "MENA - Saudi Arabia, UAE, Egypt, South Africa",
            "Asia Pacific - Japan, China, Hong Kong, Taiwan, Singapore, Australia, India, Malaysia, Thailand, Philippines, Indonesia, Vietnam, South Korea, New Zealand",
            "Custom Symbol"
        ]
        
        selected_region = st.selectbox("🌍 Select Region", region_options)
        
        if selected_region == "Custom Symbol":
            symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, TSLA)", placeholder="AAPL")
        elif selected_region != "Select Region...":
            # Step 2: Exchange Selection
            exchange_mapping = {
                "North America - US, Canada": ["NYSE", "NASDAQ", "TSX"],
                "Europe - UK, Germany, France, Netherlands, Switzerland, Italy": ["LSE", "XETRA", "XPAR", "XAMS", "SIX", "MIL"],
                "MENA - Saudi Arabia, UAE, Egypt, South Africa": ["TADAWUL", "DFM", "EGX", "JSE"],
                "Asia Pacific - Japan, China, Hong Kong, Taiwan, Singapore, Australia, India, Malaysia, Thailand, Philippines, Indonesia, Vietnam, South Korea, New Zealand": ["TSE", "SSE", "SZSE", "HKEX", "TWSE", "SGX", "ASX", "BSE", "KLSE", "SET", "PSE", "IDX", "VNX", "KRX", "NZX"]
            }
            
            exchanges = exchange_mapping.get(selected_region, [])
            selected_exchange = st.selectbox("🏛️ Select Exchange", ["Select Exchange..."] + exchanges)
            
            if selected_exchange != "Select Exchange...":
                # Step 3: Selection Method
                selection_method = st.radio(
                    "📊 How would you like to select a stock?",
                    ["Popular Stocks", "Browse by Sector", "Browse All Stocks"]
                )
                
                if selection_method == "Popular Stocks":
                    popular_stocks = self._get_popular_stocks(selected_exchange)
                    if popular_stocks:
                        # Handle both string and dict formats
                        if isinstance(popular_stocks[0], str):
                            stock_options = popular_stocks
                            selected_stock = st.selectbox("⭐ Select Popular Stock", ["Select Stock..."] + stock_options)
                            if selected_stock != "Select Stock...":
                                symbol = selected_stock.split(" - ")[0]
                        else:
                            stock_options = [f"{stock['symbol']} - {stock['name']}" for stock in popular_stocks]
                            selected_stock = st.selectbox("⭐ Select Popular Stock", ["Select Stock..."] + stock_options)
                            if selected_stock != "Select Stock...":
                                symbol = selected_stock.split(" - ")[0]
                    else:
                        st.info("No popular stocks data available for this exchange")
                
                elif selection_method == "Browse by Sector":
                    sectors = self._get_sectors(selected_exchange)
                    if sectors:
                        selected_sector = st.selectbox("🏭 Select Sector", ["Select Sector..."] + sectors)
                        if selected_sector != "Select Sector...":
                            sector_stocks = self._get_sector_stocks(selected_exchange, selected_sector)
                            if sector_stocks:
                                # Handle both string and dict formats
                                if isinstance(sector_stocks[0], str):
                                    stock_options = sector_stocks
                                    selected_stock = st.selectbox("📈 Select Stock", ["Select Stock..."] + stock_options)
                                    if selected_stock != "Select Stock...":
                                        symbol = selected_stock.split(" - ")[0]
                                else:
                                    stock_options = [f"{stock['symbol']} - {stock['name']}" for stock in sector_stocks]
                                    selected_stock = st.selectbox("📈 Select Stock", ["Select Stock..."] + stock_options)
                                    if selected_stock != "Select Stock...":
                                        symbol = selected_stock.split(" - ")[0]
                            else:
                                st.info(f"No stocks found for {selected_sector} sector")
                    else:
                        st.info("No sector data available for this exchange")
                
                elif selection_method == "Browse All Stocks":
                    all_stocks = self._get_all_stocks(selected_exchange)
                    if all_stocks:
                        # Add search functionality for large lists
                        search_term = st.text_input("🔍 Search stocks (optional)", placeholder="Enter company name or symbol")
                        
                        if search_term:
                            # Handle search for both string and dict formats
                            if isinstance(all_stocks[0], str):
                                filtered_stocks = [stock for stock in all_stocks if search_term.lower() in stock.lower()]
                            else:
                                filtered_stocks = [
                                    stock for stock in all_stocks 
                                    if search_term.lower() in stock['name'].lower() or search_term.lower() in stock['symbol'].lower()
                                ]
                        else:
                            filtered_stocks = all_stocks[:1100]  # Limit to first 1100 for performance
                        
                        if filtered_stocks:                                                      
                            # Handle string format (formatted as "SYMBOL - Company Name")
                            if isinstance(filtered_stocks[0], str):
                                stock_options = filtered_stocks
                                selected_stock = st.selectbox("📊 Select Stock", ["Select Stock..."] + stock_options)
                                if selected_stock != "Select Stock...":
                                    # Extract just the symbol from "SYMBOL - Company Name" format
                                    symbol = selected_stock.split(" - ")[0]
                            # Handle dict format
                            else:
                                stock_options = [f"{stock['symbol']} - {stock['name']}" for stock in filtered_stocks]
                                selected_stock = st.selectbox("📊 Select Stock", ["Select Stock..."] + stock_options)
                                if selected_stock != "Select Stock...":
                                    symbol = selected_stock.split(" - ")[0]
                        else:
                            st.info("No stocks found matching your search")
                    else:
                        st.info("No stock data available for this exchange")
        
        # Analysis section
        if symbol:
            if st.button("🔍 Analyze Stock", use_container_width=True, type="primary"):
                with st.spinner("Analyzing stock..."):
                    analysis_data = {
                        "asset_type": "stock",
                        "symbol": symbol.upper()
                    }
                    
                    response = requests.post(
                        f"{self.api_base_url}/analysis/stock",
                        json=analysis_data,
                        headers={"Authorization": f"Bearer {st.session_state.token}"}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result.get("status") == "completed":
                            self.display_stock_results(result)
                        elif "task_id" in result:
                            # Handle async task
                            task_id = result["task_id"]
                            st.info(f"Analysis started. Task ID: {task_id}")
                            
                            # Poll for completion
                            progress_bar = st.progress(0)
                            for i in range(180):  # 180 second timeout
                                time.sleep(1)
                                progress_bar.progress((i + 1) / 180)
                                
                                status_response = requests.get(
                                    f"{self.api_base_url}/analysis/status/{task_id}",
                                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                                )
                                
                                if status_response.status_code == 200:
                                    status_data = status_response.json()
                                    if status_data.get("status") == "completed":
                                        progress_bar.progress(100)
                                        result = status_data.get("result", {})
                                        self.display_stock_results(result)
                                        break
                                    elif status_data.get("status") == "error":
                                        st.error(f"Analysis failed: {status_data.get('error')}")
                                        break
                                else:
                                    st.error(f"Status check failed: {status_response.status_code}")
                                    break
                            else:
                                st.error("Analysis timed out after 3 minutes")
                        else:
                            st.error(f"Unexpected response format: {result}")
                    else:
                        st.error(f"Analysis failed: {response.status_code}")
    
    def display_stock_results(self, result: Dict[str, Any]):
        """Display stock analysis results."""
        if not result:
            return
        
        if result.get('error'):
            st.error(f"Analysis failed: {result.get('error')}")
            return
        
        symbol = result.get('symbol', 'N/A')
        
        # Get company name from stocks database
        company_name = symbol  # Default fallback
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from data.stocks_database import StocksDatabase
            stocks_db = StocksDatabase()
            stock_info = stocks_db.get_stock_by_symbol(symbol)
            if stock_info and stock_info.name:
                company_name = stock_info.name
        except Exception:
            pass
        
        # Use company name from result if available, otherwise use database lookup
        display_name = result.get('company_name', company_name)
        
        st.subheader(f"📈 {display_name} ({symbol})")
        
        # Company info
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Industry:** {result.get('industry', 'N/A')}")
            st.write(f"**Data Source:** {result.get('data_source', 'N/A')}")
        with col2:
            market_cap = result.get('market_cap', 0)
            if market_cap > 0:
                currency = result.get('currency', 'USD')
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                from currency_utils import get_currency_symbol
                currency_symbol = get_currency_symbol(currency)
                st.write(f"**Market Cap:** {currency_symbol}{market_cap:,.0f}M")
            website = result.get('website', '')
            if website:
                st.write(f"**Website:** {website}")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            current_price = result.get('current_price', 0)
            currency = result.get('currency', 'USD')
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from currency_utils import get_currency_symbol
            currency_symbol = get_currency_symbol(currency)
            st.metric("Current Price", f"{currency_symbol}{current_price:.2f}")
        
        with col2:
            change = result.get('change', 0)
            change_pct = result.get('change_percent', 0)
            st.metric("Change", f"{currency_symbol}{change:.2f}", f"{change_pct:.2f}%")
        
        with col3:
            high = result.get('high', 0)
            low = result.get('low', 0)
            st.metric("High / Low", f"{currency_symbol}{high:.2f}", f"{currency_symbol}{low:.2f}")
        
        with col4:
            prev_close = result.get('previous_close', 0)
            st.metric("Previous Close", f"{currency_symbol}{prev_close:.2f}")
        
        # Financial metrics
        st.subheader("📊 Financial Metrics")
        fin_col1, fin_col2, fin_col3 = st.columns(3)
        
        with fin_col1:
            pe_ratio = result.get('pe_ratio', 'N/A')
            pb_ratio = result.get('pb_ratio', 'N/A')
            st.metric("P/E Ratio", f"{pe_ratio:.2f}" if isinstance(pe_ratio, (int, float)) else str(pe_ratio))
            st.metric("P/B Ratio", f"{pb_ratio:.2f}" if isinstance(pb_ratio, (int, float)) else str(pb_ratio))
        
        with fin_col2:
            roa = result.get('roa', 'N/A')
            roe = result.get('roe', 'N/A')
            st.metric("ROA", f"{roa:.2f}%" if isinstance(roa, (int, float)) else str(roa))
            st.metric("ROE", f"{roe:.2f}%" if isinstance(roe, (int, float)) else str(roe))
        
        with fin_col3:
            revenue_growth = result.get('revenue_growth', 'N/A')
            eps = result.get('eps', 'N/A')
            st.metric("Revenue Growth", f"{revenue_growth:.2f}%" if isinstance(revenue_growth, (int, float)) else str(revenue_growth))
            st.metric("EPS", f"{eps:.2f}" if isinstance(eps, (int, float)) else str(eps))
        
        # Analyst recommendations
        recommendations = result.get('analyst_recommendations', {})
        if recommendations:
            st.subheader("🎯 Analyst Recommendations")
            rec_col1, rec_col2, rec_col3, rec_col4, rec_col5 = st.columns(5)
            
            with rec_col1:
                st.metric("Strong Buy", recommendations.get('strongBuy', 0))
            with rec_col2:
                st.metric("Buy", recommendations.get('buy', 0))
            with rec_col3:
                st.metric("Hold", recommendations.get('hold', 0))
            with rec_col4:
                st.metric("Sell", recommendations.get('sell', 0))
            with rec_col5:
                st.metric("Strong Sell", recommendations.get('strongSell', 0))
        
        # News count
        news_count = result.get('news_count', 0)
        if news_count > 0:
            st.info(f"📰 {news_count} recent news articles analyzed")
        
        # Analysis timestamp
        timestamp = result.get('timestamp', '')
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            st.caption(f"Analysis completed at {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Display enhanced trading signal with algorithmic insights
        enhanced_signal = result.get('enhanced_signal')
        if enhanced_signal:
            st.subheader("🤖 Algorithmic Trading Insights")
            
            # Main signal display
            signal_col1, signal_col2, signal_col3 = st.columns(3)
            
            with signal_col1:
                signal = enhanced_signal.get('signal', 'HOLD')
                signal_color = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(signal, "🟡")
                st.metric("Trading Signal", f"{signal_color} {signal}")
                
            with signal_col2:
                strength = enhanced_signal.get('strength', 0.5)
                st.metric("Signal Strength", f"{strength:.2f}")
                
            with signal_col3:
                confidence = enhanced_signal.get('confidence', 0.5)
                st.metric("Confidence", f"{confidence:.2f}")
            
            # Algorithmic execution insights
            if 'recommended_algorithm' in enhanced_signal:
                st.write("**🎯 Recommended Algorithm:**", enhanced_signal['recommended_algorithm'])
                
            # Algorithm recommendations
            if 'algorithm_recommendations' in enhanced_signal:
                st.write("**📊 Algorithm Recommendations:**")
                recommendations = enhanced_signal['algorithm_recommendations']
                
                for i, (algo, score, rating) in enumerate(recommendations[:3], 1):
                    rating_color = {"EXCELLENT": "🟢", "GOOD": "🟡", "FAIR": "🟠", "POOR": "🔴"}.get(rating, "⚪")
                    st.write(f"{i}. **{algo}**: {rating_color} {rating} (Score: {score:.2f})")
            
            # Market conditions
            if 'market_conditions' in enhanced_signal:
                conditions = enhanced_signal['market_conditions']
                st.write(f"**🌊 Market Conditions:** {', '.join(conditions)}")
            
            # Signal reasoning
            if 'reasoning' in enhanced_signal:
                st.write(f"**💭 Analysis:** {enhanced_signal['reasoning']}")
        
        # AI Analysis Section
        ai_analysis = result.get('ai_analysis')
        if ai_analysis and not ai_analysis.get('error'):
            st.subheader("🤖 AI Analysis")
            
            # Investment Signal and Confidence
            col1, col2 = st.columns(2)
            with col1:
                signal = ai_analysis.get('investment_signal', 'NEUTRAL')
                signal_color = {"BUY": "", "SELL": "", "HOLD": "", "NEUTRAL": ""}.get(signal, "")
                st.metric("Investment Signal", f"{signal_color} {signal}")
            with col2:
                confidence = ai_analysis.get('confidence', 0)
                st.metric("Confidence", f"{confidence:.1f}%")
        
        # Use display utils to show analysis results
        WebAnalysisDisplayUtils.display_analysis_results(result)
    
    def _get_popular_stocks(self, exchange_code):
        """Get popular stocks for an exchange."""
        try:
            response = requests.get(f"{self.api_base_url}/stocks/popular/{exchange_code}")
            if response.status_code == 200:
                return response.json().get("stocks", [])
        except:
            pass
        
        # Fallback to predefined popular stocks by exchange
        popular_stocks_by_exchange = {
            "NYSE": ["AAPL - Apple Inc.", "MSFT - Microsoft Corporation", "GOOGL - Alphabet Inc.", "TSLA - Tesla Inc.", "NVDA - NVIDIA Corporation"],
            "NASDAQ": ["AAPL - Apple Inc.", "MSFT - Microsoft Corporation", "AMZN - Amazon.com Inc.", "GOOGL - Alphabet Inc.", "META - Meta Platforms Inc."],
            "TSX": ["SHOP - Shopify Inc.", "CNR - Canadian National Railway", "RY - Royal Bank of Canada", "TD - Toronto-Dominion Bank", "BNS - Bank of Nova Scotia"],
            "LSE": ["SHEL - Shell plc", "AZN - AstraZeneca PLC", "BP - BP p.l.c.", "ULVR - Unilever PLC", "HSBA - HSBC Holdings plc"],
            "XETRA": ["SAP - SAP SE", "ASME - ASML Holding N.V.", "SIE - Siemens AG", "DTE - Deutsche Telekom AG", "ALV - Allianz SE"],
            "XPAR": ["MC - LVMH Moët Hennessy Louis Vuitton", "OR - L'Oréal S.A.", "SAN - Sanofi", "TTE - TotalEnergies SE", "BNP - BNP Paribas"],
            "TSE": ["7203 - Toyota Motor Corporation", "6758 - Sony Group Corporation", "9984 - SoftBank Group Corp.", "6861 - Keyence Corporation", "4519 - Chugai Pharmaceutical Co."],
            "HKEX": ["0700 - Tencent Holdings Limited", "0941 - China Mobile Limited", "1299 - AIA Group Limited", "2318 - Ping An Insurance", "0005 - HSBC Holdings plc"],
            "ASX": ["CBA - Commonwealth Bank of Australia", "BHP - BHP Group Limited", "CSL - CSL Limited", "WBC - Westpac Banking Corporation", "ANZ - Australia and New Zealand Banking Group"]
        }
        
        return popular_stocks_by_exchange.get(exchange_code, [])
    
    def _get_sector_stocks(self, exchange_code, sector):
        """Get stocks for a specific sector in an exchange."""
        try:
            response = requests.get(f"{self.api_base_url}/stocks/sector/{exchange_code}/{sector}")
            if response.status_code == 200:
                return response.json().get("stocks", [])
        except:
            pass
        return []
    
    def _get_sectors(self, exchange_code):
        """Get sectors for an exchange."""
        try:
            response = requests.get(f"{self.api_base_url}/stocks/sectors/{exchange_code}")
            if response.status_code == 200:
                return response.json().get("sectors", [])
        except:
            pass
        
        # Fallback to common sectors
        return ["Technology", "Healthcare", "Financial Services", "Consumer Cyclical", "Communication Services", 
                "Industrials", "Consumer Defensive", "Energy", "Utilities", "Real Estate", "Basic Materials"]
    
    def _get_all_stocks(self, exchange_code):
        """Get all stocks for an exchange."""
        try:
            response = requests.get(f"{self.api_base_url}/stocks/all/{exchange_code}")
            if response.status_code == 200:
                return response.json().get("stocks", [])
        except:
            pass
        return []
