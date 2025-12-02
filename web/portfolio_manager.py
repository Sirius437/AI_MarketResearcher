"""
Portfolio management functionality for MarketResearcher web interface.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


class PortfolioManager:
    """Portfolio management functionality."""
    
    def __init__(self, api_base_url: str, make_api_request_func):
        """Initialize portfolio manager."""
        self.api_base_url = api_base_url
        self.make_api_request = make_api_request_func
    
    def portfolio_page(self):
        """Display portfolio management page."""
        st.title("💼 Portfolio Management")
        
        # Portfolio tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📝 Manage", "🤖 AI Analysis", "📈 Performance"])
        
        with tab1:
            self.portfolio_overview_tab()
        
        with tab2:
            self.portfolio_trade_tab()
        
        with tab3:
            self.portfolio_ai_analysis_tab()
        
        with tab4:
            self.portfolio_performance_tab()
    
    def get_portfolio(self):
        """Get portfolio data from session state or load from disk."""
        if "portfolio" not in st.session_state:
            st.session_state.portfolio = self.load_portfolio_from_disk()
        return st.session_state.portfolio
    
    def load_portfolio_from_disk(self):
        """Load portfolio from disk."""
        # Create portfolio directory if it doesn't exist
        portfolio_dir = os.path.join(os.path.expanduser("~"), ".marketresearcher")
        os.makedirs(portfolio_dir, exist_ok=True)
        
        portfolio_file = os.path.join(portfolio_dir, "portfolio_data.json")
        if os.path.exists(portfolio_file):
            try:
                with open(portfolio_file, 'r') as f:
                    portfolio = json.load(f)
                    # Add timestamp for when portfolio was loaded
                    portfolio["last_loaded"] = datetime.now().isoformat()
                    return portfolio
            except Exception as e:
                st.error(f"Failed to load portfolio from disk: {e}")
        
        # Return default portfolio if file doesn't exist
        return {
            "positions": {},
            "cash_balance": 100000.0,
            "total_value": 100000.0,
            "daily_pnl": 0.0,
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
    
    def save_portfolio_to_disk(self, portfolio):
        """Save portfolio to disk."""
        # Create portfolio directory if it doesn't exist
        portfolio_dir = os.path.join(os.path.expanduser("~"), ".marketresearcher")
        os.makedirs(portfolio_dir, exist_ok=True)
        
        portfolio_file = os.path.join(portfolio_dir, "portfolio_data.json")
        
        # Update timestamp
        portfolio["last_updated"] = datetime.now().isoformat()
        
        try:
            with open(portfolio_file, 'w') as f:
                json.dump(portfolio, f, indent=2)
        except Exception as e:
            st.error(f"Failed to save portfolio to disk: {e}")
    
    def portfolio_overview_tab(self):
        """Portfolio overview tab."""
        # Get portfolio data
        portfolio = self.get_portfolio()
        
        if portfolio:
            # Portfolio overview
            st.subheader("Portfolio Overview")
            
            # Show portfolio persistence status
            if portfolio.get("last_loaded"):
                st.info(f"📁 Portfolio loaded from disk (Last updated: {portfolio.get('last_updated', 'Unknown')[:19]})")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_value = portfolio.get('total_value', 0)
                st.metric("Total Value", f"${total_value:,.2f}")
            
            with col2:
                cash_balance = portfolio.get('cash_balance', 0)
                st.metric("Cash Balance", f"${cash_balance:,.2f}")
            
            with col3:
                daily_pnl = portfolio.get('daily_pnl', 0)
                st.metric("Daily P&L", f"${daily_pnl:,.2f}", delta=f"{daily_pnl:,.2f}")
            
            with col4:
                positions_count = len(portfolio.get('positions', {}))
                st.metric("Positions", positions_count)
            
            # Manual portfolio controls
            st.subheader("Portfolio Controls")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Save Portfolio to Disk"):
                    self.save_portfolio_to_disk(portfolio)
                    st.success("Portfolio saved to disk!")
            
            with col2:
                if st.button("🔄 Reload from Disk"):
                    portfolio = self.load_portfolio_from_disk()
                    st.session_state.portfolio = portfolio
                    st.success("Portfolio reloaded from disk!")
                    st.rerun()
            
            # Current positions
            positions = portfolio.get('positions', {})
            if positions:
                st.subheader("Current Positions")
                positions_data = []
                for symbol, pos in positions.items():
                    invested = pos['quantity'] * pos['avg_price']
                    current_value = pos['quantity'] * pos['current_price']
                    pnl = current_value - invested
                    pnl_pct = (pnl / invested * 100) if invested > 0 else 0
                    
                    positions_data.append({
                        'Symbol': symbol,
                        'Quantity': pos['quantity'],
                        'Avg Price': f"${pos['avg_price']:.2f}",
                        'Current Price': f"${pos['current_price']:.2f}",
                        'Market Value': f"${pos['current_price'] * pos['quantity']:,.2f}",
                        'P&L': f"${pnl:.2f}",
                        'P&L %': f"{pnl_pct:.2f}%"
                    })
                
                df = pd.DataFrame(positions_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No positions in portfolio")
        else:
            st.error("Failed to load portfolio data")
    
    def portfolio_trade_tab(self):
        """Portfolio trading tab."""
        st.subheader("Manage Positions")
        
        # Get portfolio
        portfolio = self.get_portfolio()
        
        # Add position form
        with st.form("add_position"):
            st.markdown("### Add New Position")
            
            col1, col2 = st.columns(2)
            with col1:
                symbol = st.text_input("Symbol", placeholder="e.g., AAPL, BTCUSDT")
                quantity = st.number_input("Quantity", min_value=0.0, step=0.1)
            
            with col2:
                avg_price = st.number_input("Average Price", min_value=0.0, step=0.01)
                current_price = st.number_input("Current Price", min_value=0.0, step=0.01)
            
            submitted = st.form_submit_button("➕ Add Position")
            
            if submitted and symbol and quantity > 0 and avg_price > 0:
                # Add position to portfolio
                if "positions" not in portfolio:
                    portfolio["positions"] = {}
                
                portfolio["positions"][symbol] = {
                    "quantity": quantity,
                    "avg_price": avg_price,
                    "current_price": current_price if current_price > 0 else avg_price,
                    "added_date": datetime.now().isoformat()
                }
                
                # Update session state and save
                st.session_state.portfolio = portfolio
                self.save_portfolio_to_disk(portfolio)
                
                st.success(f"Added {quantity} shares of {symbol} at ${avg_price:.2f}")
                st.rerun()
        
        # Current positions management
        positions = portfolio.get("positions", {})
        if positions:
            st.markdown("### Current Positions")
            
            for symbol, pos in positions.items():
                st.subheader(f"{symbol} - {pos['quantity']} shares")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Quantity:** {pos['quantity']}")
                    st.write(f"**Avg Price:** ${pos['avg_price']:.2f}")
                    st.write(f"**Current Price:** ${pos['current_price']:.2f}")
                
                with col2:
                    invested = pos['quantity'] * pos['avg_price']
                    current_value = pos['quantity'] * pos['current_price']
                    pnl = current_value - invested
                    pnl_pct = (pnl / invested * 100) if invested > 0 else 0
                    
                    st.write(f"**Invested:** ${invested:,.2f}")
                    st.write(f"**Current Value:** ${current_value:,.2f}")
                    st.write(f"**P&L:** ${pnl:,.2f} ({pnl_pct:.2f}%)")
                
                with col3:
                    if st.button(f"🗑️ Remove {symbol}", key=f"remove_{symbol}"):
                        del portfolio["positions"][symbol]
                        st.session_state.portfolio = portfolio
                        self.save_portfolio_to_disk(portfolio)
                        st.success(f"Removed {symbol} from portfolio")
                        st.rerun()
        else:
            st.info("No positions to manage. Add some positions above.")
    
    def portfolio_ai_analysis_tab(self):
        """Portfolio AI analysis tab."""
        st.subheader("🤖 AI Portfolio Analysis")
        
        portfolio = st.session_state.portfolio
        positions = portfolio.get("positions", {})
        
        if not positions:
            st.info("Add positions to your portfolio to get AI analysis")
            return
        
        # Portfolio summary for context
        st.markdown("### Portfolio Summary")
        total_value = sum(pos["quantity"] * pos["current_price"] for pos in positions.values())
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Positions", len(positions))
        with col2:
            st.metric("Portfolio Value", f"${total_value:,.2f}")
        with col3:
            largest_position = max(positions.items(), key=lambda x: x[1]["quantity"] * x[1]["current_price"])
            st.metric("Largest Position", largest_position[0])
        
        # AI Analysis button
        if st.button("🤖 Get AI Portfolio Analysis", type="primary", use_container_width=True):
            with st.spinner("Analyzing your portfolio..."):
                try:
                    # Prepare portfolio data for API
                    portfolio_data = {
                        "positions": positions,
                        "total_value": total_value,
                        "analysis_type": "comprehensive"
                    }
                    
                    response = self.make_api_request("POST", "/portfolio/analyze", json=portfolio_data)
                    
                    if response and response.get("success"):
                        analysis = response.get("analysis", {})
                        
                        # Display analysis results
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Recommendations
                            st.markdown("### 📋 Recommendations")
                            recommendations = analysis.get("recommendations", [])
                            if recommendations:
                                for i, rec in enumerate(recommendations, 1):
                                    st.write(f"**{i}.** {rec}")
                            
                            # Risk Assessment
                            st.markdown("### ⚠️ Risk Assessment")
                            risk_assessment = analysis.get("risk_assessment", {})
                            if risk_assessment:
                                risk_level = risk_assessment.get("level", "Unknown")
                                risk_score = risk_assessment.get("score", 0)
                                
                                if risk_level.lower() == "low":
                                    st.success(f"🟢 Risk Level: {risk_level} (Score: {risk_score}/10)")
                                elif risk_level.lower() == "medium":
                                    st.warning(f"🟡 Risk Level: {risk_level} (Score: {risk_score}/10)")
                                else:
                                    st.error(f"🔴 Risk Level: {risk_level} (Score: {risk_score}/10)")
                                
                                factors = risk_assessment.get("factors", [])
                                if factors:
                                    st.write("**Risk Factors:**")
                                    for factor in factors:
                                        st.write(f"• {factor}")
                        
                        with col2:
                            # Rebalancing Suggestions
                            st.markdown("### ⚖️ Rebalancing Suggestions")
                            rebalancing = analysis.get("rebalancing", [])
                            if rebalancing:
                                for i, suggestion in enumerate(rebalancing, 1):
                                    st.write(f"**{i}.** {suggestion}")
                        
                        # Full analysis section
                        if analysis.get("full_analysis"):
                            st.subheader("📋 Full AI Analysis")
                            st.markdown(analysis["full_analysis"])
                    
                    else:
                        st.error(f"❌ Portfolio analysis failed: {response.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Failed to get AI portfolio analysis: {e}")
    
    def update_portfolio_prices(self):
        """Update portfolio with current market prices."""
        portfolio = st.session_state.portfolio
        positions = portfolio.get("positions", {})
        
        if not positions:
            return False
        
        try:
            updated_count = 0
            for symbol, pos in positions.items():
                # Try to get current price from API
                try:
                    if symbol.endswith("USDT"):  # Crypto
                        response = self.make_api_request("GET", f"/crypto/price/{symbol}")
                    else:  # Stock
                        response = self.make_api_request("GET", f"/stock/price/{symbol}")
                    
                    if response and response.get("success"):
                        new_price = float(response.get("price", pos["current_price"]))
                        old_price = float(pos["current_price"])
                        
                        # Only update if price actually changed
                        if abs(new_price - old_price) > 0.01:
                            pos["current_price"] = new_price
                            updated_count += 1
                        
                except Exception:
                    # Keep existing price if API fails
                    continue
            
            # Update portfolio timestamp and save
            portfolio["last_price_update"] = datetime.now().isoformat()
            st.session_state.portfolio = portfolio
            self.save_portfolio_to_disk(portfolio)
            
            return updated_count > 0
            
        except Exception as e:
            st.error(f"Failed to update prices: {e}")
            return False
    
    def portfolio_performance_tab(self):
        """Portfolio performance tab."""
        st.subheader("Performance Analytics")
        
        portfolio = st.session_state.portfolio
        positions = portfolio.get("positions", {})
        
        if not positions:
            st.info("Add positions to your portfolio to see performance analytics")
            return
        
        # Price update controls
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            last_update = portfolio.get("last_price_update", "Never")
            if last_update != "Never":
                last_update = last_update[:19].replace("T", " ")
            st.info(f"📅 Last price update: {last_update}")
        
        with col2:
            if st.button("🔄 Update Prices", help="Fetch current market prices"):
                with st.spinner("Updating prices..."):
                    # Reload portfolio from disk first to get latest data
                    portfolio = self.load_portfolio_from_disk()
                    if portfolio:
                        st.session_state.portfolio = portfolio
                    
                    success = self.update_portfolio_prices()
                    if success:
                        st.success("Prices updated!")
                        # Force complete page refresh
                        st.rerun()
                    else:
                        st.error("Price update failed")
        
        with col3:
            if st.button("📊 Refresh Analytics", help="Recalculate performance metrics"):
                st.rerun()
        
        # Reload fresh portfolio data to ensure we have latest prices
        portfolio = st.session_state.portfolio
        positions = portfolio.get("positions", {})
        
        # Calculate enhanced portfolio metrics
        total_invested = 0
        current_value = 0
        position_returns = []
        
        for symbol, pos in positions.items():
            invested = pos["quantity"] * pos["avg_price"]
            current = pos["quantity"] * pos["current_price"]
            total_invested += invested
            current_value += current
            
            if invested > 0:
                return_pct = ((current - invested) / invested) * 100
                position_returns.append(return_pct)
        
        # Calculate portfolio-level metrics
        total_return = ((current_value - total_invested) / total_invested * 100) if total_invested > 0 else 0
        
        # Calculate portfolio volatility (simplified using position variance)
        if len(position_returns) > 1:
            import statistics
            portfolio_volatility = statistics.stdev(position_returns)
        else:
            portfolio_volatility = abs(total_return) * 0.5  # Simplified for single position
        
        # Calculate Sharpe ratio (simplified)
        risk_free_rate = 2.0  # Assume 2% risk-free rate
        sharpe_ratio = (total_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        
        # Performance metrics with enhanced calculations
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            delta_color = "normal" if total_return >= 0 else "inverse"
            st.metric("Total Return", f"{total_return:.2f}%", delta=f"{total_return:.2f}%")
        
        with col2:
            st.metric("Portfolio Volatility", f"{portfolio_volatility:.2f}%")
        
        with col3:
            st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
        
        with col4:
            unrealized_pnl = current_value - total_invested
            st.metric("Unrealized P&L", f"${unrealized_pnl:,.2f}", delta=f"${unrealized_pnl:,.2f}")
        
        # Additional metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Calculate max position weight
            max_weight = 0
            if current_value > 0:
                for pos in positions.values():
                    weight = (pos["quantity"] * pos["current_price"]) / current_value * 100
                    max_weight = max(max_weight, weight)
            st.metric("Max Position Weight", f"{max_weight:.1f}%")
        
        with col2:
            positions_count = len(positions)
            st.metric("Number of Positions", positions_count)
        
        with col3:
            # Calculate portfolio beta (simplified)
            portfolio_beta = 1.0 + (portfolio_volatility / 20)  # Simplified calculation
            st.metric("Portfolio Beta", f"{portfolio_beta:.2f}")
        
        with col4:
            # Calculate win rate
            winning_positions = sum(1 for ret in position_returns if ret > 0)
            win_rate = (winning_positions / len(position_returns) * 100) if position_returns else 0
            st.metric("Win Rate", f"{win_rate:.1f}%")
        
        # Asset allocation pie chart
        if positions:
            st.subheader("🥧 Asset Allocation")
            allocation_data = {}
            for symbol, pos in positions.items():
                value = pos["quantity"] * pos["current_price"]
                allocation_data[symbol] = value
            
            if allocation_data:
                fig = px.pie(
                    values=list(allocation_data.values()), 
                    names=list(allocation_data.keys()),
                    title="Portfolio Allocation by Value"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Position performance table
        st.subheader("📊 Position Performance")
        performance_data = []
        for symbol, pos in positions.items():
            invested = pos["quantity"] * pos["avg_price"]
            current = pos["quantity"] * pos["current_price"]
            pnl = current - invested
            pnl_pct = (pnl / invested * 100) if invested > 0 else 0
            weight = (current / current_value * 100) if current_value > 0 else 0
            
            performance_data.append({
                'Symbol': symbol,
                'Quantity': pos["quantity"],
                'Avg Price': f"${pos['avg_price']:.2f}",
                'Current Price': f"${pos['current_price']:.2f}",
                'Weight': f"{weight:.1f}%",
                'Invested': f"${invested:,.2f}",
                'Current Value': f"${current:,.2f}",
                'P&L': f"${pnl:,.2f}",
                'Return': f"{pnl_pct:.2f}%"
            })
        
        if performance_data:
            df = pd.DataFrame(performance_data)
            st.dataframe(df, use_container_width=True)
        
        # Risk metrics
        st.subheader("⚠️ Risk Metrics")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Concentration Risk:**")
            if max_weight > 30:
                st.warning(f"High concentration: {max_weight:.1f}% in single position")
            elif max_weight > 20:
                st.info(f"Moderate concentration: {max_weight:.1f}% in single position")
            else:
                st.success(f"Well diversified: Max position {max_weight:.1f}%")
        
        with col2:
            st.write("**Volatility Risk:**")
            if portfolio_volatility > 25:
                st.error(f"High volatility: {portfolio_volatility:.1f}%")
            elif portfolio_volatility > 15:
                st.warning(f"Moderate volatility: {portfolio_volatility:.1f}%")
            else:
                st.success(f"Low volatility: {portfolio_volatility:.1f}%")
