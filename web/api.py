"""
FastAPI backend for MarketResearcher web interface.
"""

import asyncio
import sys
import uuid
import logging
import math
import numpy as np
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
import uuid
import pandas as pd

# Add parent directory to path for imports
from pathlib import Path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Change to parent directory so relative paths work correctly
import os
os.chdir(parent_dir)

# Import MarketResearcher components
from main import MarketResearcherCLI
from portfolio.manager import PortfolioManager
from data.market_data import MarketDataManager
from prediction.engine import PredictionEngine
from llm.local_client import LocalLLMClient
from config.settings import MarketResearcherConfig
from web.auth import UserManager, create_access_token, verify_token
from web.token_usage import token_tracker

logger = logging.getLogger(__name__)

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    username: str

class AnalysisRequest(BaseModel):
    asset_type: str  # "stock", "crypto", "forex", "commodity", "bonds", "derivatives"
    symbol: str
    exchange: Optional[str] = None

class AnalysisResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Global MarketResearcher instance
market_researcher: Optional[MarketResearcherCLI] = None
analysis_tasks: Dict[str, Dict[str, Any]] = {}

def clean_nan_values(obj):
    """Recursively clean NaN values from nested dictionaries and lists for JSON serialization."""
    if isinstance(obj, dict):
        return {key: clean_nan_values(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, np.floating):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif hasattr(obj, 'isnull') and obj.isnull():  # pandas NaType
        return None
    else:
        return obj

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events."""
    global market_researcher
    # Startup
    try:
        market_researcher = MarketResearcherCLI()
        await market_researcher.initialize()
        print("✓ MarketResearcher API initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize MarketResearcher: {e}")
    
    yield
    
    # Shutdown
    if market_researcher:
        await market_researcher._cleanup()

# FastAPI app
app = FastAPI(
    title="MarketResearcher API",
    description="Remote access API for MarketResearcher platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for external access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication
security = HTTPBearer()
user_manager = UserManager()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user."""
    username = verify_token(credentials.credentials)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = user_manager.get_user(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    user = user_manager.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=480)  # 8 hours
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        username=user["username"]
    )

@app.get("/auth/verify")
async def verify_auth(current_user: dict = Depends(get_current_user)):
    """Verify authentication status."""
    return {"authenticated": True, "username": current_user["username"]}

