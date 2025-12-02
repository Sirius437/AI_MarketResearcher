"""
Commodity Futures Analysis Web Interface for MarketResearcher.
Provides Streamlit components for commodity futures analysis and visualization.
"""

import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime, timedelta
import logging
import plotly.graph_objects as go
from analysis_display_utils import WebAnalysisDisplayUtils

logger = logging.getLogger(__name__)

class CommodityFuturesAnalysis:
    """Commodity futures analysis functionality."""
    
    def __init__(self, api_base_url: str, make_request_func):
        """Initialize commodity futures analysis."""
        self.api_base_url = api_base_url
        self.make_request = make_request_func
    
    def commodity_futures_analysis_page(self):
        """Main commodity futures analysis page."""
        return commodity_futures_analysis_page()

# Commodity categories and symbols
COMMODITY_CATEGORIES = {
    "Energy": {
        "Crude Oil (WTI)": "CL=F",
        "Brent Crude": "BZ=F", 
        "Natural Gas": "NG=F",
        "Heating Oil": "HO=F",
        "Gasoline": "RB=F"
    },
    "Precious Metals": {
        "Gold": "GC=F",
        "Silver": "SI=F",
        "Platinum": "PL=F",
        "Palladium": "PA=F"
    },
    "Base Metals": {
        "Copper": "HG=F",
        "Aluminum": "ALI=F"
    },
    "Agricultural": {
        "Corn": "C=F",
        "Wheat": "W=F",
        "Soybeans": "S=F",
        "Sugar": "SB=F",
        "Coffee": "KC=F",
        "Cotton": "CT=F",
        "Live Cattle": "LC=F",
        "Lean Hogs": "LH=F"
    },
    "Soft Commodities": {
        "Cocoa": "CC=F",
        "Orange Juice": "OJ=F",
        "Lumber": "LB=F"
    }
}

def get_api_headers():
    """Get API headers with authentication token."""
    # Check for different possible token keys in session state
    token = None
    if 'auth_token' in st.session_state:
        token = st.session_state.auth_token
    elif 'token' in st.session_state:
        token = st.session_state.token
    elif st.session_state.get('authenticated'):
        # Use dev token for authenticated sessions
        token = "dev_token"
    
    if not token:
        st.error("Please log in to access commodity futures analysis.")
        st.stop()
    
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

