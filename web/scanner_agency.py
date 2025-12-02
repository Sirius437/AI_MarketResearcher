"""
Scanner Agency - Streamlit frontend for MarketResearcher Scanner Agent.
Provides web interface for trading opportunity detection using IB market scanners.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.scanner_agent import ScannerAgent
from data.interactive_brokers_client import InteractiveBrokersClient
from llm.local_client import LocalLLMClient
from llm.prompt_manager import PromptManager
from config.settings import MarketResearcherConfig


class ScannerAgency:
    """Web interface for Scanner Agent functionality."""
    
    def __init__(self, api_base_url: str, make_request_func):
        """Initialize Scanner Agency."""
        self.api_base_url = api_base_url
        self.make_request = make_request_func
        
        # Initialize scanner agent components
        self.config = MarketResearcherConfig()
        self.llm_client = LocalLLMClient(self.config)
        self.prompt_manager = PromptManager(self.config)
        
        # Initialize scanner agent (it will create its own IB client)
        self.scanner_agent = ScannerAgent(
            llm_client=self.llm_client,
            prompt_manager=self.prompt_manager,
            config=self.config
        )
        
        # Available scanner configurations
        self.available_scanners = {
            "hot_us_volume": {
                "name": "Hot US Stocks by Volume",
                "description": "US stocks with highest trading volume",
                "market": "STK.US.MAJOR",
                "icon": "🔥"
            },
            "top_gainers_ibis": {
                "name": "Top % Gainers IBIS",
                "description": "Top percentage gainers at IBIS exchange",
                "market": "STK.EU.IBIS", 
                "icon": "📈"
            },
            "active_futures_eurex": {
                "name": "Most Active Futures EUREX",
                "description": "Most active futures contracts at EUREX",
                "market": "FUT.EU.EUREX",
                "icon": "⚡"
            },
            "high_option_volume": {
                "name": "High Option Volume P/C Ratio",
                "description": "High option volume put/call ratio for US indices",
                "market": "IND.US",
                "icon": "🎯"
            },
            "complex_orders": {
                "name": "Complex Orders and Trades",
                "description": "Complex orders and trades for options combinations",
                "market": "NATCOMB.OPT.US",
                "icon": "🧩"
            }
        }
    
    def render_scanner_dashboard(self):
        """Render the main scanner dashboard."""
        st.header("🔍 Trading Opportunity Scanner")
        st.markdown("**Systematic detection of trading opportunities using market scanners**")
        
        # Create tabs for different scanner functions
        tab1, tab2, tab3, tab4 = st.tabs([
            "🚀 Run Scanners", 
            "📊 Scanner Results", 
            "⚙️ Available Scanners",
            "📈 Analysis History"
        ])
        
        with tab1:
            self._render_run_scanners()
        
        with tab2:
            self._render_scanner_results()
            
        with tab3:
            self._render_available_scanners()
            
        with tab4:
            self._render_analysis_history()
    
    def _render_run_scanners(self):
        """Render the scanner execution interface."""
        st.subheader("Execute Market Scanners")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Scanner Selection")
            
            # Multi-select for scanners
            selected_scanners = st.multiselect(
                "Select scanners to run:",
                options=list(self.available_scanners.keys()),
                format_func=lambda x: f"{self.available_scanners[x]['icon']} {self.available_scanners[x]['name']}",
                default=["hot_us_volume"],
                help="Choose one or more scanners to execute simultaneously"
            )
            
            # Max results slider
            max_results = st.slider(
                "Maximum results per scanner:",
                min_value=5,
                max_value=50,
                value=20,
                step=5,
                help="Number of top opportunities to retrieve from each scanner"
            )
            
            # Use cache checkbox
            use_cache = st.checkbox(
                "Use cached results (if available)",
                value=True,
                help="Use previously cached scanner results to avoid API rate limits"
            )
        
        with col2:
            st.markdown("### Scanner Status")
            
            # IB Connection status
            connection_status = self._check_ib_connection()
            if connection_status:
                st.success("✅ Gateway Connected")
            else:
                st.error("❌ Gateway Disconnected")
                st.markdown("**Please ensure Gateway is running**")
            
            # Scanner execution button
            if st.button("🚀 Run Selected Scanners", type="primary", disabled=not selected_scanners):
                if selected_scanners:
                    self._execute_scanners(selected_scanners, max_results, use_cache)
                else:
                    st.warning("Please select at least one scanner to run.")
    
    def _render_scanner_results(self):
        """Render scanner results display."""
        st.subheader("Scanner Results")
        
        # Check for results in session state
        if 'scanner_results' not in st.session_state:
            st.info("No scanner results available. Run scanners to see results here.")
            return
        
        results = st.session_state.scanner_results
        
        if not results.get('success'):
            st.error(f"Scanner execution failed: {results.get('error', 'Unknown error')}")
            return
        
        # Display results summary
        scanner_data = results.get('scanner_data', {})
        top_opportunities = results.get('top_opportunities', [])
        
        if not scanner_data and not top_opportunities:
            st.warning("No scanner data available in results.")
            return
        
        # Results overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate metrics from both scanner_data and top_opportunities
        total_opportunities = 0
        scanners_run = 0
        all_scores = []
        
        if scanner_data:
            total_opportunities = sum(len(data.get('opportunities', [])) for data in scanner_data.values())
            scanners_run = len(scanner_data)
            for data in scanner_data.values():
                for opp in data.get('opportunities', []):
                    if 'total_score' in opp:
                        all_scores.append(opp['total_score'])
        elif top_opportunities:
            total_opportunities = len(top_opportunities)
            scanners_run = 1
            for opp in top_opportunities:
                if 'opportunity_score' in opp:
                    all_scores.append(opp['opportunity_score'])
        
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        top_score = max(all_scores) if all_scores else 0
        
        col1.metric("Total Opportunities", total_opportunities)
        col2.metric("Scanners Run", scanners_run)
        col3.metric("Average Score", f"{avg_score:.2f}")
        col4.metric("Top Score", f"{top_score:.2f}")
        
        # Handle both old and new data structures
        if scanner_data:
            # New structure from API
            for scanner_name, data in scanner_data.items():
                opportunities = data.get('opportunities', [])
                self._display_scanner_results(scanner_name, opportunities)
        else:
            # Fallback: check for top_opportunities in results
            top_opportunities = results.get('top_opportunities', [])
            if top_opportunities:
                self._display_scanner_results("Hot US Stocks by Volume", top_opportunities)
            else:
                st.warning("No scanner results found in response.")
    
    def _display_scanner_results(self, scanner_name: str, opportunities: List[Dict]):
        """Display results for a single scanner."""
        scanner_icon = "🔥" if "Hot" in scanner_name else "📊"
        
        with st.expander(f"{scanner_icon} {scanner_name} Results", expanded=True):
            if not opportunities:
                st.info("No opportunities found for this scanner.")
                return
            
            # Convert to DataFrame for display
            df = pd.DataFrame(opportunities)
            
            # Create interactive table
            if not df.empty:
                # Map API field names to display names
                column_mapping = {
                    'symbol': 'Symbol',
                    'longName': 'Company',
                    'opportunity_score': 'Score',
                    'rank': 'Rank',
                    'currency': 'Currency',
                    'exchange': 'Exchange'
                }
                
                # Select available columns
                available_columns = [col for col in column_mapping.keys() if col in df.columns]
                
                if available_columns:
                    display_df = df[available_columns].copy()
                    
                    # Rename columns for display
                    display_df = display_df.rename(columns=column_mapping)
                    
                    # Format numeric columns
                    if 'Score' in display_df.columns:
                        display_df['Score'] = display_df['Score'].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A")
                    
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Show summary stats
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Results", len(opportunities))
                    if 'opportunity_score' in df.columns:
                        avg_score = df['opportunity_score'].mean()
                        max_score = df['opportunity_score'].max()
                        col2.metric("Avg Score", f"{avg_score:.1f}")
                        col3.metric("Max Score", f"{max_score:.1f}")
                else:
                    # Fallback: show raw data
                    st.write("Raw scanner data:")
                    st.json(opportunities[:5])  # Show first 5 results
    
    def _render_available_scanners(self):
        """Render available scanners information."""
        st.subheader("Available Market Scanners")
        
        for scanner_key, config in self.available_scanners.items():
            with st.expander(f"{config['icon']} {config['name']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Description:** {config['description']}")
                    st.markdown(f"**Market:** {config['market']}")
                    st.markdown(f"**Scanner Type:** {scanner_key}")
                
                with col2:
                    if st.button(f"Run {config['name']}", key=f"run_{scanner_key}"):
                        self._execute_scanners([scanner_key], 20, True)
    
    def _render_analysis_history(self):
        """Render analysis history and cached results."""
        st.subheader("Analysis History")
        
        # This would typically load from a database or file system
        # For now, show placeholder content
        st.info("Analysis history functionality will be implemented to show:")
        st.markdown("""
        - Previous scanner execution results
        - Historical performance tracking
        - Trend analysis of trading opportunities
        - Success rate metrics
        - Cached results management
        """)
    
    def _check_ib_connection(self) -> bool:
        """Check Interactive Brokers connection status via scanner service."""
        try:
            import requests
            response = requests.get('http://localhost:5000/health', timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('ib_connected', False)
            return False
        except Exception:
            return False
    
    def _execute_scanners(self, scanner_types: List[str], max_results: int, use_cache: bool):
        """Execute selected scanners."""
        with st.spinner("🔍 Running market scanners..."):
            try:
                # Prepare analysis data
                analysis_data = {
                    'scanner_types': scanner_types,
                    'max_results': max_results,
                    'use_cache': use_cache
                }
                
                # Execute scanner via separate service to avoid threading conflicts
                import requests
                try:
                    response = requests.post(
                        'http://localhost:5000/scanner/execute',
                        json=analysis_data,
                        timeout=120
                    )
                    if response.status_code == 200:
                        result = response.json()
                    else:
                        result = {'success': False, 'error': f'Scanner service error: {response.status_code}'}
                except requests.exceptions.ConnectionError:
                    result = {'success': False, 'error': 'Scanner service not running. Start with: python web/scanner_service.py'}
                except Exception as e:
                    result = {'success': False, 'error': str(e)}
                
                # Store results in session state
                st.session_state.scanner_results = result
                
                if result.get('success'):
                    st.success(f"✅ Successfully executed {len(scanner_types)} scanner(s)")
                    st.rerun()
                else:
                    st.error(f"❌ Scanner execution failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"❌ Error executing scanners: {str(e)}")
    
    
    def create_opportunity_chart(self, opportunities: List[Dict[str, Any]], title: str) -> go.Figure:
        """Create interactive chart for trading opportunities."""
        if not opportunities:
            return go.Figure()
        
        df = pd.DataFrame(opportunities)
        
        # Create scatter plot of price vs volume colored by score
        fig = px.scatter(
            df,
            x='volume',
            y='price',
            color='total_score',
            size='market_cap',
            hover_data=['symbol', 'company_name', 'change_percent'],
            title=title,
            labels={
                'volume': 'Trading Volume',
                'price': 'Price ($)',
                'total_score': 'Opportunity Score'
            }
        )
        
        fig.update_layout(
            height=500,
            showlegend=True
        )
        
        return fig
    
    def format_currency(self, value: float, currency: str = "USD") -> str:
        """Format currency values."""
        if pd.isna(value) or value == 0:
            return "N/A"
        
        if value >= 1e9:
            return f"${value/1e9:.2f}B"
        elif value >= 1e6:
            return f"${value/1e6:.2f}M"
        elif value >= 1e3:
            return f"${value/1e3:.2f}K"
        else:
            return f"${value:.2f}"
    
    def get_scanner_summary_stats(self, scanner_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics for scanner results."""
        total_opportunities = 0
        total_volume = 0
        avg_score = 0
        top_opportunities = []
        
        for scanner_type, data in scanner_data.items():
            opportunities = data.get('opportunities', [])
            total_opportunities += len(opportunities)
            
            for opp in opportunities:
                if 'volume' in opp and opp['volume']:
                    total_volume += opp['volume']
                if 'total_score' in opp:
                    top_opportunities.append({
                        'symbol': opp.get('symbol', 'N/A'),
                        'score': opp['total_score'],
                        'scanner': scanner_type
                    })
        
        # Sort by score and get top 10
        top_opportunities.sort(key=lambda x: x['score'], reverse=True)
        top_10 = top_opportunities[:10]
        
        if top_opportunities:
            avg_score = sum(opp['score'] for opp in top_opportunities) / len(top_opportunities)
        
        return {
            'total_opportunities': total_opportunities,
            'total_volume': total_volume,
            'average_score': avg_score,
            'top_opportunities': top_10
        }
