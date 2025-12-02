"""
Derivatives Analysis Web Interface

This module provides a Streamlit web interface for derivatives analysis including:
- Stock Options Analysis
- Index Futures Analysis
- Currency Derivatives
- Interest Rate Derivatives
- Crypto Derivatives
- Volatility Surface Analysis
"""

import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from typing import Dict, Any, Callable
from analysis_display_utils import WebAnalysisDisplayUtils
import plotly.graph_objects as go

class DerivativesAnalysis:
    """Derivatives analysis web interface."""
    
    def __init__(self, api_base_url: str, make_request: Callable):
        """Initialize the derivatives analysis interface."""
        self.api_base_url = api_base_url
        self.make_request = make_request
    
    def derivatives_analysis_page(self):
        """Main derivatives analysis page."""
        st.title("📊 Derivatives Analysis")
        st.markdown("Comprehensive analysis of options, futures, and other derivative instruments")
        
        # Analysis type selection
        analysis_type = st.selectbox(
            "Select Analysis Type:",
            [
                "Stock Options",
                "Index Futures", 
                "Currency Derivatives",
                "Interest Rate Derivatives",
                "Crypto Derivatives",
                "Volatility Surface"
            ]
        )
        
        if analysis_type == "Stock Options":
            self._stock_options_analysis()
        elif analysis_type == "Index Futures":
            self._index_futures_analysis()
        elif analysis_type == "Currency Derivatives":
            self._currency_derivatives_analysis()
        elif analysis_type == "Interest Rate Derivatives":
            self._rates_derivatives_analysis()
        elif analysis_type == "Crypto Derivatives":
            self._crypto_derivatives_analysis()
        elif analysis_type == "Volatility Surface":
            self._volatility_surface_analysis()
    
    def _stock_options_analysis(self):
        """Stock options analysis interface."""
        st.subheader("📈 Stock Options Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            symbol = st.text_input("Stock Symbol:", value="AAPL", placeholder="e.g., AAPL, TSLA, MSFT")
        with col2:
            expiry_filter = st.text_input("Expiry Filter (optional):", placeholder="e.g., 2024-01")
        
        if st.button("Analyze Options", type="primary"):
            if symbol:
                self._run_options_analysis(symbol, expiry_filter)
            else:
                st.error("Please enter a stock symbol")
    
    def _index_futures_analysis(self):
        """Index futures analysis interface."""
        st.subheader("📊 Index Futures Analysis")
        
        category = st.selectbox(
            "Select Futures Category:",
            ["INDEX_FUTURES", "INDEX_OPTIONS"]
        )
        
        if st.button("Analyze Index Futures", type="primary"):
            self._run_futures_analysis(category)
    
    def _currency_derivatives_analysis(self):
        """Currency derivatives analysis interface."""
        st.subheader("💱 Currency Derivatives Analysis")
        
        st.info("Analyzing major currency futures contracts (EUR, GBP, JPY, CAD, AUD, CHF)")
        
        if st.button("Analyze Currency Derivatives", type="primary"):
            self._run_futures_analysis("CURRENCY_DERIVATIVES")
    
    def _rates_derivatives_analysis(self):
        """Interest rate derivatives analysis interface."""
        st.subheader("📈 Interest Rate Derivatives Analysis")
        
        st.info("Analyzing Treasury futures and Eurodollar contracts")
        
        if st.button("Analyze Rate Derivatives", type="primary"):
            self._run_futures_analysis("RATES_DERIVATIVES")
    
    def _crypto_derivatives_analysis(self):
        """Crypto derivatives analysis interface."""
        st.subheader("₿ Crypto Derivatives Analysis")
        
        st.info("Analyzing Bitcoin and Ethereum futures contracts")
        
        if st.button("Analyze Crypto Derivatives", type="primary"):
            self._run_futures_analysis("CRYPTO_DERIVATIVES")
    
    def _volatility_surface_analysis(self):
        """Volatility surface analysis interface."""
        st.subheader("📊 Volatility Surface Analysis")
        
        symbol = st.text_input("Stock Symbol for Vol Surface:", value="SPY", placeholder="e.g., SPY, QQQ, AAPL")
        
        if st.button("Analyze Volatility Surface", type="primary"):
            if symbol:
                self._run_volatility_analysis(symbol)
            else:
                st.error("Please enter a stock symbol")
    
    def _run_options_analysis(self, symbol: str, expiry_filter: str = None):
        """Run stock options analysis."""
        analysis_data = {
            "analysis_type": "stock_options",
            "symbol": symbol.upper(),
            "expiry_filter": expiry_filter if expiry_filter else None
        }
        
        with st.spinner(f"Analyzing options for {symbol.upper()}..."):
            try:
                response = requests.post(
                    f"{self.api_base_url}/analysis/derivatives",
                    json=analysis_data,
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if "task_id" in result:
                        # Handle async task
                        task_id = result["task_id"]
                        st.info(f"Analysis started. Task ID: {task_id}")
                        
                        # Poll for completion
                        progress_bar = st.progress(0)
                        for i in range(120):  # 2 minute timeout
                            time.sleep(1)
                            progress_bar.progress((i + 1) / 120)
                            
                            status_response = requests.get(
                                f"{self.api_base_url}/analysis/status/{task_id}",
                                headers={"Authorization": f"Bearer {st.session_state.token}"}
                            )
                            
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                if status_data.get("status") == "completed":
                                    progress_bar.progress(100)
                                    result = status_data.get("result", {})
                                    self.display_options_results(result)
                                    break
                                elif status_data.get("status") == "error":
                                    st.error(f"Analysis failed: {status_data.get('error')}")
                                    break
                            else:
                                st.error(f"Status check failed: {status_response.status_code}")
                                break
                        else:
                            st.error("Analysis timed out after 2 minutes")
                    else:
                        st.error(f"Unexpected response format: {result}")
                else:
                    st.error(f"Analysis failed: {response.status_code}")
                    
            except Exception as e:
                st.error(f"API connection error: {e}")
    
    def _run_futures_analysis(self, category: str):
        """Run futures analysis."""
        analysis_data = {
            "analysis_type": "futures",
            "category": category
        }
        
        with st.spinner(f"Analyzing {category.replace('_', ' ').lower()}..."):
            try:
                response = requests.post(
                    f"{self.api_base_url}/analysis/derivatives",
                    json=analysis_data,
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if "task_id" in result:
                        # Handle async task
                        task_id = result["task_id"]
                        st.info(f"Analysis started. Task ID: {task_id}")
                        
                        # Poll for completion
                        progress_bar = st.progress(0)
                        for i in range(120):  # 2 minute timeout
                            time.sleep(1)
                            progress_bar.progress((i + 1) / 120)
                            
                            status_response = requests.get(
                                f"{self.api_base_url}/analysis/status/{task_id}",
                                headers={"Authorization": f"Bearer {st.session_state.token}"}
                            )
                            
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                if status_data.get("status") == "completed":
                                    progress_bar.progress(100)
                                    result = status_data.get("result", {})
                                    self.display_futures_results(result)
                                    break
                                elif status_data.get("status") == "error":
                                    st.error(f"Analysis failed: {status_data.get('error')}")
                                    break
                            else:
                                st.error(f"Status check failed: {status_response.status_code}")
                                break
                        else:
                            st.error("Analysis timed out after 2 minutes")
                    else:
                        st.error(f"Unexpected response format: {result}")
                else:
                    st.error(f"Analysis failed: {response.status_code}")
                    
            except Exception as e:
                st.error(f"API connection error: {e}")
    
    def _run_volatility_analysis(self, symbol: str):
        """Run volatility surface analysis."""
        analysis_data = {
            "analysis_type": "volatility_surface",
            "symbol": symbol.upper()
        }
        
        with st.spinner(f"Analyzing volatility surface for {symbol.upper()}..."):
            try:
                response = requests.post(
                    f"{self.api_base_url}/analysis/derivatives",
                    json=analysis_data,
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if "task_id" in result:
                        # Handle async task
                        task_id = result["task_id"]
                        st.info(f"Analysis started. Task ID: {task_id}")
                        
                        # Poll for completion
                        progress_bar = st.progress(0)
                        for i in range(120):  # 2 minute timeout
                            time.sleep(1)
                            progress_bar.progress((i + 1) / 120)
                            
                            status_response = requests.get(
                                f"{self.api_base_url}/analysis/status/{task_id}",
                                headers={"Authorization": f"Bearer {st.session_state.token}"}
                            )
                            
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                if status_data.get("status") == "completed":
                                    progress_bar.progress(100)
                                    result = status_data.get("result", {})
                                    self.display_volatility_results(result)
                                    break
                                elif status_data.get("status") == "error":
                                    st.error(f"Analysis failed: {status_data.get('error')}")
                                    break
                            else:
                                st.error(f"Status check failed: {status_response.status_code}")
                                break
                        else:
                            st.error("Analysis timed out after 2 minutes")
                    else:
                        st.error(f"Unexpected response format: {result}")
                else:
                    st.error(f"Analysis failed: {response.status_code}")
                    
            except Exception as e:
                st.error(f"API connection error: {e}")
    
    def display_options_results(self, result: Dict[str, Any]):
        """Display options analysis results."""
        if not result:
            return
        
        if result.get('error'):
            st.error(f"Analysis failed: {result.get('error')}")
            return
        
        symbol = result.get('symbol', 'Unknown')
        current_price = result.get('current_price', 0)
        options_data = result.get('options_data', [])
        
        st.subheader(f"📈 {symbol} Options Analysis")
        
        # Current price and summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Price", f"${current_price:.2f}")
        with col2:
            total_options = len(options_data)
            st.metric("Total Options", total_options)
        with col3:
            call_options = len([opt for opt in options_data if opt['type'] == 'call'])
            put_options = len([opt for opt in options_data if opt['type'] == 'put'])
            st.metric("Call/Put Ratio", f"{call_options}/{put_options}")
        
        # Options data table
        if options_data:
            st.subheader("Options Chain")
            
            # Convert to DataFrame for display
            options_df = []
            for option in options_data:
                greeks = option.get('greeks', {})
                options_df.append({
                    'Type': option['type'].upper(),
                    'Strike': f"${option['strike']:.2f}",
                    'Expiry': option['expiry'],
                    'Last Price': f"${option['last_price']:.2f}",
                    'Bid': f"${option['bid']:.2f}",
                    'Ask': f"${option['ask']:.2f}",
                    'Volume': f"{option['volume']:,}",
                    'Open Interest': f"{option['open_interest']:,}",
                    'IV': f"{option['implied_vol']:.1%}",
                    'Delta': f"{greeks.get('delta', 0):.3f}",
                    'Gamma': f"{greeks.get('gamma', 0):.3f}",
                    'Theta': f"{greeks.get('theta', 0):.3f}",
                    'Vega': f"{greeks.get('vega', 0):.3f}"
                })
            
            df = pd.DataFrame(options_df)
            st.dataframe(df, use_container_width=True)
            
            # Volume chart
            if len(options_df) > 0:
                st.subheader("Volume Analysis")
                
                # Create volume chart by strike
                fig = go.Figure()
                
                calls = [opt for opt in options_data if opt['type'] == 'call']
                puts = [opt for opt in options_data if opt['type'] == 'put']
                
                if calls:
                    fig.add_trace(go.Bar(
                        x=[opt['strike'] for opt in calls],
                        y=[opt['volume'] for opt in calls],
                        name='Calls',
                        marker_color='green'
                    ))
                
                if puts:
                    fig.add_trace(go.Bar(
                        x=[opt['strike'] for opt in puts],
                        y=[-opt['volume'] for opt in puts],  # Negative for puts
                        name='Puts',
                        marker_color='red'
                    ))
                
                fig.update_layout(
                    title="Options Volume by Strike",
                    xaxis_title="Strike Price",
                    yaxis_title="Volume",
                    barmode='relative'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # AI Analysis
        ai_analysis = result.get('ai_analysis')
        if ai_analysis:
            if isinstance(ai_analysis, str):
                st.subheader("🤖 AI Analysis")
                st.write(ai_analysis)
            else:
                st.warning(f"AI Analysis unavailable: {ai_analysis}")
        
        # Timestamp
        timestamp = result.get('timestamp', '')
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            st.caption(f"Analysis completed at {dt.strftime('%Y-%m-%d %H:%M:%S')}")

    def display_futures_results(self, result: Dict[str, Any]):
        """Display futures analysis results."""
        if not result:
            return
        
        if result.get('error'):
            st.error(f"Analysis failed: {result.get('error')}")
            return
        
        category = result.get('category', 'Unknown')
        futures_data = result.get('futures', [])
        
        st.subheader(f"📊 {category.replace('_', ' ').title()} Analysis")
        
        # Summary metrics
        successful_futures = [f for f in futures_data if f.get('success', False)]
        
        if successful_futures:
            col1, col2, col3 = st.columns(3)
            with col1:
                # Filter out None values for change_pct calculation
                valid_changes = [f['change_pct'] for f in successful_futures if f.get('change_pct') is not None]
                avg_change = sum(valid_changes) / len(valid_changes) if valid_changes else 0
                st.metric("Average Change", f"{avg_change:+.2f}%")
            with col2:
                # Filter out None values for volatility calculation
                valid_volatilities = [f['volatility'] for f in successful_futures if f.get('volatility') is not None]
                avg_volatility = sum(valid_volatilities) / len(valid_volatilities) if valid_volatilities else 0
                st.metric("Average Volatility", f"{avg_volatility:.1f}%")
            with col3:
                st.metric("Contracts Analyzed", f"{len(successful_futures)}/{len(futures_data)}")
            
            # Futures data table
            st.subheader("Futures Contracts")
            futures_df = []
            for future in successful_futures:
                futures_df.append({
                    'Name': future.get('name', 'N/A'),
                    'Symbol': getattr(future.get('derivative_info'), 'symbol', 'N/A') if future.get('derivative_info') else 'N/A',
                    'Current Price': f"{future['current_price']:.2f}" if future.get('current_price') is not None else 'N/A',
                    'Change': f"{future['change']:+.2f}" if future.get('change') is not None else 'N/A',
                    'Change %': f"{future['change_pct']:+.2f}%" if future.get('change_pct') is not None else 'N/A',
                    'Volume': f"{future['volume']:,.0f}" if future.get('volume') is not None else 'N/A',
                    'Volatility': f"{future['volatility']:.1f}%" if future.get('volatility') is not None else 'N/A',
                    'Contract Size': future.get('contract_size', 'N/A'),
                    'Underlying': future.get('underlying', 'N/A')
                })
            
            df = pd.DataFrame(futures_df)
            st.dataframe(df, use_container_width=True)
            
            # Performance chart
            if len(futures_df) > 0:
                st.subheader("Performance Overview")
                
                import plotly.graph_objects as go
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=[f['name'] for f in successful_futures],
                    y=[f['change_pct'] for f in successful_futures],
                    name='Change %',
                    marker_color=['green' if x >= 0 else 'red' for x in [f['change_pct'] for f in successful_futures]]
                ))
                
                fig.update_layout(
                    title="Futures Performance",
                    xaxis_title="Contract",
                    yaxis_title="Change %",
                    xaxis_tickangle=-45
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # AI Analysis
        ai_analysis = result.get('ai_analysis')
        if ai_analysis:
            if isinstance(ai_analysis, str):
                st.subheader("🤖 AI Analysis")
                st.write(ai_analysis)
            else:
                st.warning(f"AI Analysis unavailable: {ai_analysis}")
        
        # Timestamp
        timestamp = result.get('timestamp', '')
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            st.caption(f"Analysis completed at {dt.strftime('%Y-%m-%d %H:%M:%S')}")

    def display_volatility_results(self, result: Dict[str, Any]):
        """Display volatility surface analysis results."""
        if not result:
            return
        
        if result.get('error'):
            st.error(f"Analysis failed: {result.get('error')}")
            return
        
        symbol = result.get('symbol', 'Unknown')
        current_price = result.get('current_price', 0)
        vol_surface = result.get('volatility_surface', [])
        
        st.subheader(f"📊 {symbol} Volatility Surface")
        
        # Current price
        st.metric("Current Price", f"${current_price:.2f}")
        
        # Volatility surface data
        if vol_surface:
            st.subheader("Volatility Surface Data")
            
            # Create volatility surface visualization
            expiries = []
            strikes = []
            ivs = []
            
            for surface_data in vol_surface:
                expiry = surface_data['expiry']
                for option in surface_data['options']:
                    expiries.append(expiry)
                    strikes.append(option['strike'])
                    ivs.append(option['implied_vol'])
            
            if expiries and strikes and ivs:
                # Create 3D surface plot
                fig = go.Figure(data=[go.Scatter3d(
                    x=expiries,
                    y=strikes,
                    z=ivs,
                    mode='markers',
                    marker=dict(
                        size=5,
                        color=ivs,
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title="Implied Volatility")
                    )
                )])
                
                fig.update_layout(
                    title="Implied Volatility Surface",
                    scene=dict(
                        xaxis_title="Expiry",
                        yaxis_title="Strike Price",
                        zaxis_title="Implied Volatility"
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Summary table
                vol_summary = []
                for surface_data in vol_surface:
                    expiry = surface_data['expiry']
                    days_to_expiry = surface_data['days_to_expiry']
                    options = surface_data['options']
                    
                    avg_iv = sum(opt['implied_vol'] for opt in options) / len(options) if options else 0
                    
                    vol_summary.append({
                        'Expiry': expiry,
                        'Days to Expiry': days_to_expiry,
                        'Options Count': len(options),
                        'Average IV': f"{avg_iv:.1%}"
                    })
                
                df = pd.DataFrame(vol_summary)
                st.dataframe(df, use_container_width=True)
        
        # AI Analysis
        ai_analysis = result.get('ai_analysis')
        if ai_analysis:
            if isinstance(ai_analysis, str):
                st.subheader("🤖 AI Analysis")
                st.write(ai_analysis)
            else:
                st.warning(f"AI Analysis unavailable: {ai_analysis}")
        
        # Timestamp
        timestamp = result.get('timestamp', '')
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            st.caption(f"Analysis completed at {dt.strftime('%Y-%m-%d %H:%M:%S')}")

def derivatives_analysis_page():
    """Standalone derivatives analysis page function."""
    # Get API headers with authentication token
    if 'auth_token' not in st.session_state:
        st.error("Please log in to access derivatives analysis.")
        st.stop()
    
    def get_api_headers():
        return {
            'Authorization': f'Bearer {st.session_state.auth_token}',
            'Content-Type': 'application/json'
        }
    
    def make_request(endpoint: str, method: str = "GET", data: dict = None):
        """Make API request with authentication."""
        try:
            headers = get_api_headers()
            url = f"http://your-domain.com:8000{endpoint}"  # Update with your server domain
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                return {"error": f"Unsupported method: {method}"}
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    # Create derivatives analysis instance and run the page
    derivatives_analyzer = DerivativesAnalysis("http://your-domain.com:8000", make_request)  # Update with your server domain
    derivatives_analyzer.derivatives_analysis_page()  