def start_commodity_analysis(symbol: str, category: str):
    """Start commodity futures analysis via API."""
    try:
        headers = get_api_headers()
        
        payload = {
            "symbol": symbol,
            "category": category,
            "analysis_type": "commodity_futures"
        }
        
        response = requests.post(
            "http://localhost:8000/analysis/commodity-futures",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error starting analysis: {str(e)}")
        return None

def poll_analysis_result(task_id: str):
    """Poll for analysis results."""
    try:
        headers = get_api_headers()
        
        response = requests.get(
            f"http://localhost:8000/analysis/status/{task_id}",
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        return {"status": "error", "error": str(e)}

def display_commodity_data(data: dict):
    """Display commodity market data."""
    if not data:
        return
    
    st.subheader("📊 Market Data")
    
    # Current price info
    current_price = data.get('current_price', 0)
    price_change = data.get('price_change', 0)
    price_change_pct = data.get('price_change_pct', 0)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Current Price",
            f"${current_price:.2f}",
            f"{price_change:+.2f} ({price_change_pct:+.2f}%)"
        )
    
    with col2:
        volume = data.get('volume', 0)
        st.metric("Volume", f"{volume:,}")
    
    with col3:
        open_interest = data.get('open_interest', 0)
        st.metric("Open Interest", f"{open_interest:,}")
    
    # Price chart
    historical_data = data.get('historical_data', [])
    if historical_data:
        st.subheader("📈 Price Chart")
        
        df = pd.DataFrame(historical_data)
        if not df.empty and 't' in df.columns:
            df['date'] = pd.to_datetime(df['t'], unit='ms')
            df = df.sort_values('date')
            
            fig = go.Figure()
            
            # Candlestick chart
            fig.add_trace(go.Candlestick(
                x=df['date'],
                open=df.get('o', df.get('open', 0)),
                high=df.get('h', df.get('high', 0)),
                low=df.get('l', df.get('low', 0)),
                close=df.get('c', df.get('close', 0)),
                name="Price"
            ))
            
            fig.update_layout(
                title=f"{data.get('name', 'Commodity')} Price Chart",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Market statistics
    if 'statistics' in data:
        stats = data['statistics']
        st.subheader("📊 Market Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Price Levels:**")
            st.write(f"• 52-Week High: ${stats.get('week_52_high', 'N/A')}")
            st.write(f"• 52-Week Low: ${stats.get('week_52_low', 'N/A')}")
            avg_volume = stats.get('avg_volume', 'N/A')
            if isinstance(avg_volume, (int, float)):
                st.write(f"• Average Volume: {avg_volume:,}")
            else:
                st.write(f"• Average Volume: {avg_volume}")
        
        with col2:
            st.write("**Volatility:**")
            volatility_30d = stats.get('volatility_30d', 'N/A')
            if isinstance(volatility_30d, (int, float)):
                st.write(f"• 30-Day Volatility: {volatility_30d:.2%}")
            else:
                st.write(f"• 30-Day Volatility: {volatility_30d}")
            st.write(f"• Beta: {stats.get('beta', 'N/A')}")

def display_commodity_news(news: list):
    """Display commodity-related news."""
    if not news:
        return
    
    st.subheader("📰 Recent News")
    
    for article in news[:5]:  # Show top 5 articles
        st.markdown(f"**{article.get('title', 'No Title')}**")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**Source:** {article.get('source', 'Unknown')}")
            st.write(f"**Published:** {article.get('time_published', 'Unknown')}")
            
            summary = article.get('summary', '')
            if summary:
                st.write(f"**Summary:** {summary[:300]}...")
        
        with col2:
            sentiment = article.get('sentiment', 'neutral').title()
            sentiment_color = {
                'Positive': 'green',
                'Negative': 'red',
                'Neutral': 'gray'
            }.get(sentiment, 'gray')
            
            st.markdown(f"**Sentiment:** :{sentiment_color}[{sentiment}]")
            
            if 'url' in article:
                st.markdown(f"[Read More]({article['url']})")

def display_ai_analysis(analysis: dict):
    """Display AI analysis results."""
    if not analysis or not analysis.get('success'):
        st.warning("AI analysis not available")
        return
    
    # Check if this is multi-agent analysis format
    if analysis.get('agent_results'):
        # Use common utilities for multi-agent analysis
        WebAnalysisDisplayUtils.display_main_metrics(analysis, asset_type="commodity")
        
        agent_results = analysis.get('agent_results', {})
        WebAnalysisDisplayUtils.display_agent_results(agent_results)
        
        market_context = analysis.get('market_context', {})
        WebAnalysisDisplayUtils.display_market_context(market_context, asset_type="commodity")
        
        trading_params = analysis.get('trading_parameters', {})
        WebAnalysisDisplayUtils.display_trading_parameters(trading_params, asset_type="commodity")
        
        enhanced_analysis = analysis.get('enhanced_analysis', '')
        WebAnalysisDisplayUtils.display_enhanced_analysis(enhanced_analysis)
        
        market_data = analysis.get('market_data', {})
        historical_data = market_data.get('historical_data')
        if historical_data is not None and not historical_data.empty:
            symbol = analysis.get('symbol', 'Commodity')
            WebAnalysisDisplayUtils.display_price_chart(historical_data, symbol, asset_type="commodity")
        
        technical_indicators = market_data.get('technical_indicators', {})
        WebAnalysisDisplayUtils.display_technical_indicators(technical_indicators, asset_type="commodity")
    else:
        # Legacy format - keep existing display logic
        st.subheader("🤖 AI Analysis")
        
        # Final recommendation
        final_signal = analysis.get('final_signal', 'HOLD')
        confidence = analysis.get('confidence', 0)
        
        signal_color = {
            'BUY': 'green',
            'SELL': 'red', 
            'HOLD': 'orange'
        }.get(final_signal, 'gray')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Final Recommendation:** :{signal_color}[{final_signal}]")
        
        with col2:
            st.metric("Confidence", f"{confidence:.1f}%")
        
        # Agent analyses
        agents_analysis = analysis.get('agents_analysis', {})
        
        if 'technical' in agents_analysis and 'error' not in agents_analysis['technical']:
            st.subheader("📊 Technical Analysis")
            tech_analysis = agents_analysis['technical']
            st.write(tech_analysis.get('analysis', 'No technical analysis available'))
            
            if 'signal' in tech_analysis:
                st.write(f"**Signal:** {tech_analysis['signal'].upper()}")
        
        if 'fundamental' in agents_analysis and 'error' not in agents_analysis['fundamental']:
            st.subheader("🌍 Fundamental Analysis")
            fund_analysis = agents_analysis['fundamental']
            st.write(fund_analysis.get('analysis', 'No fundamental analysis available'))
            
            if 'signal' in fund_analysis:
                st.write(f"**Signal:** {fund_analysis['signal'].upper()}")
        
        if 'risk' in agents_analysis and 'error' not in agents_analysis['risk']:
            st.subheader("⚠️ Risk Analysis")
            risk_analysis = agents_analysis['risk']
            st.write(risk_analysis.get('analysis', 'No risk analysis available'))
            
            if 'risk_level' in risk_analysis:
                st.write(f"**Risk Level:** {risk_analysis['risk_level'].title()}")
        
        # Final recommendation details
        final_rec = analysis.get('final_recommendation', '')
        if final_rec:
            st.subheader("🎯 Detailed Recommendation")
            st.write(final_rec)

def commodity_futures_analysis_page():
    """Main commodity futures analysis page."""
    st.title("🌾 Commodity Futures Analysis")
    st.write("Analyze commodity futures contracts with AI-powered insights")
    
    # Commodity selection
    st.subheader("Select Commodity")
    
    # Category selection
    category = st.selectbox(
        "Choose commodity category:",
        options=list(COMMODITY_CATEGORIES.keys()),
        index=0
    )
    
    # Commodity selection within category
    commodities = COMMODITY_CATEGORIES[category]
    commodity_name = st.selectbox(
        f"Choose {category.lower()} commodity:",
        options=list(commodities.keys()),
        index=0
    )
    
    symbol = commodities[commodity_name]
    
    # Custom symbol option
    st.subheader("🔧 Advanced Options")
    use_custom = st.checkbox("Use custom commodity symbol")
    if use_custom:
        custom_symbol = st.text_input(
            "Enter commodity symbol (e.g., CL=F for Crude Oil):",
            value=symbol
        )
        if custom_symbol:
            symbol = custom_symbol.upper().strip()
            commodity_name = f"Custom ({symbol})"
    
    # Analysis button
    if st.button("🚀 Analyze Commodity", type="primary"):
        if not symbol:
            st.error("Please select or enter a commodity symbol")
            return
        
        # Start analysis
        with st.spinner(f"Starting analysis for {commodity_name} ({symbol})..."):
            result = start_commodity_analysis(symbol, category)
        
        if not result:
            return
        
        if not result.get('success'):
            st.error(f"Failed to start analysis: {result.get('error', 'Unknown error')}")
            return
        
        task_id = result.get('task_id')
        if not task_id:
            st.error("No task ID received from API")
            return
        
        # Poll for results
        progress_bar = st.progress(0)
        status_text = st.empty()
        result_container = st.empty()
        
        max_attempts = 60  # 5 minutes max
        attempt = 0
        
        while attempt < max_attempts:
            status_text.text(f"Analyzing {commodity_name}... ({attempt + 1}/{max_attempts})")
            progress_bar.progress((attempt + 1) / max_attempts)
            
            poll_result = poll_analysis_result(task_id)
            
            if poll_result.get('status') == 'completed':
                progress_bar.progress(1.0)
                status_text.text("✅ Analysis completed!")
                
                # Display results
                analysis_result = poll_result.get('result', {})
                
                if analysis_result.get('success'):
                    with result_container.container():
                        st.success(f"Analysis completed for {commodity_name}")
                        
                        # Display market data
                        display_commodity_data(analysis_result)
                        
                        # Display news
                        news = analysis_result.get('news', [])
                        if news:
                            display_commodity_news(news)
                        
                        # Display AI analysis
                        ai_analysis = analysis_result.get('ai_analysis')
                        if ai_analysis:
                            display_ai_analysis(ai_analysis)
                        
                        # Display raw data
                        st.subheader("🔍 Raw Analysis Data")
                        st.json(analysis_result)
                else:
                    st.error(f"Analysis failed: {analysis_result.get('error', 'Unknown error')}")
                
                break
                
            elif poll_result.get('status') == 'failed':
                st.error(f"Analysis failed: {poll_result.get('error', 'Unknown error')}")
                break
                
            elif poll_result.get('status') == 'error':
                st.error(f"Polling error: {poll_result.get('error', 'Unknown error')}")
                break
            
            time.sleep(5)  # Wait 5 seconds before next poll
            attempt += 1
        
        if attempt >= max_attempts:
            st.error("Analysis timed out. Please try again.")
        
        # Clean up progress indicators
        progress_bar.empty()
        status_text.empty()

if __name__ == "__main__":
    commodity_futures_analysis_page()