@app.post("/auth/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Change user password."""
    try:
        # Verify current password
        if not user_manager.authenticate_user(current_user["username"], request.current_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        if len(request.new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 6 characters long"
            )
        
        # Change password
        success = user_manager.change_password(current_user["username"], request.new_password)
        
        if success:
            return {"success": True, "message": "Password changed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )

@app.get("/user/token-usage")
async def get_user_token_usage(current_user: dict = Depends(get_current_user), days: int = 30):
    """Get token usage statistics for the current user."""
    try:
        usage_stats = token_tracker.get_user_usage(current_user["username"], days)
        limits_check = token_tracker.check_limits(current_user["username"])
        
        return {
            "success": True,
            "usage_stats": usage_stats,
            "limits": limits_check
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get token usage: {str(e)}")

@app.get("/user/activity")
async def get_user_activity(current_user: dict = Depends(get_current_user)):
    """Get recent activity for current user only."""
    try:
        username = current_user['username']
        
        # Get user-specific activity from token tracker
        user_usage = token_tracker.get_user_usage(username)
        activities = []
        
        # Convert usage data to activity format
        if user_usage and 'recent_sessions' in user_usage:
            for session in user_usage['recent_sessions'][-10:]:  # Last 10 activities
                activities.append({
                    "Time": session.get('timestamp', datetime.now().strftime("%H:%M")),
                    "User": username,
                    "Action": session.get('analysis_type', 'Analysis').replace('_', ' ').title(),
                    "Symbol": session.get('symbol', '-'),
                    "Status": "✅ Success"
                })
        
        # If no activities, show current session
        if not activities:
            activities = [{
                "Time": datetime.now().strftime("%H:%M"),
                "User": username,
                "Action": "Dashboard View",
                "Symbol": "-",
                "Status": "✅ Success"
            }]
        
        return {"activities": activities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user activity: {str(e)}")

@app.post("/user/token-limits")
async def set_user_token_limits(
    limits_request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Set token usage limits for current user."""
    try:
        username = current_user['username']
        daily_limit = limits_request.get('daily_limit', 10000)
        monthly_limit = limits_request.get('monthly_limit', 100000)
        
        # Set limits in token tracker
        token_tracker.set_user_limits(username, daily_limit, monthly_limit)
        
        return {"success": True, "message": "Token limits updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set token limits: {str(e)}")

@app.get("/admin/all-users-usage")
async def get_all_users_usage(current_user: dict = Depends(get_current_user)):
    """Get token usage statistics for all users (admin only)."""
    try:
        # Check if user is admin (you might want to implement proper role checking)
        if current_user.get('username') != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        all_usage = token_tracker.get_all_users_usage()
        return {"users": all_usage}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get all users usage: {str(e)}")

@app.get("/admin/active-users")
async def get_active_users(current_user: dict = Depends(get_current_user)):
    """Get currently active users based on recent API activity (admin only)."""
    try:
        # Check if user is admin
        if current_user.get('username') != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get active connections from netstat
        import subprocess
        import re
        from datetime import datetime, timedelta
        
        # Check API connections (port 8000)
        api_cmd = "netstat -an | grep :8000 | grep ESTABLISHED | wc -l"
        api_connections = int(subprocess.check_output(api_cmd, shell=True).decode('utf-8').strip())
        
        # Check Streamlit connections (port 8501)
        ui_cmd = "netstat -an | grep :8501 | grep ESTABLISHED | wc -l"
        ui_connections = int(subprocess.check_output(ui_cmd, shell=True).decode('utf-8').strip())
        
        # Get recent user activity from token tracker
        recent_activity = []
        current_time = datetime.now()
        active_threshold = timedelta(minutes=15)  # Consider active if activity within 15 minutes
        
        if hasattr(token_tracker, 'sessions'):
            for username, user_data in token_tracker.sessions.items():
                last_activity = user_data.get('last_activity')
                if last_activity and (current_time - last_activity) < active_threshold:
                    recent_activity.append({
                        "username": username,
                        "last_activity": last_activity.isoformat(),
                        "session_id": user_data.get('current_session_id', 'unknown'),
                        "ip_address": user_data.get('ip_address', 'unknown')
                    })
        
        return {
            "active_users": len(recent_activity),
            "api_connections": api_connections,
            "ui_connections": ui_connections,
            "recent_activity": recent_activity,
            "timestamp": current_time.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active users: {str(e)}")

@app.post("/analysis/stock")
async def analyze_stock(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Analyze a stock symbol."""
    if not market_researcher:
        raise HTTPException(status_code=500, detail="MarketResearcher not initialized")
    
    task_id = f"{current_user['username']}_{datetime.now().timestamp()}"
    analysis_tasks[task_id] = {"status": "running", "result": None, "error": None}
    
    async def run_analysis():
        try:
            # Use actual MarketResearcher stock analyzer
            if not market_researcher.stock_analyzer:
                raise Exception("Stock analyzer not available")
            
            # Capture the analysis output by temporarily redirecting
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            # Create a mock symbol selection for the analyzer
            original_questionary = __import__('questionary')
            
            class MockQuestionary:
                @staticmethod
                def select(prompt, choices):
                    class MockChoice:
                        async def ask_async(self):
                            # Find the symbol in choices or return custom option
                            for choice in choices:
                                if request.symbol.upper() in choice.upper():
                                    return choice
                            return "custom - Enter custom symbol"
                    return MockChoice()
                
                @staticmethod
                def text(prompt, default=""):
                    class MockText:
                        async def ask_async(self):
                            return request.symbol.upper()
                    return MockText()
            
            # Temporarily replace questionary for automated analysis
            import sys
            questionary_module = sys.modules.get('questionary')
            if questionary_module:
                original_select = questionary_module.select
                original_text = questionary_module.text
                questionary_module.select = MockQuestionary.select
                questionary_module.text = MockQuestionary.text
            
            try:
                # Get stock data directly from the analyzer's data sources
                symbol = request.symbol.upper()
                
                # Use the stock analyzer's data fetching methods
                stock_info = market_researcher.stock_analyzer.stocks_db.get_stock_by_symbol(symbol)
                
                # Determine if US stock or international
                is_us_stock = False
                if stock_info:
                    is_us_stock = stock_info.exchange in market_researcher.stock_analyzer.us_exchanges
                
                # Fetch actual market data
                analysis_data, data_source = await market_researcher.stock_analyzer._fetch_stock_data(symbol, is_us_stock)
                
                if analysis_data and 'error' not in analysis_data:
                    # Extract key data from the analysis
                    profile = analysis_data.get('profile', {})
                    quote = analysis_data.get('quote', {})
                    financials_raw = analysis_data.get('financials', {})
                    # Handle both MarketDataManager format and legacy Finnhub metric format
                    if 'metric' in financials_raw:
                        # Legacy Finnhub format
                        financials = financials_raw.get('metric', {})
                    else:
                        # MarketDataManager format (already processed)
                        financials = financials_raw
                    recommendations = analysis_data.get('recommendations', [])
                    
                    # Use prediction engine for multi-agent analysis including trading
                    try:
                        # Prepare data for prediction engine analysis
                        llm_data = {
                            'symbol': symbol,
                            'profile': profile,
                            'quote': quote,
                            'news_count': len(analysis_data.get('news', [])),
                            'recent_news': analysis_data.get('news', [])[:3],
                            'financials': financials,
                            'recommendations': recommendations[0] if recommendations else {},
                            'insider_transactions': analysis_data.get('insider_transactions', [])[:10]
                        }
                        
                        # Run prediction using the prediction engine
                        prediction = await market_researcher.prediction_engine.predict(symbol, analysis_data)
                        
                        # Generate enhanced trading signal directly using UnifiedSignalGenerator
                        enhanced_signal = None
                        try:
                            from analyzers.signal_generator import UnifiedSignalGenerator
                            signal_generator = UnifiedSignalGenerator()
                            enhanced_signal = signal_generator.generate_enhanced_trading_signal(
                                symbol, analysis_data, position_size=100
                            )
                        except Exception as e:
                            logger.warning(f"Failed to generate enhanced signal for {symbol}: {e}")
                        
                        # Track token usage for prediction engine analysis
                        if prediction and prediction.get("success", False):
                            estimated_prompt_tokens = len(str(llm_data)) // 4  # Rough estimate
                            estimated_completion_tokens = 1200  # Higher for multi-agent analysis
                            
                            token_tracker.track_usage(
                                username=current_user['username'],
                                analysis_type="stock_analysis",
                                prompt_tokens=estimated_prompt_tokens,
                                completion_tokens=estimated_completion_tokens,
                                symbol=symbol,
                                session_id=task_id
                            )
                    
                        if prediction and prediction.get("success", False):
                            # Get currency from stock info
                            currency = 'USD'  # Default
                            if stock_info and stock_info.currency:
                                currency = stock_info.currency
                            
                            # Return full prediction result with trading agent data
                            result = {
                                "symbol": symbol,
                                "analysis_type": "stock",
                                "timestamp": datetime.now().isoformat(),
                                "status": "completed",
                                "data_source": data_source,
                                "company_name": profile.get('name', symbol),
                                "industry": profile.get('finnhubIndustry', 'N/A'),
                                "market_cap": profile.get('marketCapitalization', 0),
                                "website": profile.get('weburl', ''),
                                "current_price": quote.get('c', 0),
                                "change": quote.get('d', 0),
                                "change_percent": quote.get('dp', 0),
                                "high": quote.get('h', 0),
                                "low": quote.get('l', 0),
                                "previous_close": quote.get('pc', 0),
                                # Use MarketDataManager financial metrics (IB → Finnhub → Yahoo priority)
                                "pe_ratio": financials.get('pe_ratio', 'N/A'),
                                "pb_ratio": financials.get('pb_ratio', 'N/A'),
                                "roa": financials.get('roa', 'N/A'),
                                "roe": financials.get('roe', 'N/A'),
                                "revenue_growth": financials.get('revenue_growth', 'N/A'),
                                "eps": financials.get('eps', 'N/A'),
                                "analyst_recommendations": recommendations[0] if recommendations else {},
                                "news_count": len(analysis_data.get('news', [])),
                                "success": True,
                                "final_decision": prediction.get("final_decision", {}),
                                "confidence": prediction.get("confidence", 0),
                                "risk_assessment": prediction.get("risk_assessment", 50),
                                "agent_results": prediction.get("agent_results", {}),
                                "market_context": prediction.get("market_context", {}),
                                "enhanced_signal": enhanced_signal,
                                "currency": currency,
                                "mock_data": False
                            }
                        else:
                            # Get currency from stock info
                            currency = 'USD'  # Default
                            if stock_info and stock_info.currency:
                                currency = stock_info.currency
                            
                            # Fallback if prediction fails
                            result = {
                                "symbol": symbol,
                                "analysis_type": "stock",
                                "timestamp": datetime.now().isoformat(),
                                "status": "completed",
                                "data_source": data_source,
                                "company_name": profile.get('name', symbol),
                                "industry": profile.get('finnhubIndustry', 'N/A'),
                                "market_cap": profile.get('marketCapitalization', 0),
                                "website": profile.get('weburl', ''),
                                "current_price": quote.get('c', 0),
                                "change": quote.get('d', 0),
                                "change_percent": quote.get('dp', 0),
                                "high": quote.get('h', 0),
                                "low": quote.get('l', 0),
                                "previous_close": quote.get('pc', 0),
                                # Use MarketDataManager financial metrics (IB → Finnhub → Yahoo priority)
                                "pe_ratio": financials.get('pe_ratio', 'N/A'),
                                "pb_ratio": financials.get('pb_ratio', 'N/A'),
                                "roa": financials.get('roa', 'N/A'),
                                "roe": financials.get('roe', 'N/A'),
                                "revenue_growth": financials.get('revenue_growth', 'N/A'),
                                "eps": financials.get('eps', 'N/A'),
                                "analyst_recommendations": recommendations[0] if recommendations else {},
                                "news_count": len(analysis_data.get('news', [])),
                                "currency": currency,
                                "error": f"Prediction failed: {prediction.get('error', 'Unknown error') if prediction else 'Prediction engine unavailable'}",
                                "mock_data": False
                            }
                    except Exception as e:
                        print(f"Prediction engine analysis failed: {e}")
                        # Create fallback result without prediction data
                        result = {
                            "symbol": symbol,
                            "analysis_type": "stock",
                            "timestamp": datetime.now().isoformat(),
                            "status": "completed",
                            "data_source": data_source,
                            "company_name": profile.get('name', symbol),
                            "industry": profile.get('finnhubIndustry', 'N/A'),
                            "market_cap": profile.get('marketCapitalization', 0),
                            "website": profile.get('weburl', ''),
                            "current_price": quote.get('c', 0),
                            "change": quote.get('d', 0),
                            "change_percent": quote.get('dp', 0),
                            "high": quote.get('h', 0),
                            "low": quote.get('l', 0),
                            "previous_close": quote.get('pc', 0),
                            "pe_ratio": financials.get('peNormalizedAnnual', 'N/A'),
                            "pb_ratio": financials.get('pbAnnual', 'N/A'),
                            "roa": financials.get('roaAnnual', 'N/A'),
                            "roe": financials.get('roeAnnual', 'N/A'),
                            "revenue_growth": financials.get('revenueGrowthAnnual', 'N/A'),
                            "eps": financials.get('epsAnnual', 'N/A'),
                            "analyst_recommendations": recommendations[0] if recommendations else {},
                            "news_count": len(analysis_data.get('news', [])),
                            "error": f"Analysis failed: {str(e)}",
                            "mock_data": False
                        }
                    except Exception as e:
                        print(f"Prediction engine analysis failed: {e}")
                        # Create legacy AI analysis as fallback
                        ai_analysis = {"error": f"AI analysis failed: {str(e)}"}
                        
                        result = {
                            "symbol": symbol,
                            "analysis_type": "stock",
                            "timestamp": datetime.now().isoformat(),
                            "status": "completed",
                            "data_source": data_source,
                            "company_name": profile.get('name', symbol),
                            "industry": profile.get('finnhubIndustry', 'N/A'),
                            "market_cap": profile.get('marketCapitalization', 0),
                            "website": profile.get('weburl', ''),
                            "current_price": quote.get('c', 0),
                            "change": quote.get('d', 0),
                            "change_percent": quote.get('dp', 0),
                            "high": quote.get('h', 0),
                            "low": quote.get('l', 0),
                            "previous_close": quote.get('pc', 0),
                            "pe_ratio": financials.get('peNormalizedAnnual', 'N/A'),
                            "pb_ratio": financials.get('pbAnnual', 'N/A'),
                            "roa": financials.get('roaAnnual', 'N/A'),
                            "roe": financials.get('roeAnnual', 'N/A'),
                            "revenue_growth": financials.get('revenueGrowthAnnual', 'N/A'),
                            "eps": financials.get('epsAnnual', 'N/A'),
                            "analyst_recommendations": recommendations[0] if recommendations else {},
                            "news_count": len(analysis_data.get('news', [])),
                            "ai_analysis": ai_analysis,
                            "mock_data": False
                        }
                else:
                    # Fallback if data fetch fails
                    result = {
                        "symbol": symbol,
                        "analysis_type": "stock",
                        "timestamp": datetime.now().isoformat(),
                        "status": "failed",
                        "error": analysis_data.get('error', 'No data available'),
                        "message": f"Could not fetch data for {symbol}",
                        "mock_data": False
                    }
                
            finally:
                # Restore original questionary functions
                if questionary_module:
                    questionary_module.select = original_select
                    questionary_module.text = original_text
            
            analysis_tasks[task_id]["status"] = "completed"
            analysis_tasks[task_id]["result"] = result
            
        except Exception as e:
            analysis_tasks[task_id]["status"] = "error"
            analysis_tasks[task_id]["result"] = None
            analysis_tasks[task_id]["error"] = str(e)
    
    background_tasks.add_task(run_analysis)
    return {"task_id": task_id, "status": "started"}

@app.post("/analysis/crypto")
async def analyze_crypto(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Analyze a cryptocurrency symbol."""
    if not market_researcher:
        raise HTTPException(status_code=500, detail="MarketResearcher not initialized")
    
    task_id = f"{current_user['username']}_{datetime.now().timestamp()}"
    analysis_tasks[task_id] = {"status": "running", "result": None, "error": None}
    
    async def run_analysis():
        try:
            # Use actual MarketResearcher crypto analyzer
            if not market_researcher.crypto_analyzer:
                raise Exception("Crypto analyzer not available")
            
            # Create mock questionary responses for automated analysis
            import sys
            questionary_module = sys.modules.get('questionary')
            
            class MockQuestionary:
                @staticmethod
                def select(prompt, choices):
                    class MockChoice:
                        async def ask_async(self):
                            # Auto-select based on symbol or return first choice
                            if "symbol" in prompt.lower():
                                for choice in choices:
                                    if request.symbol.upper() in choice.upper():
                                        return choice
                                return choices[0] if choices else "BTCUSDT"
                            return choices[0] if choices else ""
                    return MockChoice()
                
                @staticmethod
                def text(prompt, default=""):
                    class MockText:
                        async def ask_async(self):
                            return request.symbol.upper()
                    return MockText()
            
            # Temporarily replace questionary for automated analysis
            if questionary_module:
                original_select = questionary_module.select
                original_text = questionary_module.text
                questionary_module.select = MockQuestionary.select
                questionary_module.text = MockQuestionary.text
            
            # Get symbol from request
            symbol = request.symbol.upper()
            exchange = request.exchange
            
            # Use crypto analyzer for proper data enrichment
            try:
                # Get enriched data using crypto analyzer's data collection method
                market_overview = await market_researcher.market_data.get_market_overview([symbol])
                current_price = market_overview.get(symbol, {}).get('price', 0)
                
                # Get fresh ticker data from public API that doesn't require API keys
                ticker_data = None
                try:
                    # Import the public crypto API
                    from data.public_crypto_api import PublicCryptoAPI
                    
                    # Create a public crypto API client
                    public_api = PublicCryptoAPI()
                    
                    # Get ticker data from public API
                    ticker_data = public_api.get_ticker_data(symbol)
                    
                    if ticker_data and 'price' in ticker_data:
                        current_price = float(ticker_data['price'])
                        print(f"[DEBUG] Using public API price for {symbol}: ${current_price}")
                except Exception as e:
                    print(f"[DEBUG] Could not get public API data: {e}")
                
                # Get 60-day historical data with technical indicators (same as CLI)
                historical_data = await market_researcher.market_data.get_symbol_data(
                    symbol, timeframe='1d', limit=60, include_indicators=True
                )
                
                # Debug: Log the historical data structure
                print(f"[DEBUG] Historical data shape: {historical_data.shape if not historical_data.empty else 'Empty'}")
                if not historical_data.empty:
                    print(f"[DEBUG] Historical data columns: {list(historical_data.columns)}")
                    latest_row = historical_data.iloc[-1]
                    print(f"[DEBUG] Latest indicators - RSI: {latest_row.get('rsi', 'N/A')}, MACD: {latest_row.get('macd_line', 'N/A')}")
                
                # Create enriched data structure
                enriched_data = {
                    'current_price': current_price,
                    'historical_data': historical_data,
                    'market_overview': market_overview.get(symbol, {})
                }
                
                # Add ticker data if available
                if ticker_data:
                    enriched_data['ticker'] = ticker_data
                    # Add price change data directly from ticker
                    enriched_data['price_change'] = float(ticker_data.get('priceChange', 0))
                    enriched_data['price_change_percent'] = float(ticker_data.get('priceChangePercent', 0))
                    enriched_data['volume'] = float(ticker_data.get('volume', 0))
                    enriched_data['quote_volume'] = float(ticker_data.get('quoteVolume', 0))
                
                # Run crypto prediction with enriched data
                prediction = await market_researcher.prediction_engine.predict(symbol, enriched_data=enriched_data)
                
                if prediction and prediction.get("success"):
                    # Track token usage for crypto analysis
                    estimated_prompt_tokens = 600  # Typical crypto analysis prompt
                    estimated_completion_tokens = 1000  # Typical completion for crypto analysis
                    
                    token_tracker.track_usage(
                        username=current_user['username'],
                        analysis_type="crypto_analysis",
                        prompt_tokens=estimated_prompt_tokens,
                        completion_tokens=estimated_completion_tokens,
                        symbol=symbol,
                        session_id=task_id
                    )
                    
                    # Get real price data from Binance using existing client (force refresh to bypass cache)
                    ticker_data = None
                    if market_researcher.binance_client:
                        ticker_data = market_researcher.binance_client.get_24hr_ticker(symbol, force_refresh=True)
                    
                    current_price = float(ticker_data.get("price", 0)) if ticker_data else 0
                    change_24h = float(ticker_data.get("priceChange", 0)) if ticker_data else 0
                    change_percent = float(ticker_data.get("priceChangePercent", 0)) if ticker_data else 0
                    volume = float(ticker_data.get("quoteVolume", 0)) if ticker_data else 0  # Use quoteVolume for USD volume
                    
                    # Return full prediction result with trading agent data
                    # Update market_context with real Binance data
                    market_context = prediction.get("market_context", {})
                    market_context.update({
                        "current_price": current_price,
                        "price_change": change_24h,
                        "price_change_percent": change_percent,
                        "volume": volume
                    })
                    
                    result = {
                        "symbol": symbol,
                        "exchange": exchange,
                        "current_price": current_price,
                        "change_24h": change_24h,
                        "change_percent_24h": change_percent,
                        "volume_24h": volume,
                        "success": True,
                        "final_decision": prediction.get("final_decision", {}),
                        "confidence": prediction.get("confidence", 0),
                        "risk_assessment": prediction.get("risk_assessment", 50),
                        "agent_results": prediction.get("agent_results", {}),
                        "market_context": market_context,
                        "timestamp": datetime.now().isoformat(),
                        "mock_data": False
                    }
                else:
                    # Fallback if prediction fails
                    result = {
                        "symbol": symbol,
                        "exchange": exchange,
                        "error": f"Prediction failed: {prediction.get('error', 'Unknown error')}",
                        "timestamp": datetime.now().isoformat(),
                        "mock_data": False
                    }
                    
            except Exception as e:
                # Final fallback with error message
                result = {
                    "symbol": symbol,
                    "exchange": exchange,
                    "error": f"Crypto analysis failed: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                    "mock_data": False
                }
            
            analysis_tasks[task_id]["status"] = "completed"
            analysis_tasks[task_id]["result"] = result
            
        except Exception as e:
            analysis_tasks[task_id]["status"] = "error"
            analysis_tasks[task_id]["result"] = None
            analysis_tasks[task_id]["error"] = str(e)
        finally:
            # Restore original questionary functions
            if questionary_module:
                questionary_module.select = original_select
                questionary_module.text = original_text
    
    background_tasks.add_task(run_analysis)
    return {"task_id": task_id, "status": "started"}

@app.post("/analysis/bonds")
async def analyze_bonds(analysis_request: dict, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Analyze bonds and gilts using AI/LLM."""
    
    task_id = str(uuid.uuid4())
    analysis_tasks[task_id] = {
        "status": "running",
        "result": None,
        "error": None,
        "created_at": datetime.now()
    }
    
    async def run_analysis():
        try:
            # Simulate analysis delay
            await asyncio.sleep(2)
            
            analysis_type = analysis_request.get("analysis_type", "market_bonds")
            
            # Initialize bonds analyzer if not already done
            if not hasattr(market_researcher, 'bonds_analyzer') or not market_researcher.bonds_analyzer:
                from analyzers.bonds_analyzer import BondsAnalyzer
                market_researcher.bonds_analyzer = BondsAnalyzer(
                    llm_client=market_researcher.llm_client,
                    config=market_researcher.config
                )
            
            result = {}
            
            if analysis_type == "market_bonds":
                market = analysis_request.get("market", "US_TREASURY")
                period = analysis_request.get("period", "1mo")
                
                # Get market bonds data
                bonds_data = await market_researcher.bonds_analyzer.analyze_market_bonds(market, period)
                
                if bonds_data.get("success", False):
                    # Run AI analysis and track token usage
                    ai_result = await market_researcher.bonds_analyzer.analyze_bonds_with_ai(bonds_data)
                    ai_analysis = ai_result.get("ai_analysis", "") if ai_result.get("success") else ai_result.get("error", "AI analysis failed")
                    
                    # Track token usage for bonds analysis
                    if ai_result.get("success"):
                        token_tracker.track_usage(
                            username=current_user['username'],
                            analysis_type="bonds_analysis",
                            prompt_tokens=500,
                            completion_tokens=600,
                            symbol=market,
                            session_id=task_id
                        )
                    
                    result = {
                        "analysis_type": "market_bonds",
                        "market": market,
                        "summary": bonds_data.get("summary", {}),
                        "bonds": bonds_data.get("bonds", []),
                        "ai_analysis": ai_analysis,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    result = {"error": bonds_data.get("error", "Failed to fetch bonds data")}
            
            elif analysis_type == "yield_curve":
                country = analysis_request.get("country", "US")
                
                # Get yield curve data
                curve_data = await market_researcher.bonds_analyzer.get_yield_curve_data(country)
                
                if curve_data.get("success", False):
                    # Run AI analysis
                    ai_result = await market_researcher.bonds_analyzer.analyze_yield_curve_with_ai(curve_data)
                    ai_analysis = ai_result.get("ai_analysis", "") if ai_result.get("success") else ai_result.get("error", "AI analysis failed")
                    
                    result = {
                        "analysis_type": "yield_curve",
                        "country": country,
                        "curve_shape": ai_result.get("curve_shape", "Unknown"),
                        "slope": ai_result.get("slope", 0),
                        "curve_data": curve_data.get("curve_data", []),
                        "ai_analysis": ai_analysis,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    result = {"error": curve_data.get("error", "Failed to fetch yield curve data")}
            
            elif analysis_type == "international_comparison":
                maturity = analysis_request.get("maturity", "10Y")
                
                # Get international comparison data
                comparison_data = await market_researcher.bonds_analyzer.compare_international_bonds(maturity)
                
                if comparison_data.get("success", False):
                    # Run AI analysis
                    ai_result = await market_researcher.bonds_analyzer.analyze_international_bonds_with_ai(comparison_data)
                    ai_analysis = ai_result.get("ai_analysis", "") if ai_result.get("success") else ai_result.get("error", "AI analysis failed")
                    
                    result = {
                        "analysis_type": "international_comparison",
                        "maturity": maturity,
                        "comparison": comparison_data.get("comparison", []),
                        "benchmark_yield": ai_result.get("benchmark_yield", 0),
                        "ai_analysis": ai_analysis,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    result = {"error": comparison_data.get("error", "Failed to fetch international bonds data")}
            
            elif analysis_type == "bond_trends":
                market = analysis_request.get("market", "US_TREASURY")
                period = analysis_request.get("period", "3mo")
                
                # Get bond trends data
                trends_data = await market_researcher.bonds_analyzer.analyze_bond_trends(market, period)
                
                if trends_data.get("success", False):
                    # Run AI analysis
                    ai_result = await market_researcher.bonds_analyzer.analyze_bond_trends_with_ai(trends_data)
                    ai_analysis = ai_result.get("ai_analysis", "") if ai_result.get("success") else ai_result.get("error", "AI analysis failed")
                    
                    result = {
                        "analysis_type": "bond_trends",
                        "market": market,
                        "period": period,
                        "market_direction": ai_result.get("market_direction", "Unknown"),
                        "trends_summary": ai_result.get("trends_summary", {}),
                        "trends": trends_data.get("trends", []),
                        "ai_analysis": ai_analysis,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    result = {"error": trends_data.get("error", "Failed to fetch bond trends data")}
            
            else:
                result = {"error": f"Unknown analysis type: {analysis_type}"}
            
            analysis_tasks[task_id]["status"] = "completed"
            analysis_tasks[task_id]["result"] = result
            
        except Exception as e:
            analysis_tasks[task_id]["status"] = "error"
            analysis_tasks[task_id]["error"] = str(e)
    
    # Start the background task
    background_tasks.add_task(run_analysis)
    
    return {
        "success": True,
        "task_id": task_id,
        "message": f"Bonds analysis started"
    }

@app.post("/analysis/derivatives")
async def analyze_derivatives(analysis_request: dict, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Analyze derivatives using AI/LLM."""
    
    task_id = str(uuid.uuid4())
    analysis_tasks[task_id] = {
        "status": "running",
        "result": None,
        "error": None,
        "created_at": datetime.now()
    }
    
    async def run_analysis():
        try:
            # Simulate analysis delay
            await asyncio.sleep(2)
            
            analysis_type = analysis_request.get("analysis_type", "stock_options")
            
            # Initialize derivatives analyzer if not already done
            if not hasattr(market_researcher, 'derivatives_analyzer') or not market_researcher.derivatives_analyzer:
                from analyzers.derivatives_analyzer import DerivativesAnalyzer
                market_researcher.derivatives_analyzer = DerivativesAnalyzer(
                    llm_client=market_researcher.llm_client,
                    config=market_researcher.config
                )
            
            result = {}
            
            if analysis_type == "stock_options":
                symbol = analysis_request.get("symbol", "AAPL")
                expiry_filter = analysis_request.get("expiry_filter")
                
                # Get options data
                options_data = await market_researcher.derivatives_analyzer.analyze_stock_options(symbol, expiry_filter)
                
                if options_data.get("success", False):
                    # Run AI analysis and track token usage
                    ai_result = await market_researcher.derivatives_analyzer.analyze_options_with_ai(options_data)
                    ai_analysis = ai_result.get("ai_analysis", "") if ai_result.get("success") else ai_result.get("error", "AI analysis failed")
                    
                    # Track token usage for derivatives analysis
                    if ai_result.get("success"):
                        token_tracker.track_usage(
                            username=current_user['username'],
                            analysis_type="derivatives_analysis",
                            prompt_tokens=400,
                            completion_tokens=700,
                            symbol=symbol,
                            session_id=task_id
                        )
                    
                    result = {
                        "analysis_type": "stock_options",
                        "symbol": symbol,
                        "current_price": options_data.get("current_price", 0),
                        "options_data": options_data.get("options_data", []),
                        "total_options": options_data.get("total_options", 0),
                        "ai_analysis": ai_analysis,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    result = {"error": options_data.get("error", "Failed to fetch options data")}
            
            elif analysis_type == "futures":
                category = analysis_request.get("category", "INDEX_FUTURES")
                
                # Get futures data based on category
                if category == "INDEX_FUTURES":
                    futures_data = await market_researcher.derivatives_analyzer.analyze_index_futures(category)
                elif category == "CURRENCY_DERIVATIVES":
                    futures_data = await market_researcher.derivatives_analyzer.analyze_currency_derivatives()
                elif category == "RATES_DERIVATIVES":
                    futures_data = await market_researcher.derivatives_analyzer.analyze_rates_derivatives()
                elif category == "CRYPTO_DERIVATIVES":
                    futures_data = await market_researcher.derivatives_analyzer.analyze_crypto_derivatives()
                else:
                    futures_data = await market_researcher.derivatives_analyzer.analyze_index_futures(category)
                
                if futures_data.get("success", False):
                    # Run AI analysis
                    ai_result = await market_researcher.derivatives_analyzer.analyze_futures_with_ai(futures_data, category)
                    ai_analysis = ai_result.get("ai_analysis", "") if ai_result.get("success") else ai_result.get("error", "AI analysis failed")
                    
                    result = {
                        "analysis_type": "futures",
                        "category": category,
                        "futures": futures_data.get("futures", []),
                        "total_contracts": futures_data.get("total_contracts", 0),
                        "ai_analysis": ai_analysis,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    result = {"error": futures_data.get("error", "Failed to fetch futures data")}
            
            elif analysis_type == "volatility_surface":
                symbol = analysis_request.get("symbol", "SPY")
                
                # Get volatility surface data
                vol_data = await market_researcher.derivatives_analyzer.get_volatility_surface(symbol)
                
                if vol_data.get("success", False):
                    # Run AI analysis
                    ai_result = await market_researcher.derivatives_analyzer.analyze_volatility_with_ai(vol_data)
                    ai_analysis = ai_result.get("ai_analysis", "") if ai_result.get("success") else ai_result.get("error", "AI analysis failed")
                    
                    result = {
                        "analysis_type": "volatility_surface",
                        "symbol": symbol,
                        "current_price": vol_data.get("current_price", 0),
                        "volatility_surface": vol_data.get("volatility_surface", []),
                        "ai_analysis": ai_analysis,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    result = {"error": vol_data.get("error", "Failed to fetch volatility data")}
            
            else:
                result = {"error": f"Unknown analysis type: {analysis_type}"}
            
            analysis_tasks[task_id]["status"] = "completed"
            analysis_tasks[task_id]["result"] = result
            
        except Exception as e:
            analysis_tasks[task_id]["status"] = "error"
            analysis_tasks[task_id]["error"] = str(e)
    
    background_tasks.add_task(run_analysis)
    return {"task_id": task_id, "status": "started"}

@app.post("/analysis/forex")
async def analyze_forex(analysis_request: dict, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Analyze forex pair using AI/LLM."""
    
    task_id = str(uuid.uuid4())
    analysis_tasks[task_id] = {
        "status": "running",
        "result": None,
        "error": None,
        "created_at": datetime.now()
    }
    
    async def run_analysis():
        try:
            # Simulate analysis delay
            await asyncio.sleep(2)
            
            symbol = analysis_request.get("symbol", "EURUSD")
            broker = analysis_request.get("broker", "OANDA")
            
            # Parse currency pair
            if len(symbol) == 6:
                base_currency = symbol[:3]
                quote_currency = symbol[3:]
            else:
                base_currency = "EUR"
                quote_currency = "USD"
            
            # Use real forex analysis from MarketResearcher
            try:
                # Format symbol for forex analyzer (add slash if needed)
                formatted_symbol = symbol
                if "/" not in symbol and len(symbol) == 6:
                    formatted_symbol = f"{symbol[:3]}/{symbol[3:]}"
                
                # Create a mock request object for the forex analyzer
                class MockRequest:
                    def __init__(self):
                        pass
                
                # Initialize forex analyzer if not already done
                if not hasattr(market_researcher, 'forex_analyzer') or not market_researcher.forex_analyzer:
                    from analyzers.forex_analyzer import ForexAnalyzer
                    market_researcher.forex_analyzer = ForexAnalyzer(
                        polygon_client=getattr(market_researcher, 'polygon_client', None),
                        llm_client=market_researcher.llm_client,
                        config=market_researcher.config
                    )
                
                # Run forex analysis
                forex_data = await market_researcher.forex_analyzer._fetch_forex_data(formatted_symbol)
                
                if 'error' not in forex_data:
                    # Extract real forex data
                    quote = forex_data.get('quote', {})
                    daily_data = forex_data.get('daily_data', [])
                    
                    # Get current price and calculate metrics
                    current_price = quote.get('price', quote.get('p', 0))
                    if not current_price and daily_data:
                        current_price = daily_data[0].get('c', 0)
                    
                    # Calculate change
                    change = 0
                    change_percent = 0
                    high = current_price
                    low = current_price
                    previous_close = current_price
                    
                    if daily_data and len(daily_data) >= 2:
                        previous_close = daily_data[1].get('c', current_price)
                        change = current_price - previous_close
                        if previous_close > 0:
                            change_percent = (change / previous_close) * 100
                        
                        # Get high/low from latest day
                        latest_day = daily_data[0]
                        high = latest_day.get('h', current_price)
                        low = latest_day.get('l', current_price)
                    
                    # Run AI analysis
                    llm_data = {
                        'symbol': formatted_symbol,
                        'quote': quote,
                        'daily_data': daily_data[:10],
                        'hourly_data': forex_data.get('hourly_data', [])[:24],
                        'market_status': forex_data.get('market_status', {}),
                        'news': forex_data.get('news', [])[:3]
                    }
                    
                    ai_analysis = {}
                    try:
                        ai_result = await market_researcher.forex_analyzer._run_forex_llm_analysis(formatted_symbol, llm_data)
                        if ai_result.get("success", False):
                            agents_analysis = ai_result.get("agents_analysis", {})
                            ai_analysis = {
                                "investment_signal": ai_result.get("final_signal", "NEUTRAL"),
                                "confidence_score": ai_result.get("confidence", 0),
                                "technical_analysis": agents_analysis.get("technical", {}).get("analysis", ""),
                                "fundamental_analysis": agents_analysis.get("fundamental", {}).get("analysis", ""),
                                "risk_analysis": agents_analysis.get("risk", {}).get("analysis", ""),
                                "final_recommendation": ai_result.get("final_recommendation", "")
                            }
                    except Exception as e:
                        print(f"AI analysis failed: {e}")
                        ai_analysis = {"error": f"AI analysis failed: {str(e)}"}
                    
                    result = {
                        "symbol": symbol,
                        "pair_name": f"{base_currency}/{quote_currency}",
                        "base_currency": base_currency,
                        "quote_currency": quote_currency,
                        "broker": broker,
                        "current_price": current_price,
                        "change": change,
                        "change_percent": change_percent,
                        "high": high,
                        "low": low,
                        "previous_close": previous_close,
                        "spread": quote.get('spread', 0.0001),
                        "trading_session": forex_data.get('market_status', {}).get('currencies', {}).get('fx', 'Active'),
                        "ai_analysis": ai_analysis,
                        "timestamp": datetime.now().isoformat(),
                        "mock_data": False
                    }
                else:
                    # Fallback to mock data if real data fails
                    result = {
                        "symbol": symbol,
                        "pair_name": f"{base_currency}/{quote_currency}",
                        "base_currency": base_currency,
                        "quote_currency": quote_currency,
                        "broker": broker,
                        "current_price": 1.0000,
                        "change": 0.0000,
                        "change_percent": 0.000,
                        "high": 1.0000,
                        "low": 1.0000,
                        "previous_close": 1.0000,
                        "spread": 0.0001,
                        "trading_session": "Active",
                        "error": forex_data.get('error', 'Data unavailable'),
                        "timestamp": datetime.now().isoformat(),
                        "mock_data": True
                    }
                
            except Exception as e:
                result = {
                    "symbol": symbol,
                    "pair_name": f"{base_currency}/{quote_currency}",
                    "base_currency": base_currency,
                    "quote_currency": quote_currency,
                    "broker": broker,
                    "error": f"Analysis failed: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                    "mock_data": False
                }
            
            analysis_tasks[task_id]["status"] = "completed"
            analysis_tasks[task_id]["result"] = result
            
        except Exception as e:
            analysis_tasks[task_id]["status"] = "error"
            analysis_tasks[task_id]["result"] = None
            analysis_tasks[task_id]["error"] = str(e)
    
    background_tasks.add_task(run_analysis)
    return {"task_id": task_id, "status": "started"}

@app.get("/analysis/status/{task_id}")
async def get_analysis_status(task_id: str):
    """Get analysis task status."""
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = analysis_tasks[task_id]
    
    # Clean NaN values from the result before returning
    cleaned_result = clean_nan_values(task["result"]) if task["result"] else None
    
    return {
        "task_id": task_id,
        "status": task["status"],
        "result": cleaned_result,
        "error": task["error"]
    }

@app.get("/portfolio")
async def get_portfolio(current_user: dict = Depends(get_current_user)):
    """Get user portfolio."""
    
    try:
        # Mock portfolio data
        return {
            "success": True,
            "portfolio": {
                "positions": {
                    "AAPL": {"quantity": 10, "avg_price": 150.00, "current_price": 152.34},
                    "BTCUSDT": {"quantity": 0.5, "avg_price": 45000.00, "current_price": 44567.89}
                },
                "cash_balance": 5000.00,
                "total_value": 25000.00,
                "daily_pnl": 234.50
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/portfolio/analyze")
async def analyze_portfolio(portfolio_data: dict, current_user: dict = Depends(get_current_user)):
    """Analyze portfolio using AI/LLM."""
    
    try:
        from llm.local_client import LocalLLMClient
        from config.settings import MarketResearcherConfig
        
        # Initialize LLM client
        config = MarketResearcherConfig()
        llm_client = LocalLLMClient(config)
        
        # Prepare portfolio analysis prompt
        positions = portfolio_data.get("positions", {})
        total_value = portfolio_data.get("total_value", 0)
        
        # Calculate portfolio metrics
        portfolio_summary = []
        total_invested = 0
        current_value = 0
        
        for symbol, pos in positions.items():
            quantity = pos.get("quantity", 0)
            avg_price = pos.get("avg_price", 0)
            current_price = pos.get("current_price", avg_price)
            
            invested = quantity * avg_price
            current = quantity * current_price
            total_invested += invested
            current_value += current
            
            weight = (current / total_value * 100) if total_value > 0 else 0
            pnl = current - invested
            pnl_pct = (pnl / invested * 100) if invested > 0 else 0
            
            portfolio_summary.append(f"- {symbol}: {quantity} shares, Weight: {weight:.1f}%, P&L: {pnl_pct:.2f}%")
        
        # Update total value based on actual calculations
        if current_value > 0:
            total_value = current_value
        
        prompt = f"""
        Analyze the following portfolio and provide investment advice:
        
        Portfolio Summary:
        {chr(10).join(portfolio_summary)}
        
        Total Portfolio Value: ${total_value:,.2f}
        Cash Balance: ${portfolio_data.get('cash_balance', 0):,.2f}
        
        Please provide:
        1. Risk assessment (level, diversification, concentration risk)
        2. Specific recommendations for portfolio optimization
        3. Rebalancing suggestions
        4. Overall portfolio health score (1-10)
        
        Format your response as actionable advice for an investor.
        """
        
        # Get LLM analysis
        messages = [{"role": "user", "content": prompt}]
        response = llm_client.generate_response(messages)
        
        # Parse response into structured format
        analysis_text = response.get("content", "")
        
        # Extract structured recommendations with better parsing
        recommendations = []
        risk_level = "Moderate"
        rebalancing_suggestions = []
        
        # Parse risk level from content
        if "very high" in analysis_text.lower():
            risk_level = "Very High"
        elif "high risk" in analysis_text.lower() or "high concentration" in analysis_text.lower():
            risk_level = "High"
        elif "low risk" in analysis_text.lower():
            risk_level = "Low"
        
        # Extract recommendations from all relevant sections
        lines = analysis_text.split('\n')
        current_section = ""
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Track current section
            if line.startswith("#") or line.startswith("##"):
                current_section = line.lower()
                continue
            
            # Extract table content with actionable recommendations
            if "|" in line and len(line.split("|")) >= 3:
                parts = [p.strip() for p in line.split("|")]
                
                # Skip table headers
                if any(header in parts[0].lower() for header in ["goal", "item", "dimension", "step", "metric"]):
                    continue
                
                # Extract meaningful recommendations from tables
                if len(parts) >= 3 and parts[1]:
                    goal_or_action = parts[0].strip("*").strip()
                    detail = parts[1].strip("•").strip()
                    
                    # Check if this is an actionable recommendation
                    if any(keyword in detail.lower() for keyword in ["allocate", "reduce", "sell", "buy", "consider", "add", "keep", "set", "rebalance"]):
                        if goal_or_action and not any(skip in goal_or_action.lower() for skip in ["why", "value", "observation", "rating"]):
                            recommendations.append(f"{goal_or_action}: {detail}")
                        else:
                            recommendations.append(detail)
                    
                    # Also check for rebalancing content
                    if "rebalancing" in current_section and detail:
                        rebalancing_suggestions.append(detail)
            
            # Extract bullet points
            elif line and (line.startswith('-') or line.startswith('•') or line.startswith('*')) and len(line) > 15:
                clean_line = line.lstrip('-•*').strip()
                
                # Check if it's actionable advice
                if any(keyword in clean_line.lower() for keyword in ["allocate", "reduce", "sell", "buy", "consider", "add", "keep", "set", "rebalance", "review"]):
                    if "rebalancing" in current_section or "rebalance" in clean_line.lower():
                        rebalancing_suggestions.append(clean_line)
                    else:
                        recommendations.append(clean_line)
            
            # Extract checklist items
            elif line.startswith("- [ ]") or line.startswith("- [x]"):
                clean_line = line.replace("- [ ]", "").replace("- [x]", "").strip()
                if clean_line:
                    rebalancing_suggestions.append(clean_line)
        
        # Fallback: extract any bullet points if no structured sections found
        if not recommendations:
            for line in lines:
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•')) and len(line) > 20:
                    clean_line = line.lstrip('-•').strip()
                    if any(keyword in clean_line.lower() for keyword in ['reduce', 'add', 'consider', 'allocate', 'diversify']):
                        recommendations.append(clean_line)
        
        # Default rebalancing suggestions if none found
        if not rebalancing_suggestions:
            rebalancing_suggestions = [
                "Consider reducing concentration in largest position",
                "Add defensive assets for risk management", 
                "Maintain 5-10% cash buffer"
            ]
        
        return {
            "success": True,
            "analysis": {
                "recommendations": recommendations[:5],  # Top 5 recommendations
                "risk_assessment": {
                    "level": risk_level,
                    "beta": "1.2",
                    "diversification": f"{len(positions)} positions"
                },
                "rebalancing": rebalancing_suggestions,
                "full_analysis": analysis_text
            }
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Portfolio analysis error: {e}")
        print(f"Full traceback: {error_details}")
        
        return {
            "success": False,
            "error": f"Portfolio analysis failed: {str(e)}"
        }

@app.get("/crypto/price/{symbol}")
async def get_crypto_price(symbol: str, current_user: dict = Depends(get_current_user)):
    """Get current crypto price using public API that doesn't require API keys."""
    try:
        # Import the public crypto API
        from data.public_crypto_api import PublicCryptoAPI
        
        # Create a public crypto API client
        public_api = PublicCryptoAPI()
        
        # Get ticker data from public API
        ticker_data = public_api.get_ticker_data(symbol)
        
        if ticker_data and 'price' in ticker_data:
            return {
                "success": True,
                "symbol": symbol,
                "price": float(ticker_data.get("price", 0)),
                "change": float(ticker_data.get("priceChange", 0)),
                "change_percent": float(ticker_data.get("priceChangePercent", 0))
            }
        else:
            # Try fallback to market data manager if available
            if market_researcher and market_researcher.market_data:
                try:
                    market_overview = await market_researcher.market_data.get_market_overview([symbol])
                    if symbol in market_overview:
                        return {
                            "success": True,
                            "symbol": symbol,
                            "price": float(market_overview[symbol].get("price", 0)),
                            "change": float(market_overview[symbol].get("change_24h", 0)),
                            "change_percent": float(market_overview[symbol].get("change_percent_24h", 0))
                        }
                except Exception:
                    pass
                    
            return {
                "success": False,
                "error": f"Could not fetch price for {symbol}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/stock/price/{symbol}")
async def get_stock_price(symbol: str, current_user: dict = Depends(get_current_user)):
    """Get current stock price."""
    try:
        from data.alpha_vantage_client import AlphaVantageClient
        
        av_client = AlphaVantageClient()
        quote_data = av_client.get_quote(symbol)
        
        if quote_data and "Global Quote" in quote_data:
            quote = quote_data["Global Quote"]
            current_price = float(quote.get("05. price", 0))
            prev_close = float(quote.get("08. previous close", current_price))
            change = current_price - prev_close
            change_percent = (change / prev_close * 100) if prev_close > 0 else 0
            
            return {
                "success": True,
                "symbol": symbol,
                "price": current_price,
                "change": change,
                "change_percent": change_percent
            }
        else:
            return {
                "success": False,
                "error": f"Could not fetch price for {symbol}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# Initialize stocks database
stocks_db = None

def get_stocks_database():
    """Get or initialize the stocks database."""
    global stocks_db
    if stocks_db is None:
        from data.stocks_database import StocksDatabase
        stocks_db = StocksDatabase()
    return stocks_db

@app.get("/stocks/popular/{exchange_code}")
async def get_popular_stocks(exchange_code: str):
    """Get popular stocks for an exchange."""
    try:
        db = get_stocks_database()
        stocks = db.get_stocks_by_exchange(exchange_code)
        # Filter for large cap stocks (popular)
        popular_stocks = [stock for stock in stocks if stock.market_cap_category == "large"]
        # Convert to display format
        stock_list = [f"{stock.symbol} - {stock.name}" for stock in popular_stocks[:10]]
        return {"exchange": exchange_code, "stocks": stock_list}
    except Exception as e:
        print(f"Error getting popular stocks: {e}")
        return {"exchange": exchange_code, "stocks": []}

@app.get("/stocks/sectors/{exchange_code}")
async def get_sectors(exchange_code: str):
    """Get sectors for an exchange."""
    try:
        db = get_stocks_database()
        stocks = db.get_stocks_by_exchange(exchange_code)
        sectors = list(set(stock.sector for stock in stocks))
        sectors.sort()
        return {"exchange": exchange_code, "sectors": sectors}
    except Exception as e:
        print(f"Error getting sectors: {e}")
        return {"exchange": exchange_code, "sectors": []}

@app.get("/stocks/sector/{exchange_code}/{sector}")
async def get_sector_stocks(exchange_code: str, sector: str):
    """Get stocks for a specific sector."""
    try:
        db = get_stocks_database()
        # Get stocks by exchange first, then filter by sector
        exchange_stocks = db.get_stocks_by_exchange(exchange_code)
        sector_stocks = [stock for stock in exchange_stocks if stock.sector.lower() == sector.lower()]
        # Convert to display format
        stock_list = [f"{stock.symbol} - {stock.name}" for stock in sector_stocks]
        stock_list.sort()
        return {"exchange": exchange_code, "sector": sector, "stocks": stock_list}
    except Exception as e:
        print(f"Error getting sector stocks: {e}")
        return {"exchange": exchange_code, "sector": sector, "stocks": []}

@app.get("/stocks/all/{exchange_code}")
async def get_all_stocks(exchange_code: str):
    """Get all stocks for an exchange."""
    try:
        db = get_stocks_database()
        stocks = db.get_stocks_by_exchange(exchange_code)
        # Convert to display format
        stock_list = [f"{stock.symbol} - {stock.name}" for stock in stocks]
        stock_list.sort()
        return {"exchange": exchange_code, "stocks": stock_list}
    except Exception as e:
        print(f"Error getting all stocks: {e}")
        return {"exchange": exchange_code, "stocks": []}

@app.post("/analysis/commodity-futures")
async def analyze_commodity_futures(analysis_request: dict, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Analyze commodity futures with AI insights."""
    
    task_id = str(uuid.uuid4())
    analysis_tasks[task_id] = {
        "status": "running",
        "result": None,
        "error": None,
        "created_at": datetime.now()
    }
    
    async def run_analysis():
        try:
            symbol = analysis_request.get("symbol")
            category = analysis_request.get("category", "Energy")
            
            print(f"[COMMODITY DEBUG] Starting analysis for symbol: {symbol}, category: {category}")
            
            if not symbol:
                analysis_tasks[task_id]["status"] = "error"
                analysis_tasks[task_id]["error"] = "Symbol is required"
                return
            
            # Use existing commodity analyzer from main initialization
            if hasattr(market_researcher, 'commodity_analyzer') and market_researcher.commodity_analyzer:
                analyzer = market_researcher.commodity_analyzer
                print(f"[COMMODITY DEBUG] Commodity analyzer found: {analyzer}")
            else:
                analysis_tasks[task_id]["status"] = "error"
                analysis_tasks[task_id]["error"] = "Commodity analyzer not initialized in main system"
                print("[COMMODITY DEBUG] Commodity analyzer not found")
                return
            
            # Check if commodity client is available
            if not analyzer.commodity_client:
                analysis_tasks[task_id]["status"] = "error"
                analysis_tasks[task_id]["error"] = "Commodity data client not configured. Please set ALPHA_VANTAGE_API_KEY in your .env file"
                print("[COMMODITY DEBUG] Commodity client not available")
                return
            
            print(f"[COMMODITY DEBUG] Commodity client available: {analyzer.commodity_client}")
            
            # Run commodity futures analysis using the analyzer's method
            print("[COMMODITY DEBUG] Fetching commodity data...")
            commodity_data = await analyzer._fetch_commodity_data(symbol)
            print(f"[COMMODITY DEBUG] Commodity data received: {type(commodity_data)}, keys: {commodity_data.keys() if isinstance(commodity_data, dict) else 'Not a dict'}")
            
            if not commodity_data or commodity_data.get('error'):
                error_msg = commodity_data.get('error', f"Failed to fetch commodity data for {symbol}") if commodity_data else f"No data returned for {symbol}"
                analysis_tasks[task_id]["status"] = "error"
                analysis_tasks[task_id]["error"] = error_msg
                print(f"[COMMODITY DEBUG] Error in commodity data: {error_msg}")
                return
            
            # Extract data from the commodity analysis result
            quote = commodity_data.get('quote', {})
            daily_data = commodity_data.get('daily_data', [])
            news = commodity_data.get('news', [])
            
            print(f"[COMMODITY DEBUG] Quote data: {quote}")
            print(f"[COMMODITY DEBUG] Daily data length: {len(daily_data)}")
            print(f"[COMMODITY DEBUG] News length: {len(news)}")
            
            # Calculate current metrics
            current_price = quote.get('price', 0)
            price_change = quote.get('change', 0)
            price_change_pct = 0
            if quote.get('change_percent'):
                try:
                    # Remove % sign and convert to float
                    price_change_pct = float(str(quote.get('change_percent', '0')).replace('%', ''))
                except Exception as pct_error:
                    print(f"[COMMODITY DEBUG] Error parsing change_percent: {pct_error}")
                    price_change_pct = 0
            
            print(f"[COMMODITY DEBUG] Parsed metrics - Price: {current_price}, Change: {price_change}, Change%: {price_change_pct}")
            
            # Run AI analysis with proper parameters
            print("[COMMODITY DEBUG] Running AI analysis...")
            try:
                ai_analysis = await analyzer._run_commodity_llm_analysis(
                    symbol, symbol, commodity_data
                )
                print(f"[COMMODITY DEBUG] AI analysis completed: {type(ai_analysis)}")
            except Exception as ai_error:
                print(f"[COMMODITY DEBUG] AI analysis error: {ai_error}")
                ai_analysis = {"error": str(ai_error)}
            
            result = {
                "success": True,
                "symbol": symbol,
                "category": category,
                "name": symbol,
                "current_price": current_price,
                "price_change": price_change,
                "price_change_pct": price_change_pct,
                "volume": quote.get('volume', 0),
                "open_interest": 0,  # Not available in current data structure
                "historical_data": daily_data,
                "statistics": {
                    "previous_close": quote.get('previous_close', 0),
                    "latest_trading_day": quote.get('latest_trading_day', ''),
                },
                "news": news,
                "ai_analysis": ai_analysis,
                "last_updated": datetime.now().isoformat()
            }
            
            print(f"[COMMODITY DEBUG] Analysis completed successfully")
            analysis_tasks[task_id]["status"] = "completed"
            analysis_tasks[task_id]["result"] = result
            
        except Exception as e:
            print(f"[COMMODITY DEBUG] Exception in run_analysis: {e}")
            import traceback
            traceback.print_exc()
            analysis_tasks[task_id]["status"] = "error"
            analysis_tasks[task_id]["error"] = str(e)
    
    # Start the background task
    background_tasks.add_task(run_analysis)
    
    return {
        "success": True,
        "task_id": task_id,
        "message": f"Commodity futures analysis started for {analysis_request.get('symbol', 'unknown symbol')}",
        "category": analysis_request.get("category", "Energy")
    }

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
