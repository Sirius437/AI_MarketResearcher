"""
Common display utilities for web analysis interfaces.
Centralizes agent result formatting and display logic across all analysis types.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, Optional, List
from datetime import datetime
from llm_response_parser import LLMResponseParser


class WebAnalysisDisplayUtils:
    """Centralized display utilities for web analysis interfaces."""
    
    @staticmethod
    def display_main_metrics(result: Dict[str, Any], asset_type: str = None):
        """Display main analysis metrics (decision, confidence, risk) - REMOVED to avoid confusion."""
        # Multi-agent decision display removed due to inconsistency with unified signals
        pass
    
    @staticmethod
    def display_analysis_results(result: Dict[str, Any]):
        """Display comprehensive analysis results including enhanced signals."""
        if not result or not result.get('success'):
            st.error("Analysis failed or no results available")
            return
        
        # Display main metrics
        WebAnalysisDisplayUtils.display_main_metrics(result)
        
        # Display enhanced signal if available
        enhanced_signal = result.get('enhanced_signal')
        if enhanced_signal:
            WebAnalysisDisplayUtils.display_enhanced_signal(enhanced_signal)
        
        # Display market data if available
        market_data = result.get('market_data', {})
        historical_data = market_data.get('historical_data')
        if historical_data is not None and not historical_data.empty:
            symbol = result.get('symbol', 'Unknown')
            WebAnalysisDisplayUtils.display_price_chart(historical_data, symbol, asset_type="stock")
        
        # Display technical indicators if available
        technical_indicators = market_data.get('technical_indicators', {})
        WebAnalysisDisplayUtils.display_technical_indicators(technical_indicators, asset_type="stock")
        
        # Display agent results
        agent_results = result.get('agent_results', {})
        if agent_results:
            WebAnalysisDisplayUtils.display_agent_results(agent_results)
    
    @staticmethod
    def display_enhanced_signal(unified_signal: Dict[str, Any]):
        """Display unified trading signal with algorithmic insights."""
        st.subheader("🎯 Unified Trading Signal")
        
        # Signal overview
        col1, col2, col3 = st.columns(3)
        with col1:
            signal = unified_signal.get('signal', 'HOLD')
            signal_color = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(signal, "⚪")
            st.metric("Trading Signal", f"{signal_color} {signal}")
        
        with col2:
            strength = unified_signal.get('strength', 0)
            st.metric("Signal Strength", f"{strength:.2f}")
        
        with col3:
            confidence = unified_signal.get('confidence', 0)
            # Convert to percentage if it's a decimal (0-1 range)
            if confidence <= 1.0:
                confidence_pct = confidence * 100
            else:
                confidence_pct = confidence
            st.metric("Confidence", f"{confidence_pct:.1f}%")
        
        # Technical indicators from unified signal
        indicators = unified_signal.get('indicators', {})
        if indicators:
            st.subheader("📈 Technical Indicators")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if 'rsi' in indicators:
                    st.metric("RSI", f"{indicators['rsi']:.1f}")
            
            with col2:
                if 'macd' in indicators:
                    st.metric("MACD", f"{indicators['macd']:.4f}")
            
            with col3:
                if 'bb_position' in indicators:
                    st.metric("BB Position", f"{indicators['bb_position']:.2f}")
            
            with col4:
                if 'volume_ratio' in indicators:
                    st.metric("Volume Ratio", f"{indicators['volume_ratio']:.2f}")
        
        # Algorithmic execution insights (if available from enhanced signal generation)
        execution_insights = unified_signal.get('execution_insights', {})
        if execution_insights:
            st.subheader("⚙️ Execution Insights")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                algo = execution_insights.get('recommended_algorithm', 'N/A')
                st.metric("Recommended Algorithm", algo)
            
            with col2:
                exec_time = execution_insights.get('estimated_execution_time', 'N/A')
                st.metric("Est. Execution Time", exec_time)
            
            with col3:
                impact = execution_insights.get('market_impact_bps', 0)
                st.metric("Market Impact", f"{impact} bps")
            
            # Risk and stealth metrics
            col1, col2 = st.columns(2)
            with col1:
                risk_profile = execution_insights.get('risk_profile', 'N/A')
                st.metric("Risk Profile", risk_profile)
            
            with col2:
                stealth = execution_insights.get('stealth_level', 0)
                st.metric("Stealth Level", f"{stealth}/5")
        
        # Algorithm recommendations (if available)
        algo_recommendations = unified_signal.get('algorithm_recommendations', [])
        if algo_recommendations:
            st.subheader("📊 Algorithm Recommendations")
            
            for i, rec in enumerate(algo_recommendations[:3]):  # Show top 3
                with st.expander(f"{i+1}. {rec.get('algorithm', 'Unknown')} (Score: {rec.get('score', 0):.2f})"):
                    st.write(f"**Suitability:** {rec.get('suitability_reason', 'N/A')}")
        
        # Market conditions and reasoning
        col1, col2 = st.columns(2)
        with col1:
            market_conditions = unified_signal.get('market_conditions', [])
            if market_conditions:
                st.subheader("🌊 Market Conditions")
                for condition in market_conditions:
                    st.write(f"• {condition}")
        
        with col2:
            reasoning = unified_signal.get('reasoning', '')
            if reasoning:
                st.subheader("💭 Signal Reasoning")
                st.write(reasoning)

    @staticmethod
    def display_market_context(market_context: Dict[str, Any], asset_type: str = "stock"):
        """Display market context with appropriate formatting for asset type."""
        if not market_context:
            return
            
        st.subheader("📊 Market Context")
        
        if asset_type == "crypto":
            # Debug market context data
            print(f"[DEBUG] Crypto market context: {market_context}")
            
            # Try to get fresh price data directly
            try:
                # Import the public crypto API
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from data.public_crypto_api import PublicCryptoAPI
                
                # Get symbol from context or parent result
                symbol = market_context.get('symbol', '')
                if not symbol:
                    parent_result = st.session_state.get('current_analysis_result', {})
                    if parent_result:
                        symbol = parent_result.get('symbol', 'BTCUSDT')
                    else:
                        symbol = 'BTCUSDT'  # Default to BTC if no symbol found
                
                # Get fresh price data
                public_api = PublicCryptoAPI()
                ticker_data = public_api.get_ticker_data(symbol)
                
                if ticker_data and ticker_data.get('price', 0) > 0:
                    # Use fresh data from public API
                    current_price = float(ticker_data.get('price', 0))
                    price_change = float(ticker_data.get('priceChange', 0))
                    price_change_pct = float(ticker_data.get('priceChangePercent', 0))
                    volume = float(ticker_data.get('volume', 0))
                    
                    # Display fresh data
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Current Price", f"${current_price:.2f}")
                    with col2:
                        st.metric("24h Change", f"${price_change:.2f}", delta=f"{price_change_pct:.2f}%")
                    with col3:
                        st.metric("Volume 24h", f"{volume:,.0f}")
                    
                    # Add a note about the data source
                    st.caption("Data from CoinGecko public API")
                    return
            except Exception as e:
                print(f"[DEBUG] Error getting fresh price data: {e}")
            
            # Fallback to existing data if public API fails
            # Check for ticker data in the result
            ticker_data = market_context.get('ticker', {})
            if not ticker_data:
                # Try to get ticker from parent result
                parent_result = st.session_state.get('current_analysis_result', {})
                if parent_result:
                    ticker_data = parent_result.get('market_data', {}).get('ticker', {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                # Get current price with multiple fallbacks
                current_price = market_context.get('current_price', 0)
                if current_price == 0 and ticker_data:
                    current_price = float(ticker_data.get('price', 0))
                
                # Format price
                if current_price > 0:
                    st.metric("Current Price", f"${current_price:.2f}")
                else:
                    st.metric("Current Price", "$0.00")
                    
            with col2:
                # Get price change with multiple fallbacks
                price_change = market_context.get('price_change', 0)
                if price_change == 0 and ticker_data:
                    price_change = float(ticker_data.get('priceChange', 0))
                    
                price_change_pct = market_context.get('price_change_percent', 0)
                if price_change_pct == 0 and ticker_data:
                    price_change_pct = float(ticker_data.get('priceChangePercent', 0))
                
                # Format price change
                if price_change != 0:
                    st.metric("24h Change", f"${price_change:.2f}", delta=f"{price_change_pct:.2f}%")
                else:
                    st.metric("24h Change", "$0.00", delta="0.00%")
                    
            with col3:
                # Get volume with multiple fallbacks
                volume = market_context.get('volume', 0)
                if volume == 0 and ticker_data:
                    volume = float(ticker_data.get('volume', 0))
                    if volume == 0:
                        volume = float(ticker_data.get('quoteVolume', 0))
                
                # Format volume
                st.metric("Volume 24h", f"{volume:,.0f}")
                
        elif asset_type == "forex":
            col1, col2, col3 = st.columns(3)
            with col1:
                current_price = market_context.get('current_price', 0)
                st.metric("Current Price", f"{current_price:.5f}")
            with col2:
                price_change = market_context.get('price_change', 0)
                price_change_pct = market_context.get('price_change_percent', 0)
                st.metric("Daily Change", f"{price_change:.5f}", delta=f"{price_change_pct:.3f}%")
            with col3:
                spread = market_context.get('spread', 0)
                st.metric("Spread", f"{spread:.5f}")
                
        else:  # stock, bonds, commodities
            col1, col2, col3 = st.columns(3)
            with col1:
                current_price = market_context.get('current_price', 0)
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                from currency_utils import format_currency
                symbol = market_context.get('symbol', '')
                st.metric("Current Price", format_currency(current_price, symbol))
            with col2:
                price_change = market_context.get('price_change', 0)
                price_change_pct = market_context.get('price_change_percent', 0)
                st.metric("Price Change", format_currency(price_change, symbol), delta=f"{price_change_pct:.2f}%")
            with col3:
                volume = market_context.get('volume', 0)
                if volume > 0:
                    st.metric("Volume", f"{volume:,.0f}")
    
    @staticmethod
    def _display_investment_commentary_details(analysis: Dict[str, Any]):
        """Display investment commentary details."""
        content = analysis.get('content', analysis.get('raw_analysis', ''))
        
        # Display the content directly using st.write which handles markdown better
        if content:
            # First display any title or header that might be at the beginning
            lines = content.split('\n')
            if lines and lines[0].startswith('#'):
                st.markdown(lines[0])
                content = '\n'.join(lines[1:])
            
            # Display the rest of the content
            st.write(content)
    
    @staticmethod
    def display_agent_results(agent_results: Dict[str, Any]):
        """Display multi-agent analysis results with deduplication."""
        if not agent_results:
            return
            
        st.subheader("🔍 Agent Analysis Breakdown")
        
        # Group agents by type and display only the first occurrence of each type
        agent_types_seen = set()
        
        # Display each unique agent type only once
        for agent_name, analysis in agent_results.items():
            if isinstance(analysis, dict) and analysis.get('success'):
                # Determine agent type from name
                agent_type = agent_name.lower().replace('_agent', '').replace('agent', '').strip()
                
                # Special handling for Investment Commentary
                if agent_name == 'investment_commentary':
                    agent_type = 'investment_commentary'
                # Regular agent type detection
                elif 'technical' in agent_type:
                    agent_type = 'technical'
                elif 'trading' in agent_type:
                    agent_type = 'trading'
                elif 'sentiment' in agent_type:
                    agent_type = 'sentiment'
                elif 'news' in agent_type:
                    agent_type = 'news'
                elif 'risk' in agent_type:
                    agent_type = 'risk'
                
                # Only display if we haven't seen this agent type yet
                if agent_type not in agent_types_seen:
                    agent_types_seen.add(agent_type)
                    
                    # Display agent header with special case for Investment Commentary
                    if agent_type == 'investment_commentary':
                        st.markdown("---")
                        st.markdown("## 📊 Investment Commentary")
                    else:
                        st.subheader(f"{agent_type.title()} Agent Analysis")
                    
                    # Use normal display for all agents
                    WebAnalysisDisplayUtils._display_agent_content(agent_name, analysis)
    
    @staticmethod
    def display_llm_agent_results(llm_responses: List[Dict[str, Any]], symbol: str):
        """
        Display LLM agent results by parsing raw responses first.
        
        Args:
            llm_responses: List of raw LLM response objects
            symbol: Trading symbol for the analysis
        """
        if not llm_responses:
            st.warning("No LLM responses to display")
            return
        
        try:
            # Parse LLM responses into structured format
            agent_results = LLMResponseParser.parse_agent_responses(llm_responses, symbol)
            
            # Display using existing agent results method
            WebAnalysisDisplayUtils.display_agent_results(agent_results)
            
        except Exception as e:
            st.error(f"Error parsing LLM responses: {e}")
            # Fallback to raw display if parsing fails
            st.subheader("🔍 Raw Agent Analysis")
            for i, response in enumerate(llm_responses):
                agent_names = ["Technical", "Trading", "Sentiment", "News", "Risk"]
                agent_name = agent_names[i] if i < len(agent_names) else f"Agent {i+1}"
                
                st.subheader(f"{agent_name} Agent Analysis")
                content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
                if content:
                    st.markdown(content)
                else:
                    st.write("No content available")
    
    @staticmethod
    def _display_agent_content(agent_name: str, analysis: Dict[str, Any]):
        """Display agent content based on agent type and actual data structure."""
        
        # Display basic metrics first
        col1, col2 = st.columns(2)
        with col1:
            if 'symbol' in analysis:
                st.write(f"**Symbol:** {analysis['symbol']}")
            if 'confidence' in analysis:
                confidence = analysis['confidence']
                if confidence <= 1.0:
                    st.write(f"**Confidence:** {confidence*100:.1f}%")
                else:
                    st.write(f"**Confidence:** {confidence:.1f}%")
        
        with col2:
            if 'score' in analysis:
                st.write(f"**Score:** {analysis['score']}")
            if 'action' in analysis:
                st.write(f"**Action:** {analysis['action']}")
        
        # Display analysis text for all agents except trading
        if 'trading' not in agent_name.lower():
            analysis_text = analysis.get('analysis', analysis.get('summary', ''))
            if analysis_text and len(analysis_text.strip()) > 3:
                st.markdown("**Analysis:**")
                st.markdown(analysis_text)
        
        # Handle agent-specific structures
        if 'trading' in agent_name.lower():
            WebAnalysisDisplayUtils._display_trading_agent_details(analysis)
        elif 'sentiment' in agent_name.lower():
            WebAnalysisDisplayUtils._display_sentiment_agent_details(analysis)
        elif 'news' in agent_name.lower():
            WebAnalysisDisplayUtils._display_news_agent_details(analysis)
        elif 'risk' in agent_name.lower():
            WebAnalysisDisplayUtils._display_risk_agent_details(analysis)
        elif 'investment_commentary' in agent_name.lower():
            WebAnalysisDisplayUtils._display_investment_commentary_details(analysis)
            
    
    @staticmethod
    def _display_trading_agent_details(analysis: Dict[str, Any]):
        """Display unified signal data from simplified TradingAgent."""
        # Get unified signal data
        unified_signal = analysis.get('unified_signal', {})
        
        if unified_signal:
            # Display signal recommendation
            signal = unified_signal.get('signal', 'HOLD')
            strength = unified_signal.get('strength', 0)
            confidence = unified_signal.get('confidence', 0)
            
            st.markdown("**📊 Unified Trading Signal:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Signal", signal)
            with col2:
                st.metric("Strength", f"{strength:.2f}")
            with col3:
                # Convert to percentage if it's a decimal (0-1 range)
                if confidence <= 1.0:
                    confidence_pct = confidence * 100
                else:
                    confidence_pct = confidence
                st.metric("Confidence", f"{confidence_pct:.1f}%")
            
            # Display position management parameters
            st.markdown("**💰 Position Management:**")
            
            # Entry range
            entry_range = unified_signal.get('entry_range', {})
            if entry_range:
                col1, col2, col3 = st.columns(3)
                with col1:
                    min_price = entry_range.get('min_price', 0)
                    st.metric("Entry Min", f"${min_price:.4f}")
                with col2:
                    optimal_price = entry_range.get('optimal_price', 0)
                    st.metric("Entry Optimal", f"${optimal_price:.4f}")
                with col3:
                    max_price = entry_range.get('max_price', 0)
                    st.metric("Entry Max", f"${max_price:.4f}")
            
            # Profit target and stop loss
            col1, col2 = st.columns(2)
            with col1:
                profit_target = unified_signal.get('profit_target', 0)
                st.metric("Profit Target", f"${profit_target:.4f}")
            with col2:
                stop_loss = unified_signal.get('stop_loss', 0)
                st.metric("Stop Loss", f"${stop_loss:.4f}")
            
            # Trailing stop parameters
            col1, col2, col3 = st.columns(3)
            with col1:
                trailing_activation = unified_signal.get('trailing_stop_activation', 0)
                st.metric("Trailing Activation", f"${trailing_activation:.4f}")
            with col2:
                trailing_distance = unified_signal.get('trailing_stop_distance', 0)
                st.metric("Trailing Distance", f"{trailing_distance:.1f}%")
            with col3:
                position_size = unified_signal.get('position_size_pct', 0)
                st.metric("Position Size", f"{position_size:.1f}%")
                        
        else:
            st.write("No unified signal data available")
    
    @staticmethod
    def _display_sentiment_agent_details(analysis: Dict[str, Any]):
        """Display sentiment agent specific details."""
        sentiment_signals = analysis.get('sentiment_signals', {})
        if isinstance(sentiment_signals, dict) and sentiment_signals:
            st.markdown("**📊 Sentiment Signals:**")
            for key, value in sentiment_signals.items():
                if value is not None:
                    display_key = key.replace('_', ' ').title()
                    st.write(f"{display_key}: {str(value).replace('_', ' ').title()}")
        
        # Sentiment score
        sentiment_score = analysis.get('sentiment_score', 0)
        if sentiment_score > 0:
            st.write(f"**Sentiment Score:** {sentiment_score}/100")
        
        # Recommendation
        recommendation = analysis.get('recommendation', {})
        if isinstance(recommendation, dict) and recommendation:
            st.markdown("**💡 Recommendation:**")
            col1, col2 = st.columns(2)
            with col1:
                if 'action' in recommendation:
                    st.write(f"Action: {recommendation['action'].upper()}")
                if 'strength' in recommendation:
                    st.write(f"Strength: {recommendation['strength'].title()}")
            with col2:
                if 'score' in recommendation:
                    st.write(f"Score: {recommendation['score']}/100")
                if 'confidence' in recommendation:
                    conf = recommendation['confidence']
                    if conf <= 1.0:
                        st.write(f"Confidence: {conf*100:.1f}%")
                    else:
                        st.write(f"Confidence: {conf:.1f}%")
    
    @staticmethod
    def _display_news_agent_details(analysis: Dict[str, Any]):
        """Display news agent specific details."""
        news_signals = analysis.get('news_signals', {})
        if isinstance(news_signals, dict) and news_signals:
            st.markdown("**📰 News Signals:**")
            for key, value in news_signals.items():
                if value is not None:
                    display_key = key.replace('_', ' ').title()
                    st.write(f"{display_key}: {str(value).replace('_', ' ').title()}")
        
        # News score
        news_score = analysis.get('news_score', 0)
        if news_score > 0:
            st.write(f"**News Score:** {news_score}/100")
        
        # Recommendation
        recommendation = analysis.get('recommendation', {})
        if isinstance(recommendation, dict) and recommendation:
            st.markdown("**💡 Recommendation:**")
            col1, col2 = st.columns(2)
            with col1:
                if 'action' in recommendation:
                    st.write(f"Action: {recommendation['action'].upper()}")
                if 'strength' in recommendation:
                    st.write(f"Strength: {recommendation['strength'].title()}")
            with col2:
                if 'score' in recommendation:
                    st.write(f"Score: {recommendation['score']}/100")
                if 'confidence' in recommendation:
                    conf = recommendation['confidence']
                    if conf <= 1.0:
                        st.write(f"Confidence: {conf*100:.1f}%")
                    else:
                        st.write(f"Confidence: {conf:.1f}%")
    
    @staticmethod
    def _display_risk_agent_details(analysis: Dict[str, Any]):
        """Display risk agent specific details."""
        risk_signals = analysis.get('risk_signals', {})
        if isinstance(risk_signals, dict) and risk_signals:
            st.markdown("**⚠️ Risk Signals:**")
            for key, value in risk_signals.items():
                if value is not None:
                    display_key = key.replace('_', ' ').title()
                    if isinstance(value, bool):
                        st.write(f"{display_key}: {'Yes' if value else 'No'}")
                    else:
                        st.write(f"{display_key}: {str(value).replace('_', ' ').title()}")
        
        # Risk score
        risk_score = analysis.get('risk_score', 0)
        if risk_score > 0:
            st.write(f"**Risk Score:** {risk_score}/100")
        
        # Recommendation
        recommendation = analysis.get('recommendation', {})
        if isinstance(recommendation, dict) and recommendation:
            st.markdown("**💡 Recommendation:**")
            col1, col2 = st.columns(2)
            with col1:
                if 'action' in recommendation:
                    st.write(f"Action: {recommendation['action'].upper()}")
                if 'strength' in recommendation:
                    st.write(f"Strength: {recommendation['strength'].title()}")
            with col2:
                if 'score' in recommendation:
                    st.write(f"Score: {recommendation['score']}/100")
                if 'confidence' in recommendation:
                    conf = recommendation['confidence']
                    if conf <= 1.0:
                        st.write(f"Confidence: {conf*100:.1f}%")
                    else:
                        st.write(f"Confidence: {conf:.1f}%")
    
    @staticmethod
    def _display_investment_commentary(analysis: Dict[str, Any]):
        """Display investment commentary section."""
        raw_analysis = analysis.get('raw_analysis', '')
        
        if raw_analysis and 'Investment Commentary' in str(raw_analysis):
            st.markdown("---")
            st.markdown("## 📊 Investment Commentary")
            st.markdown(raw_analysis)
    
    @staticmethod
    def display_trading_parameters(trading_params: Dict[str, Any], asset_type: str = "stock"):
        """Display trading parameters in a structured format."""
        if not trading_params:
            return
            
        st.subheader("📋 Trading Parameters")
        col1, col2 = st.columns(2)
        
        with col1:
            for key, value in list(trading_params.items())[:len(trading_params)//2]:
                if value is not None:
                    display_key = key.replace('_', ' ').title()
                    if 'price' in key.lower():
                        if asset_type == "crypto":
                            st.metric(display_key, f"${value:,.2f}")
                        elif asset_type == "forex":
                            st.metric(display_key, f"{value:.5f}")
                        else:
                            st.metric(display_key, f"${value:.2f}")
                    elif 'ratio' in key.lower():
                        st.metric(display_key, str(value))
                    else:
                        st.metric(display_key, str(value))
        
        with col2:
            for key, value in list(trading_params.items())[len(trading_params)//2:]:
                if value is not None:
                    display_key = key.replace('_', ' ').title()
                    if 'price' in key.lower():
                        if asset_type == "crypto":
                            st.metric(display_key, f"${value:,.2f}")
                        elif asset_type == "forex":
                            st.metric(display_key, f"{value:.5f}")
                        else:
                            st.metric(display_key, f"${value:.2f}")
                    elif 'ratio' in key.lower():
                        st.metric(display_key, str(value))
                    else:
                        st.metric(display_key, str(value))
    
    @staticmethod
    def display_price_chart(historical_data: pd.DataFrame, symbol: str, asset_type: str = "stock"):
        """Display price chart from historical data."""
        try:
            if historical_data is None or historical_data.empty:
                st.info("No historical data available for chart")
                return
            
            # Debug: Show what data we have
            st.write(f"Debug: Historical data shape: {historical_data.shape}")
            st.write(f"Debug: Columns: {list(historical_data.columns)}")
            st.write(f"Debug: First few rows:")
            st.write(historical_data.head())
            
            # Additional debug info
            st.write(f"Debug: Data types: {historical_data.dtypes}")
            st.write(f"Debug: Index type: {type(historical_data.index)}")
            st.write(f"Debug: Index name: {historical_data.index.name}")
            
            st.subheader("📊 Price Chart")
            
            # Reset index to ensure we have a proper datetime index
            if 'timestamp' in historical_data.columns:
                historical_data['datetime'] = pd.to_datetime(historical_data['timestamp'])
            elif historical_data.index.name == 'timestamp' or 'datetime' in str(type(historical_data.index)):
                historical_data = historical_data.reset_index()
                historical_data['datetime'] = historical_data.index
            else:
                historical_data['datetime'] = historical_data.index
            
            # Create candlestick chart if OHLC data available
            if all(col in historical_data.columns for col in ['open', 'high', 'low', 'close']):
                fig = go.Figure(data=go.Candlestick(
                    x=historical_data['datetime'],
                    open=historical_data['open'],
                    high=historical_data['high'],
                    low=historical_data['low'],
                    close=historical_data['close'],
                    name=symbol
                ))
                
                # Set appropriate y-axis title based on asset type
                if asset_type == "crypto":
                    yaxis_title = "Price (USDT)"
                elif asset_type == "forex":
                    yaxis_title = "Exchange Rate"
                else:
                    yaxis_title = "Price ($)"
                
                fig.update_layout(
                    title=f"{symbol} Price Chart",
                    xaxis_title="Time",
                    yaxis_title=yaxis_title,
                    xaxis_rangeslider_visible=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            elif 'close' in historical_data.columns:
                # Simple line chart if only close price available
                fig = px.line(historical_data, x='datetime', y='close', 
                            title=f"{symbol} Price History")
                
                # Set appropriate y-axis title based on asset type
                if asset_type == "crypto":
                    yaxis_title = "Price (USDT)"
                elif asset_type == "forex":
                    yaxis_title = "Exchange Rate"
                else:
                    yaxis_title = "Price ($)"
                    
                fig.update_layout(
                    xaxis_title="Time",
                    yaxis_title=yaxis_title
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Insufficient price data for chart display")
                
        except Exception as e:
            st.error(f"Error displaying chart: {e}")
    
    @staticmethod
    def display_technical_indicators(indicators: Dict[str, Any], asset_type: str = "stock"):
        """Display technical indicators in a structured format."""
        if not indicators:
            return
            
        st.subheader("📈 Technical Indicators")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # RSI
            rsi_key = 'rsi_14' if 'rsi_14' in indicators else 'rsi'
            if rsi_key in indicators:
                rsi = indicators[rsi_key]
                if rsi > 70:
                    st.error(f"RSI: {rsi:.2f} (Overbought)")
                elif rsi < 30:
                    st.success(f"RSI: {rsi:.2f} (Oversold)")
                else:
                    st.info(f"RSI: {rsi:.2f} (Neutral)")
        
        with col2:
            # MACD
            if 'macd' in indicators and 'macd_signal' in indicators:
                macd = indicators['macd']
                macd_signal = indicators['macd_signal']
                trend = "Bullish" if macd > macd_signal else "Bearish"
                
                # Format based on asset type
                if asset_type == "crypto":
                    st.metric("MACD", f"{macd:.6f}", delta=f"{trend}")
                elif asset_type == "forex":
                    st.metric("MACD", f"{macd:.5f}", delta=f"{trend}")
                else:
                    st.metric("MACD", f"{macd:.4f}", delta=f"{trend}")
            elif 'macd' in indicators:
                macd = indicators['macd']
                if asset_type == "crypto":
                    st.metric("MACD", f"{macd:.6f}")
                elif asset_type == "forex":
                    st.metric("MACD", f"{macd:.5f}")
                else:
                    st.metric("MACD", f"{macd:.4f}")
        
        with col3:
            # Bollinger Bands
            bb_key = 'bb_position' if 'bb_position' in indicators else 'bollinger_position'
            if bb_key in indicators:
                bb_pos = indicators[bb_key]
                if bb_pos < 0.2:
                    st.success(f"BB Position: {bb_pos:.2f} (Near Lower)")
                elif bb_pos > 0.8:
                    st.error(f"BB Position: {bb_pos:.2f} (Near Upper)")
                else:
                    st.info(f"BB Position: {bb_pos:.2f} (Middle)")      
            
    @staticmethod
    def display_enhanced_analysis(enhanced_analysis: str):
        """Display enhanced AI analysis text."""
        if not enhanced_analysis:
            return
        
        # Check if this is Investment Market Commentary
        if "Investment Market Commentary" in enhanced_analysis or "Market Assessment" in enhanced_analysis:
            st.subheader("📊 Investment Market Commentary")
        else:
            st.subheader("🤖 AI Trading Strategy")
        
        st.markdown(enhanced_analysis)
