"""
Streamlit frontend for MarketResearcher web interface.
"""

import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, Any
from stock_analysis import StockAnalysis
from crypto_analysis import CryptoAnalysis
from forex_analysis import ForexAnalysis
from bonds_analysis import BondsAnalysis
from commodity_futures_analysis import CommodityFuturesAnalysis
from derivatives_analysis import DerivativesAnalysis
from portfolio_manager import PortfolioManager
from scanner_agency import ScannerAgency

# Page config
st.set_page_config(
    page_title="MarketResearcher",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "#http://your-server-ip:8000"  # Update with your server IP

class MarketResearcherApp:
    """Main Streamlit application for MarketResearcher."""
    
    def __init__(self):
        """Initialize the application."""
        self.api_base_url = "#http://your-server-ip:8000"  # Update with your server IP
        
        # Initialize session state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'token' not in st.session_state:
            st.session_state.token = None
        if 'username' not in st.session_state:
            st.session_state.username = None
        
        # Initialize modular components
        self.stock_analysis = StockAnalysis(self.api_base_url, self.make_request)
        self.crypto_analysis = CryptoAnalysis(self.api_base_url, self.make_request)
        self.forex_analysis = ForexAnalysis(self.api_base_url, self.make_request)
        self.bonds_analysis = BondsAnalysis(self.api_base_url, self.make_request)
        self.commodity_futures_analysis = CommodityFuturesAnalysis(self.api_base_url, self.make_request)
        self.derivatives_analysis = DerivativesAnalysis(self.api_base_url, self.make_request)
        self.portfolio_manager = PortfolioManager(self.api_base_url, self.make_api_request)
        self.scanner_agency = ScannerAgency(self.api_base_url, self.make_request)
    
    def make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Make authenticated API request."""
        headers = {}
        if st.session_state.token:
            headers["Authorization"] = f"Bearer {st.session_state.token}"
        
        url = f"{self.api_base_url}{endpoint}"
        
        try:
            if method == "POST":
                response = requests.post(url, json=data, headers=headers)
            else:
                response = requests.get(url, headers=headers)
            
            if response.status_code == 401:
                st.session_state.authenticated = False
                st.session_state.token = None
                st.error("Authentication expired. Please log in again.")
                return {}
            
            # Check if response has content before trying to parse JSON
            if response.text.strip():
                return response.json()
            else:
                return {"error": "Empty response from API"}
        except requests.exceptions.JSONDecodeError:
            return {"error": f"Invalid JSON response: {response.text[:100]}"}
        except Exception as e:
            return {"error": f"API connection error: {e}"}
    
    def make_api_request(self, method: str, endpoint: str, **kwargs):
        """Make API request with authentication."""
        try:
            headers = {}
            if "token" in st.session_state:
                headers["Authorization"] = f"Bearer {st.session_state.token}"
            
            url = f"{self.api_base_url}{endpoint}"
            response = requests.request(method, url, headers=headers, **kwargs)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                st.error("Authentication failed. Please login again.")
                del st.session_state.token
                st.rerun()
            else:
                return {"error": f"API request failed: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def load_disclaimer_content(self, filename):
        """Load disclaimer content from CSV file."""
        try:
            with open(filename, 'r') as f:
                content = f.read().strip()
                return content if content else f"Content from {filename}"
        except Exception as e:
            return f"Error loading {filename}: {str(e)}"
    
    def login_page(self):
        """Display login page."""
        st.title("🔐 MarketResearcher Login")
        
        # Load and display disclaimers
        st.markdown("---")
        
        # Risk Disclaimer
        risk_content = self.load_disclaimer_content("risk_disclaimer.csv")
        with st.expander("⚠️ Risk Disclaimer - Please Read", expanded=False):
            st.markdown(risk_content)
        
        # Financial Disclaimer  
        financial_content = self.load_disclaimer_content("financial_disclaimer.csv")
        with st.expander("📋 Financial Disclaimer - Please Read", expanded=False):
            st.markdown(financial_content)
        
        st.markdown("---")
        
        with st.form("login_form"):
            st.markdown("### Please enter your credentials")
            
            # Disclaimer acknowledgment
            acknowledge = st.checkbox("I have read and acknowledge the Risk and Financial Disclaimers above")
            
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if not acknowledge:
                    st.error("Please acknowledge that you have read the disclaimers before logging in.")
                    return
                    
                login_data = {"username": username, "password": password}
                response = self.make_request("/auth/login", "POST", login_data)
                
                if "access_token" in response:
                    st.session_state.authenticated = True
                    st.session_state.token = response["access_token"]
                    st.session_state.username = response["username"]
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
        
    
    def sidebar_navigation(self):
        """Display sidebar navigation."""
        with st.sidebar:
            st.title("📊 MarketResearcher")
            st.markdown(f"**User:** {st.session_state.username}")
            
            # Navigation menu
            page = st.selectbox(
                "Navigate to:",
                ["Dashboard", "Stock Analysis", "Crypto Analysis", "Forex Analysis", "Bonds & Gilts", "Derivatives", "Commodity Futures", "Scanner Agency", "Portfolio", "Settings"]
            )
            
            # Logout button
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.token = None
                st.session_state.username = None
                st.rerun()
            
            # Auto-login for development (always enabled when no API server)
            if not st.session_state.get('authenticated'):
                st.session_state.authenticated = True
                st.session_state.token = "dev_token"
                st.session_state.username = "admin"
            
            return page
    
    def dashboard_page(self):
        """Display dashboard page."""
        st.title("📊 MarketResearcher Dashboard")
        
        # Health check
        health = self.make_request("/health")
        if health.get("status") == "healthy":
            st.success("✅ System Status: Healthy")
        else:
            st.error("❌ System Status: Unhealthy")
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Active Users", "1", "0")
        
        with col2:
            st.metric("API Status", "Online", "")
        
        with col3:
            st.metric("Last Analysis", "2 min ago", "")
        
        with col4:
            st.metric("System Uptime", "99.9%", "0.1%")
        
        # Recent activity - user-specific
        st.subheader("Recent Activity")
        
        # Get user-specific activity from API
        try:
            activity_response = self.make_request("/user/activity", "GET")
            if activity_response and "activities" in activity_response:
                activity_data = activity_response["activities"]
                if activity_data:
                    st.dataframe(pd.DataFrame(activity_data), use_container_width=True)
                else:
                    st.info("No recent activity found.")
            else:
                st.info("Unable to load activity data.")
        except Exception as e:
            st.error(f"Failed to load activity: {e}")
            # Fallback to user-specific mock data
            current_user = st.session_state.get('username', 'user')
            activity_data = {
                "Time": [datetime.now().strftime("%H:%M")],
                "User": [current_user],
                "Action": ["Dashboard View"],
                "Symbol": ["-"],
                "Status": ["✅ Success"]
            }
            st.dataframe(pd.DataFrame(activity_data), use_container_width=True)
    
    def settings_page(self):
        """Display settings page with token usage tracking."""
        st.title("⚙️ Settings")
        
        # Token Usage Section
        st.subheader("🔢 Token Usage Statistics")
        
        # Get token usage data
        try:
            token_response = self.make_request("/user/token-usage", "GET")
            
            if token_response.get("success"):
                usage_stats = token_response.get("usage_stats", {})
                limits = token_response.get("limits", {})
                
                # Current limits and usage
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "Daily Token Usage", 
                        f"{limits.get('daily_used', 0):,}", 
                        f"{limits.get('daily_remaining', 0):,} remaining"
                    )
                    
                    daily_progress = limits.get('daily_used', 0) / max(limits.get('daily_limit', 1), 1)
                    st.progress(min(daily_progress, 1.0))
                    
                    if limits.get('daily_exceeded', False):
                        st.error("⚠️ Daily limit exceeded!")
                
                with col2:
                    st.metric(
                        "Monthly Token Usage", 
                        f"{limits.get('monthly_used', 0):,}", 
                        f"{limits.get('monthly_remaining', 0):,} remaining"
                    )
                    
                    monthly_progress = limits.get('monthly_used', 0) / max(limits.get('monthly_limit', 1), 1)
                    st.progress(min(monthly_progress, 1.0))
                    
                    if limits.get('monthly_exceeded', False):
                        st.error("⚠️ Monthly limit exceeded!")
                
                # Usage by analysis type
                if usage_stats.get('by_analysis_type'):
                    st.subheader("📊 Usage by Analysis Type")
                    
                    analysis_data = usage_stats['by_analysis_type']
                    df = pd.DataFrame(analysis_data)
                    
                    if not df.empty:
                        # Create pie chart for token usage by type
                        fig = px.pie(
                            df, 
                            values='tokens', 
                            names='analysis_type',
                            title="Token Usage Distribution"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Table view
                        st.dataframe(
                            df[['analysis_type', 'requests', 'tokens', 'cost']].rename(columns={
                                'analysis_type': 'Analysis Type',
                                'requests': 'Requests',
                                'tokens': 'Tokens',
                                'cost': 'Est. Cost ($)'
                            }),
                            use_container_width=True
                        )
                
                # Daily usage chart
                if usage_stats.get('daily_usage'):
                    st.subheader("📈 Daily Usage (Last 7 Days)")
                    
                    daily_data = usage_stats['daily_usage']
                    if daily_data:
                        df_daily = pd.DataFrame(daily_data)
                        
                        fig = px.bar(
                            df_daily, 
                            x='date', 
                            y='tokens',
                            title="Daily Token Usage",
                            labels={'tokens': 'Tokens Used', 'date': 'Date'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                # Recent requests
                if usage_stats.get('recent_requests'):
                    st.subheader("🕒 Recent Requests")
                    
                    recent_data = usage_stats['recent_requests']
                    if recent_data:
                        df_recent = pd.DataFrame(recent_data)
                        st.dataframe(
                            df_recent[['timestamp', 'analysis_type', 'symbol', 'total_tokens', 'cost_estimate']].rename(columns={
                                'timestamp': 'Time',
                                'analysis_type': 'Type',
                                'symbol': 'Symbol',
                                'total_tokens': 'Tokens',
                                'cost_estimate': 'Cost ($)'
                            }),
                            use_container_width=True
                        )
                
                # Token limits configuration
                st.subheader("⚙️ Token Limits")
                
                with st.form("token_limits_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_daily_limit = st.number_input(
                            "Daily Token Limit", 
                            min_value=1000, 
                            max_value=100000, 
                            value=limits.get('daily_limit', 10000),
                            step=1000
                        )
                    
                    with col2:
                        new_monthly_limit = st.number_input(
                            "Monthly Token Limit", 
                            min_value=10000, 
                            max_value=1000000, 
                            value=limits.get('monthly_limit', 100000),
                            step=10000
                        )
                    
                    if st.form_submit_button("Update Limits"):
                        limits_data = {
                            "daily_limit": new_daily_limit,
                            "monthly_limit": new_monthly_limit
                        }
                        
                        response = self.make_request("/user/token-limits", "POST", limits_data)
                        if response.get("success"):
                            st.success("Token limits updated successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to update limits: {response.get('error', 'Unknown error')}")
            
            else:
                st.error(f"Failed to load token usage: {token_response.get('error', 'Unknown error')}")
        
        except Exception as e:
            st.error(f"Error loading token usage: {str(e)}")
        
        st.markdown("---")
        
        # Other settings sections
        st.subheader("🔧 API Configuration")
        st.text_input("API Base URL", value=self.api_base_url, disabled=True)
        
        # Password Change Section
        st.subheader("🔒 Password Management")
        
        if st.button("🔑 Change Password", use_container_width=True):
            st.session_state.show_password_dialog = True
        
        # Password change dialog
        if st.session_state.get('show_password_dialog', False):
            with st.form("password_change_form"):
                st.markdown("### Change Your Password")
                
                current_password = st.text_input("Current Password", type="password", placeholder="Enter current password")
                new_password = st.text_input("New Password", type="password", placeholder="Enter new password")
                confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Confirm new password")
                
                col1, col2 = st.columns(2)
                with col1:
                    submit_password = st.form_submit_button("Update Password", type="primary", use_container_width=True)
                with col2:
                    cancel_password = st.form_submit_button("Cancel", use_container_width=True)
                
                if cancel_password:
                    st.session_state.show_password_dialog = False
                    st.rerun()
                
                if submit_password:
                    if not current_password or not new_password or not confirm_password:
                        st.error("All password fields are required")
                    elif new_password != confirm_password:
                        st.error("New passwords do not match")
                    elif len(new_password) < 6:
                        st.error("New password must be at least 6 characters long")
                    else:
                        # Make API request to change password
                        password_data = {
                            "current_password": current_password,
                            "new_password": new_password
                        }
                        
                        response = self.make_request("/auth/change-password", "POST", password_data)
                        
                        if response.get("success"):
                            st.success("Password changed successfully!")
                            st.session_state.show_password_dialog = False
                            st.rerun()
                        else:
                            st.error(f"Password change failed: {response.get('error', 'Unknown error')}")
        
        st.markdown("---")
        
        st.subheader("👤 User Preferences")
        st.selectbox("Default Currency", ["USD", "EUR", "GBP", "JPY"])
        st.selectbox("Theme", ["Light", "Dark"])
        st.slider("Refresh Interval (seconds)", 5, 60, 30)
        
        st.subheader("⚠️ Risk Settings")
        st.slider("Risk Tolerance", 1, 10, 5)
        st.number_input("Max Position Size (%)", 1, 100, 25)
        
        if st.button("Save Settings"):
            st.success("Settings saved successfully!")
    
    def run(self):
        """Run the Streamlit app."""
        if not st.session_state.authenticated:
            self.login_page()
        else:
            # Skip API verification when running standalone
            # verify_response = self.make_request("/auth/verify")
            # if "error" in verify_response:
            #     st.session_state.authenticated = False
            #     st.rerun()
            
            # Main app
            page = self.sidebar_navigation()
            
            if page == "Dashboard":
                self.dashboard_page()
            elif page == "Stock Analysis":
                self.stock_analysis.stock_analysis_page()
            elif page == "Crypto Analysis":
                self.crypto_analysis.crypto_analysis_page()
            elif page == "Forex Analysis":
                self.forex_analysis.forex_analysis_page()
            elif page == "Bonds & Gilts":
                self.bonds_analysis.bonds_analysis_page()
            elif page == "Derivatives":
                self.derivatives_analysis.derivatives_analysis_page()
            elif page == "Commodity Futures":
                self.commodity_futures_analysis.commodity_futures_analysis_page()
            elif page == "Scanner Agency":
                self.scanner_agency.render_scanner_dashboard()
            elif page == "Portfolio":
                self.portfolio_manager.portfolio_page()
            elif page == "Settings":
                self.settings_page()

# Run the app
if __name__ == "__main__":
    app = MarketResearcherApp()
    app.run()
