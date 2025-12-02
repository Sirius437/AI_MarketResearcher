"""
Bonds and Gilts analysis functionality for MarketResearcher web interface.
"""

import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
from typing import Dict, Any, Optional
from analysis_display_utils import WebAnalysisDisplayUtils


class BondsAnalysis:
    """Bonds and Gilts analysis functionality."""
    
    def __init__(self, api_base_url: str, make_request_func):
        """Initialize bonds analysis."""
        self.api_base_url = api_base_url
        self.make_request = make_request_func
    
    def bonds_analysis_page(self):
        """Display bonds analysis page."""
        st.title("🏛️ Bonds & Gilts Analysis")
        
        # Analysis type selection
        analysis_type = st.selectbox(
            "Choose Analysis Type:",
            ["Market Bonds", "Yield Curve", "International Comparison", "Bond Trends"],
            key="bonds_analysis_type"
        )
        
        if analysis_type == "Market Bonds":
            self._market_bonds_analysis()
        elif analysis_type == "Yield Curve":
            self._yield_curve_analysis()
        elif analysis_type == "International Comparison":
            self._international_comparison_analysis()
        elif analysis_type == "Bond Trends":
            self._bond_trends_analysis()
    
    def _market_bonds_analysis(self):
        """Market bonds analysis interface."""
        st.subheader("📊 Market Bonds Analysis")
        
        # Market selection
        markets = {
            "US_TREASURY": "US Treasury Bonds",
            "UK_GILTS": "UK Gilts",
            "EUROPEAN": "European Government Bonds",
            "OTHER_MAJOR": "Other Major Markets"
        }
        
        selected_market = st.selectbox(
            "Select Bond Market:",
            list(markets.keys()),
            format_func=lambda x: markets[x],
            key="market_bonds_selection"
        )
        
        period = st.selectbox(
            "Analysis Period:",
            ["1d", "1w", "1mo", "3mo", "6mo", "1y"],
            index=2,
            key="market_bonds_period"
        )
        
        if st.button("🔍 Analyze Market Bonds", use_container_width=True, type="primary"):
            with st.spinner("Analyzing market bonds..."):
                analysis_data = {
                    "analysis_type": "market_bonds",
                    "market": selected_market,
                    "period": period
                }
                
                self._run_bonds_analysis(analysis_data)
    
    def _yield_curve_analysis(self):
        """Yield curve analysis interface."""
        st.subheader("📈 Yield Curve Analysis")
        
        country = st.selectbox(
            "Select Country:",
            ["US", "UK"],
            key="yield_curve_country"
        )
        
        if st.button("🔍 Analyze Yield Curve", use_container_width=True, type="primary"):
            with st.spinner("Analyzing yield curve..."):
                analysis_data = {
                    "analysis_type": "yield_curve",
                    "country": country
                }
                
                self._run_bonds_analysis(analysis_data)
    
    def _international_comparison_analysis(self):
        """International bonds comparison interface."""
        st.subheader("🌍 International Bonds Comparison")
        
        maturity = st.selectbox(
            "Select Maturity:",
            ["2Y", "5Y", "10Y", "30Y"],
            index=2,
            key="international_maturity"
        )
        
        if st.button("🔍 Compare International Bonds", use_container_width=True, type="primary"):
            with st.spinner("Comparing international bonds..."):
                analysis_data = {
                    "analysis_type": "international_comparison",
                    "maturity": maturity
                }
                
                self._run_bonds_analysis(analysis_data)
    
    def _bond_trends_analysis(self):
        """Bond trends analysis interface."""
        st.subheader("📊 Bond Trends Analysis")
        
        markets = {
            "US_TREASURY": "US Treasury Bonds",
            "UK_GILTS": "UK Gilts",
            "EUROPEAN": "European Government Bonds",
            "OTHER_MAJOR": "Other Major Markets"
        }
        
        selected_market = st.selectbox(
            "Select Bond Market:",
            list(markets.keys()),
            format_func=lambda x: markets[x],
            key="trends_market_selection"
        )
        
        period = st.selectbox(
            "Trend Analysis Period:",
            ["1mo", "3mo", "6mo", "1y"],
            index=1,
            key="trends_period"
        )
        
        if st.button("🔍 Analyze Bond Trends", use_container_width=True, type="primary"):
            with st.spinner("Analyzing bond trends..."):
                analysis_data = {
                    "analysis_type": "bond_trends",
                    "market": selected_market,
                    "period": period
                }
                
                self._run_bonds_analysis(analysis_data)
    
    def _run_bonds_analysis(self, analysis_data: Dict[str, Any]):
        """Run bonds analysis and display results."""
        # Check authentication
        if not st.session_state.get('authenticated') or not st.session_state.get('token'):
            st.error("Authentication required. Please log in first.")
            st.stop()
        
        try:
            response = requests.post(
                f"{self.api_base_url}/analysis/bonds",
                json=analysis_data,
                headers={"Authorization": f"Bearer {st.session_state.token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result and "task_id" in result:
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
                                    self.display_bonds_results(result)
                                    break
                                elif status_data.get("status") == "failed":
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
        except Exception as e:
            st.error(f"Request failed: {str(e)}")
    
    def display_bonds_results(self, result: Dict[str, Any]):
        """Display bonds analysis results."""
        if not result:
            return
        
        if result.get('error'):
            st.error(f"Analysis failed: {result.get('error')}")
            return
        
        analysis_type = result.get('analysis_type', '')
        
        if analysis_type == "market_bonds":
            self._display_market_bonds_results(result)
        elif analysis_type == "yield_curve":
            self._display_yield_curve_results(result)
        elif analysis_type == "international_comparison":
            self._display_international_comparison_results(result)
        elif analysis_type == "bond_trends":
            self._display_bond_trends_results(result)
    
    def _display_market_bonds_results(self, result: Dict[str, Any]):
        """Display market bonds analysis results."""
        market = result.get('market', 'Unknown')
        summary = result.get('summary', {})
        bonds = result.get('bonds', [])
        
        st.subheader(f"📊 {market.replace('_', ' ').title()} Analysis")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_yield = summary.get('average_yield', 0)
            st.metric("Average Yield", f"{avg_yield:.3f}%")
        with col2:
            avg_change = summary.get('average_change', 0)
            st.metric("Average Change", f"{avg_change:+.3f}%")
        with col3:
            bonds_analyzed = summary.get('bonds_analyzed', 0)
            total_bonds = summary.get('total_bonds', 0)
            st.metric("Bonds Analyzed", f"{bonds_analyzed}/{total_bonds}")
        
        # Individual bonds table
        if bonds:
            st.subheader("Individual Bonds")
            bonds_data = []
            for bond_data in bonds:
                if bond_data.get('success', False):
                    bond_info = bond_data.get('bond_info', {})
                    bonds_data.append({
                        'Name': bond_info.get('name', 'Unknown'),
                        'Maturity': bond_info.get('maturity', 'Unknown'),
                        'Current Yield': f"{bond_data.get('current_yield', 0):.3f}%",
                        'Change': f"{bond_data.get('change', 0):+.3f}%",
                        'Change %': f"{bond_data.get('change_pct', 0):+.2f}%",
                        '52W High': f"{bond_data.get('high_52w', 0):.3f}%",
                        '52W Low': f"{bond_data.get('low_52w', 0):.3f}%"
                    })
            
            if bonds_data:
                df = pd.DataFrame(bonds_data)
                st.dataframe(df, use_container_width=True)
        
        # Multi-Agent Analysis Section (if available)
        if result.get('agent_results'):
            # Display main metrics using common utilities
            WebAnalysisDisplayUtils.display_main_metrics(result, asset_type="bonds")
            
            # Display agent results using common utilities
            agent_results = result.get('agent_results', {})
            WebAnalysisDisplayUtils.display_agent_results(agent_results)
            
            # Display market context using common utilities
            market_context = result.get('market_context', {})
            WebAnalysisDisplayUtils.display_market_context(market_context, asset_type="bonds")
            
            # Display trading parameters if available
            trading_params = result.get('trading_parameters', {})
            WebAnalysisDisplayUtils.display_trading_parameters(trading_params, asset_type="bonds")
            
            # Display enhanced analysis if available
            enhanced_analysis = result.get('enhanced_analysis', '')
            WebAnalysisDisplayUtils.display_enhanced_analysis(enhanced_analysis)
            
            # Display price chart if available
            market_data = result.get('market_data', {})
            historical_data = market_data.get('historical_data')
            if historical_data is not None and not historical_data.empty:
                WebAnalysisDisplayUtils.display_price_chart(historical_data, market, asset_type="bonds")
            
            # Display technical indicators if available
            technical_indicators = market_data.get('technical_indicators', {})
            WebAnalysisDisplayUtils.display_technical_indicators(technical_indicators, asset_type="bonds")
        
        # Legacy AI Analysis Section (fallback for older format)
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


def bonds_analysis_page():
    """Standalone bonds analysis page function."""
    # Get API headers with authentication token
    if 'auth_token' not in st.session_state:
        st.error("Please log in to access bonds analysis.")
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
            url = f"http://localhost:8000{endpoint}"
            
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
    
    # Create bonds analysis instance and run the page
    bonds_analyzer = BondsAnalysis("http://localhost:8000", make_request)
    bonds_analyzer.bonds_analysis_page()
    
    def _display_yield_curve_results(self, result: Dict[str, Any]):
        """Display yield curve analysis results."""
        country = result.get('country', 'Unknown')
        curve_data = result.get('curve_data', [])
        curve_shape = result.get('curve_shape', 'Unknown')
        slope = result.get('slope', 0)
        
        st.subheader(f"📈 {country} Yield Curve")
        
        # Curve metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Curve Shape", curve_shape)
        with col2:
            st.metric("Slope (Long - Short)", f"{slope:+.3f}%")
        
        # Yield curve chart
        if curve_data:
            df = pd.DataFrame(curve_data)
            df = df.sort_values('maturity')
            
            fig = px.line(df, x='maturity', y='yield', 
                         title=f"{country} Yield Curve",
                         labels={'maturity': 'Maturity (Years)', 'yield': 'Yield (%)'})
            fig.update_traces(mode='lines+markers')
            st.plotly_chart(fig, use_container_width=True)
            
            # Curve data table
            st.subheader("Yield Curve Points")
            curve_table = []
            for point in curve_data:
                maturity = point['maturity']
                if maturity < 1:
                    maturity_str = f"{int(maturity * 12)}M"
                else:
                    maturity_str = f"{int(maturity)}Y"
                
                curve_table.append({
                    'Maturity': maturity_str,
                    'Yield': f"{point['yield']:.3f}%",
                    'Bond': point['name']
                })
            
            df_table = pd.DataFrame(curve_table)
            st.dataframe(df_table, use_container_width=True)
        
        # AI Analysis
        ai_analysis = result.get('ai_analysis')
        if ai_analysis:
            if isinstance(ai_analysis, str):
                st.subheader("🤖 AI Analysis")
                st.write(ai_analysis)
            else:
                st.warning(f"AI Analysis unavailable: {ai_analysis}")
    
    def _display_international_comparison_results(self, result: Dict[str, Any]):
        """Display international bonds comparison results."""
        maturity = result.get('maturity', 'Unknown')
        comparison = result.get('comparison', [])
        benchmark_yield = result.get('benchmark_yield', 0)
        
        st.subheader(f"🌍 International {maturity} Bonds Comparison")
        
        if benchmark_yield:
            st.info(f"Benchmark (US Treasury): {benchmark_yield:.3f}%")
        
        # Comparison chart
        if comparison:
            df = pd.DataFrame(comparison)
            df['spread_bp'] = (df['yield'] - benchmark_yield) * 100 if benchmark_yield else 0
            
            fig = px.bar(df, x='country', y='yield',
                        title=f"{maturity} Government Bond Yields",
                        labels={'country': 'Country', 'yield': 'Yield (%)'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Spreads chart
            if benchmark_yield:
                fig_spread = px.bar(df, x='country', y='spread_bp',
                                  title=f"Spreads vs US Treasury ({maturity})",
                                  labels={'country': 'Country', 'spread_bp': 'Spread (bp)'})
                st.plotly_chart(fig_spread, use_container_width=True)
            
            # Comparison table
            st.subheader("International Bonds Data")
            comparison_table = []
            for bond in comparison:
                spread_bp = (bond['yield'] - benchmark_yield) * 100 if benchmark_yield else 0
                comparison_table.append({
                    'Country': bond['country'],
                    'Yield': f"{bond['yield']:.3f}%",
                    'Spread (bp)': f"{spread_bp:+.0f}",
                    'Change': f"{bond['change']:+.3f}%",
                    'Change %': f"{bond['change_pct']:+.2f}%",
                    'Currency': bond['currency']
                })
            
            df_table = pd.DataFrame(comparison_table)
            st.dataframe(df_table, use_container_width=True)
        
        # AI Analysis
        ai_analysis = result.get('ai_analysis')
        if ai_analysis:
            if isinstance(ai_analysis, str):
                st.subheader("🤖 AI Analysis")
                st.write(ai_analysis)
            else:
                st.warning(f"AI Analysis unavailable: {ai_analysis}")
    
    def _display_bond_trends_results(self, result: Dict[str, Any]):
        """Display bond trends analysis results."""
        market = result.get('market', 'Unknown')
        period = result.get('period', 'Unknown')
        market_direction = result.get('market_direction', 'Unknown')
        trends_summary = result.get('trends_summary', {})
        trends = result.get('trends', [])
        
        st.subheader(f"📊 {market.replace('_', ' ').title()} Trends ({period})")
        
        # Trends summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Market Direction", market_direction)
        with col2:
            rising = trends_summary.get('rising', 0)
            st.metric("Rising Yields", rising)
        with col3:
            falling = trends_summary.get('falling', 0)
            st.metric("Falling Yields", falling)
        with col4:
            stable = trends_summary.get('stable', 0)
            st.metric("Stable Yields", stable)
        
        # Trends chart
        if trends:
            df = pd.DataFrame(trends)
            fig = px.bar(df, x='bond', y='total_change_pct',
                        color='trend',
                        title=f"Bond Yield Changes ({period})",
                        labels={'bond': 'Bond', 'total_change_pct': 'Change (%)'})
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Trends table
            st.subheader("Individual Bond Trends")
            trends_table = []
            for trend in trends:
                trends_table.append({
                    'Bond': trend['bond'],
                    'Maturity': trend['maturity'],
                    'Start Yield': f"{trend['start_yield']:.3f}%",
                    'End Yield': f"{trend['end_yield']:.3f}%",
                    'Total Change': f"{trend['total_change']:+.3f}%",
                    'Change %': f"{trend['total_change_pct']:+.2f}%",
                    'Trend': trend['trend'],
                    'Volatility': f"{trend['volatility']:.3f}%"
                })
            
            df_table = pd.DataFrame(trends_table)
            st.dataframe(df_table, use_container_width=True)
        
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


def bonds_analysis_page():
    """Standalone bonds analysis page function."""
    # Get API headers with authentication token
    if 'auth_token' not in st.session_state:
        st.error("Please log in to access bonds analysis.")
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
            url = f"http://localhost:8000{endpoint}"
            
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
    
    # Create bonds analysis instance and run the page
    bonds_analyzer = BondsAnalysis("http://localhost:8000", make_request)
    bonds_analyzer.bonds_analysis_page()
