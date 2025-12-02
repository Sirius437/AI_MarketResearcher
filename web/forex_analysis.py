"""
Forex analysis functionality for MarketResearcher web interface.
"""

import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
from typing import Dict, Any, Optional
from analysis_display_utils import WebAnalysisDisplayUtils


class ForexAnalysis:
    """Forex analysis functionality."""
    
    def __init__(self, api_base_url: str, make_request_func):
        """Initialize forex analysis."""
        self.api_base_url = api_base_url
        self.make_request = make_request_func
    
    def forex_analysis_page(self):
        """Display forex analysis page."""
        st.title("💱 Forex Analysis")
        
        # Popular forex pairs list
        major_pairs = [
            "EURUSD - Euro/US Dollar",
            "GBPUSD - British Pound/US Dollar", 
            "USDJPY - US Dollar/Japanese Yen",
            "USDCHF - US Dollar/Swiss Franc",
            "AUDUSD - Australian Dollar/US Dollar",
            "USDCAD - US Dollar/Canadian Dollar",
            "NZDUSD - New Zealand Dollar/US Dollar"
        ]
        
        minor_pairs = [
            "EURGBP - Euro/British Pound",
            "EURJPY - Euro/Japanese Yen",
            "EURCHF - Euro/Swiss Franc",
            "EURAUD - Euro/Australian Dollar",
            "EURCAD - Euro/Canadian Dollar",
            "GBPJPY - British Pound/Japanese Yen",
            "GBPCHF - British Pound/Swiss Franc",
            "GBPAUD - British Pound/Australian Dollar",
            "GBPCAD - British Pound/Canadian Dollar",
            "AUDJPY - Australian Dollar/Japanese Yen",
            "AUDCHF - Australian Dollar/Swiss Franc",
            "AUDCAD - Australian Dollar/Canadian Dollar",
            "CADJPY - Canadian Dollar/Japanese Yen",
            "CHFJPY - Swiss Franc/Japanese Yen",
            "NZDJPY - New Zealand Dollar/Japanese Yen"
        ]
        
        exotic_pairs = [
            "USDTRY - US Dollar/Turkish Lira",
            "USDZAR - US Dollar/South African Rand",
            "USDMXN - US Dollar/Mexican Peso",
            "USDBRL - US Dollar/Brazilian Real",
            "USDSGD - US Dollar/Singapore Dollar",
            "USDHKD - US Dollar/Hong Kong Dollar",
            "USDNOK - US Dollar/Norwegian Krone",
            "USDSEK - US Dollar/Swedish Krona",
            "USDPLN - US Dollar/Polish Zloty",
            "EURPLN - Euro/Polish Zloty",
            "EURTRY - Euro/Turkish Lira",
            "GBPTRY - British Pound/Turkish Lira"
        ]
        
        # Forex selection method
        selection_method = st.selectbox(
            "Choose selection method:",
            ["Major Pairs", "Minor Pairs", "Exotic Pairs", "Enter Custom Pair"],
            key="forex_method"
        )
        
        symbol = None
        
        if selection_method == "Major Pairs":
            selected_pair = st.selectbox(
                "Select Major Forex Pair:",
                major_pairs,
                key="major_pairs_dropdown"
            )
            if selected_pair:
                symbol = selected_pair.split(" - ")[0]
        elif selection_method == "Minor Pairs":
            selected_pair = st.selectbox(
                "Select Minor Forex Pair:",
                minor_pairs,
                key="minor_pairs_dropdown"
            )
            if selected_pair:
                symbol = selected_pair.split(" - ")[0]
        elif selection_method == "Exotic Pairs":
            selected_pair = st.selectbox(
                "Select Exotic Forex Pair:",
                exotic_pairs,
                key="exotic_pairs_dropdown"
            )
            if selected_pair:
                symbol = selected_pair.split(" - ")[0]
        else:
            symbol = st.text_input(
                "Forex Pair Symbol", 
                value="EURUSD", 
                help="Enter forex pair (e.g., EURUSD, GBPJPY)",
                key="forex_input"
            )
        
        broker = st.selectbox("Broker/Data Provider", ["OANDA", "Interactive Brokers", "Forex.com", "XM"])
        
        if symbol and st.button("🔍 Analyze Forex Pair", use_container_width=True, type="primary"):
            with st.spinner("Analyzing forex pair..."):
                analysis_data = {
                    "asset_type": "forex",
                    "symbol": symbol.upper(),
                    "broker": broker
                }
                
                # Check if user is authenticated before making request
                if not st.session_state.get('authenticated') or not st.session_state.get('token'):
                    st.error("Authentication required. Please log in first.")
                    st.stop()
                
                response = requests.post(
                    f"{self.api_base_url}/analysis/forex",
                    json=analysis_data,
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "task_id" in result:
                        task_id = result["task_id"]
                        st.info(f"Analysis started. Task ID: {task_id}")
                        
                        # Poll for results
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for i in range(120):  # 120 second timeout
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
                                        progress_bar.progress(100)
                                        status_text.success("Analysis completed!")
                                        
                                        result = status_data.get("result", {})
                                        self.display_forex_results(result)
                                        break
                                    elif status_data.get("status") == "error":
                                        st.error(f"Analysis failed: {status_data.get('error')}")
                                        break
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
    
    def display_forex_results(self, result: Dict[str, Any]):
        """Display forex analysis results."""
        if not result:
            return
        
        if result.get('error'):
            st.error(f"Analysis failed: {result.get('error')}")
            return
        
        symbol = result.get('symbol', 'N/A')
        pair_name = result.get('pair_name', symbol)
        
        st.subheader(f"💱 {pair_name} ({symbol})")
        
        # Current price info
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Base Currency:** {result.get('base_currency', 'N/A')}")
            st.write(f"**Quote Currency:** {result.get('quote_currency', 'N/A')}")
        with col2:
            spread = result.get('spread', 0)
            if spread > 0:
                st.write(f"**Spread:** {spread:.5f}")
            session = result.get('trading_session', '')
            if session:
                st.write(f"**Trading Session:** {session}")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            current_price = result.get('current_price', 0)
            st.metric("Current Price", f"{current_price:.5f}")
        
        with col2:
            change = result.get('change', 0)
            change_pct = result.get('change_percent', 0)
            st.metric("Daily Change", f"{change:.5f}", f"{change_pct:.3f}%")
        
        with col3:
            high = result.get('high', 0)
            low = result.get('low', 0)
            st.metric("Daily High", f"{high:.5f}")
            st.metric("Daily Low", f"{low:.5f}")
        
        with col4:
            prev_close = result.get('previous_close', 0)
            st.metric("Previous Close", f"{prev_close:.5f}")
        
        # Technical indicators
        technical_indicators = result.get('technical_indicators', {})
        if technical_indicators:
            st.subheader("📊 Technical Indicators")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if 'rsi' in technical_indicators:
                    rsi = technical_indicators['rsi']
                    if rsi > 70:
                        st.error(f"RSI: {rsi:.2f} (Overbought)")
                    elif rsi < 30:
                        st.success(f"RSI: {rsi:.2f} (Oversold)")
                    else:
                        st.info(f"RSI: {rsi:.2f} (Neutral)")
            
            with col2:
                if 'macd' in technical_indicators:
                    macd = technical_indicators['macd']
                    st.metric("MACD", f"{macd:.5f}")
            
            with col3:
                if 'moving_average' in technical_indicators:
                    ma = technical_indicators['moving_average']
                    st.metric("20-day MA", f"{ma:.5f}")
        
        # Economic indicators
        economic_data = result.get('economic_indicators', {})
        if economic_data:
            st.subheader("📈 Economic Indicators")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'interest_rate_diff' in economic_data:
                    rate_diff = economic_data['interest_rate_diff']
                    st.metric("Interest Rate Differential", f"{rate_diff:.3f}%")
                
                if 'inflation_diff' in economic_data:
                    inflation_diff = economic_data['inflation_diff']
                    st.metric("Inflation Differential", f"{inflation_diff:.3f}%")
            
            with col2:
                if 'gdp_growth_diff' in economic_data:
                    gdp_diff = economic_data['gdp_growth_diff']
                    st.metric("GDP Growth Differential", f"{gdp_diff:.3f}%")
                
                if 'unemployment_diff' in economic_data:
                    unemployment_diff = economic_data['unemployment_diff']
                    st.metric("Unemployment Differential", f"{unemployment_diff:.3f}%")
        
        # News count
        news_count = result.get('news_count', 0)
        if news_count > 0:
            st.info(f"📰 {news_count} recent forex news articles analyzed")
        
        # Analysis timestamp
        timestamp = result.get('timestamp', '')
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            st.caption(f"Analysis completed at {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Multi-Agent Analysis Section (if available)
        if result.get('agent_results'):
            # Display main metrics using common utilities
            WebAnalysisDisplayUtils.display_main_metrics(result, asset_type="forex")
            
            # Display agent results using common utilities
            agent_results = result.get('agent_results', {})
            WebAnalysisDisplayUtils.display_agent_results(agent_results)
            
            # Display market context using common utilities
            market_context = result.get('market_context', {})
            WebAnalysisDisplayUtils.display_market_context(market_context, asset_type="forex")
            
            # Display trading parameters if available
            trading_params = result.get('trading_parameters', {})
            WebAnalysisDisplayUtils.display_trading_parameters(trading_params, asset_type="forex")
            
            # Display enhanced analysis if available
            enhanced_analysis = result.get('enhanced_analysis', '')
            WebAnalysisDisplayUtils.display_enhanced_analysis(enhanced_analysis)
            
            # Display price chart if available
            market_data = result.get('market_data', {})
            historical_data = market_data.get('historical_data')
            if historical_data is not None and not historical_data.empty:
                WebAnalysisDisplayUtils.display_price_chart(historical_data, symbol, asset_type="forex")
            
            # Display technical indicators using common utilities
            tech_indicators = market_data.get('technical_indicators', {})
            if tech_indicators:
                WebAnalysisDisplayUtils.display_technical_indicators(tech_indicators, asset_type="forex")
        
        # Legacy AI Analysis Section (fallback for older format)
        ai_analysis = result.get('ai_analysis')
        if ai_analysis and not ai_analysis.get('error'):
            st.subheader("🤖 AI Analysis")
            
            # Investment Signal and Confidence
            col1, col2 = st.columns(2)
            with col1:
                signal = ai_analysis.get('investment_signal', 'NEUTRAL')
                signal_color = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡", "NEUTRAL": "⚪"}.get(signal, "⚪")
                st.metric("Trading Signal", f"{signal_color} {signal}")
            
            with col2:
                confidence = ai_analysis.get('confidence_score', 0)
                st.metric("Confidence Score", f"{confidence:.1f}%")
            
            # Technical Analysis
            technical = ai_analysis.get('technical_analysis', '')
            if technical:
                st.subheader("📊 Technical Analysis")
                st.write(technical)
            
            # Fundamental Analysis
            fundamental = ai_analysis.get('fundamental_analysis', '')
            if fundamental:
                st.subheader("📈 Fundamental Analysis")
                st.write(fundamental)
            
            # Market Sentiment
            sentiment = ai_analysis.get('market_sentiment', '')
            if sentiment:
                st.subheader("📰 Market Sentiment")
                st.write(sentiment)
            
            # Risk Analysis
            risk = ai_analysis.get('risk_analysis', '')
            if risk:
                st.subheader("⚠️ Risk Analysis")
                st.write(risk)
            
            # Trading Strategy
            strategy = ai_analysis.get('trading_strategy', '')
            if strategy:
                st.subheader("💡 Trading Strategy")
                st.write(strategy)
            
            # Final Recommendation
            final_rec = ai_analysis.get('final_recommendation', '')
            if final_rec:
                st.subheader("🎯 Final AI Recommendation")
                st.write(final_rec)
        
        elif ai_analysis and ai_analysis.get('error'):
            st.warning(f"AI Analysis unavailable: {ai_analysis.get('error')}")
        
        if not result.get('mock_data', True):
            st.success("✅ Real forex data analysis completed successfully!")
