"""
Derivatives Analyzer Module

This module provides comprehensive analysis capabilities for various derivative instruments:
- Stock Options (calls, puts, chains, Greeks)
- Equity Index Futures and Options (SPX, NDX, RUT, etc.)
- Currency Derivatives (FX forwards, options, swaps)
- Volatility and Rates Derivatives (VIX, SONIA, SOFR)
- Crypto Derivatives (Bitcoin/Ethereum futures and options)
"""

import numpy as np
import math
from scipy.stats import norm
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

from data.universal_cache import UniversalCache
from data.yahoo_client import YahooFinanceClient

logger = logging.getLogger(__name__)

@dataclass
class OptionContract:
    """Option contract information structure."""
    symbol: str
    underlying: str
    strike: float
    expiry: str
    option_type: str  # 'call' or 'put'
    last_price: float
    bid: float
    ask: float
    volume: int
    open_interest: int
    implied_volatility: float

@dataclass
class FuturesContract:
    """Futures contract information structure."""
    symbol: str
    underlying: str
    expiry: str
    last_price: float
    change: float
    change_pct: float
    volume: int
    open_interest: int

@dataclass
class DerivativeInfo:
    """General derivative instrument information."""
    symbol: str
    name: str
    category: str
    underlying: str
    exchange: str
    currency: str
    contract_size: str

class DerivativesAnalyzer:
    """Comprehensive derivatives analyzer."""
    
    def __init__(self, llm_client=None, config=None):
        """Initialize the derivatives analyzer."""
        self.derivatives_data = self._initialize_derivatives_data()
        self.llm_client = llm_client
        self.config = config
        self.cache = UniversalCache(config) if config else None
        self.yahoo_client = YahooFinanceClient()
        
    def _initialize_derivatives_data(self) -> Dict[str, List[DerivativeInfo]]:
        """Initialize derivatives data for different categories."""
        return {
            "STOCK_OPTIONS": [
                DerivativeInfo("AAPL", "Apple Inc. Options", "Stock Options", "AAPL", "CBOE", "USD", "100 shares"),
                DerivativeInfo("TSLA", "Tesla Inc. Options", "Stock Options", "TSLA", "CBOE", "USD", "100 shares"),
                DerivativeInfo("MSFT", "Microsoft Corp. Options", "Stock Options", "MSFT", "CBOE", "USD", "100 shares"),
                DerivativeInfo("GOOGL", "Alphabet Inc. Options", "Stock Options", "GOOGL", "CBOE", "USD", "100 shares"),
                DerivativeInfo("AMZN", "Amazon.com Inc. Options", "Stock Options", "AMZN", "CBOE", "USD", "100 shares"),
                DerivativeInfo("NVDA", "NVIDIA Corp. Options", "Stock Options", "NVDA", "CBOE", "USD", "100 shares"),
                DerivativeInfo("SPY", "SPDR S&P 500 ETF Options", "Stock Options", "SPY", "CBOE", "USD", "100 shares"),
                DerivativeInfo("QQQ", "Invesco QQQ ETF Options", "Stock Options", "QQQ", "CBOE", "USD", "100 shares"),
            ],
            "INDEX_FUTURES": [
                DerivativeInfo("ES=F", "E-mini S&P 500 Futures", "Index Futures", "SPX", "CME", "USD", "$50 x Index"),
                DerivativeInfo("NQ=F", "E-mini NASDAQ 100 Futures", "Index Futures", "NDX", "CME", "USD", "$20 x Index"),
                DerivativeInfo("YM=F", "E-mini Dow Jones Futures", "Index Futures", "DJI", "CBOT", "USD", "$5 x Index"),
                DerivativeInfo("RTY=F", "E-mini Russell 2000 Futures", "Index Futures", "RUT", "CME", "USD", "$50 x Index"),
                DerivativeInfo("VX=F", "VIX Futures", "Volatility Futures", "VIX", "CFE", "USD", "$1000 x Index"),
            ],
            "INDEX_OPTIONS": [
                DerivativeInfo("SPX", "S&P 500 Index Options", "Index Options", "SPX", "CBOE", "USD", "$100 x Index"),
                DerivativeInfo("NDX", "NASDAQ 100 Index Options", "Index Options", "NDX", "CBOE", "USD", "$100 x Index"),
                DerivativeInfo("RUT", "Russell 2000 Index Options", "Index Options", "RUT", "CBOE", "USD", "$100 x Index"),
                DerivativeInfo("VIX", "VIX Options", "Volatility Options", "VIX", "CBOE", "USD", "$100 x Index"),
            ],
            "CURRENCY_DERIVATIVES": [
                DerivativeInfo("6E=F", "Euro FX Futures", "Currency Futures", "EUR/USD", "CME", "USD", "€125,000"),
                DerivativeInfo("6B=F", "British Pound Futures", "Currency Futures", "GBP/USD", "CME", "USD", "£62,500"),
                DerivativeInfo("6J=F", "Japanese Yen Futures", "Currency Futures", "JPY/USD", "CME", "USD", "¥12,500,000"),
                DerivativeInfo("6C=F", "Canadian Dollar Futures", "Currency Futures", "CAD/USD", "CME", "USD", "C$100,000"),
                DerivativeInfo("6A=F", "Australian Dollar Futures", "Currency Futures", "AUD/USD", "CME", "USD", "A$100,000"),
                DerivativeInfo("6S=F", "Swiss Franc Futures", "Currency Futures", "CHF/USD", "CME", "USD", "CHF125,000"),
            ],
            "RATES_DERIVATIVES": [
                DerivativeInfo("ZB=F", "30-Year Treasury Bond Futures", "Interest Rate Futures", "US30Y", "CBOT", "USD", "$100,000"),
                DerivativeInfo("ZN=F", "10-Year Treasury Note Futures", "Interest Rate Futures", "US10Y", "CBOT", "USD", "$100,000"),
                DerivativeInfo("ZF=F", "5-Year Treasury Note Futures", "Interest Rate Futures", "US5Y", "CBOT", "USD", "$100,000"),
                DerivativeInfo("ZT=F", "2-Year Treasury Note Futures", "Interest Rate Futures", "US2Y", "CBOT", "USD", "$200,000"),
                DerivativeInfo("GE=F", "Eurodollar Futures", "Interest Rate Futures", "USD3M", "CME", "USD", "$2,500 x Rate"),
            ],
            "CRYPTO_DERIVATIVES": [
                DerivativeInfo("BTC=F", "Bitcoin Futures", "Crypto Futures", "BTC-USD", "CME", "USD", "5 BTC"),
                DerivativeInfo("ETH=F", "Ethereum Futures", "Crypto Futures", "ETH-USD", "CME", "USD", "50 ETH"),
                DerivativeInfo("MBT=F", "Micro Bitcoin Futures", "Crypto Futures", "BTC-USD", "CME", "USD", "0.1 BTC"),
                DerivativeInfo("MET=F", "Micro Ethereum Futures", "Crypto Futures", "ETH-USD", "CME", "USD", "0.1 ETH"),
            ]
        }
    
    def _calculate_black_scholes(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> Dict[str, float]:
        """Calculate Black-Scholes option price and Greeks."""
        try:
            if T <= 0 or sigma <= 0:
                return {"price": 0, "delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}
            
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)
            
            # Standard normal CDF approximation
            def norm_cdf(x):
                return 0.5 * (1 + math.erf(x / math.sqrt(2)))
            
            # Standard normal PDF
            def norm_pdf(x):
                return math.exp(-0.5 * x ** 2) / math.sqrt(2 * math.pi)
            
            if option_type.lower() == 'call':
                price = S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
                delta = norm_cdf(d1)
                rho = K * T * math.exp(-r * T) * norm_cdf(d2)
            else:  # put
                price = K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)
                delta = -norm_cdf(-d1)
                rho = -K * T * math.exp(-r * T) * norm_cdf(-d2)
            
            gamma = norm_pdf(d1) / (S * sigma * math.sqrt(T))
            theta = (-S * norm_pdf(d1) * sigma / (2 * math.sqrt(T)) 
                    - r * K * math.exp(-r * T) * norm_cdf(d2 if option_type.lower() == 'call' else -d2))
            if option_type.lower() == 'put':
                theta += r * K * math.exp(-r * T) * norm_cdf(-d2)
            theta /= 365  # Convert to daily theta
            
            vega = S * norm_pdf(d1) * math.sqrt(T) / 100  # Convert to percentage
            
            return {
                "price": max(0, price),
                "delta": delta,
                "gamma": gamma,
                "theta": theta,
                "vega": vega,
                "rho": rho / 100  # Convert to percentage
            }
            
        except Exception as e:
            logger.error(f"Error calculating Black-Scholes: {e}")
            return {"price": 0, "delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}
    
    async def analyze_stock_options(self, symbol: str, expiry_filter: Optional[str] = None) -> Dict[str, Any]:
        """Analyze stock options for a given symbol."""
        try:
            # Check cache first
            if self.cache:
                cached_result = self.cache.get("options", symbol, symbol=symbol, expiry_filter=expiry_filter)
                if cached_result:
                    logger.info(f"Using cached options data for: {symbol}")
                    return cached_result
            
            # Get current stock price using centralized client
            stock_info = await self.yahoo_client.get_stock_info(symbol)
            current_price = stock_info.get('currentPrice', 0)
            
            if current_price == 0:
                # Fallback to history if currentPrice not available
                hist = await self.yahoo_client.get_historical_data(symbol, period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
            
            # Note: Options data requires direct yfinance access for now
            # as yahoo_client doesn't support options chains yet
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            
            # Get options expiration dates
            expiry_dates = ticker.options
            if not expiry_dates:
                return {"success": False, "error": f"No options data available for {symbol}"}
            
            # Filter expiry dates if specified
            if expiry_filter:
                expiry_dates = [date for date in expiry_dates if expiry_filter in date]
            
            options_data = []
            for expiry in expiry_dates[:3]:  # Limit to first 3 expiries to avoid too much data
                try:
                    option_chain = ticker.option_chain(expiry)
                    calls = option_chain.calls
                    puts = option_chain.puts
                    
                    # Process calls
                    for _, call in calls.iterrows():
                        if call['volume'] > 0:  # Only include options with volume
                            # Calculate time to expiry in years
                            try:
                                expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
                                days_to_expiry = (expiry_date - datetime.now()).days
                                time_to_expiry = max(days_to_expiry / 365.0, 0.001)  # Minimum 1 day
                            except:
                                time_to_expiry = 0.05  # Default ~18 days
                            
                            greeks = self._calculate_black_scholes(
                                current_price, call['strike'], time_to_expiry, 0.05, call['impliedVolatility'], 'call'
                            )
                            options_data.append({
                                "type": "call",
                                "strike": call['strike'],
                                "expiry": expiry,
                                "last_price": call['lastPrice'],
                                "bid": call['bid'],
                                "ask": call['ask'],
                                "volume": call['volume'],
                                "open_interest": call['openInterest'],
                                "implied_vol": call['impliedVolatility'],
                                "greeks": greeks
                            })
                    
                    # Process puts
                    for _, put in puts.iterrows():
                        if put['volume'] > 0:  # Only include options with volume
                            # Calculate time to expiry in years
                            try:
                                expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
                                days_to_expiry = (expiry_date - datetime.now()).days
                                time_to_expiry = max(days_to_expiry / 365.0, 0.001)  # Minimum 1 day
                            except:
                                time_to_expiry = 0.05  # Default ~18 days
                            
                            greeks = self._calculate_black_scholes(
                                current_price, put['strike'], time_to_expiry, 0.05, put['impliedVolatility'], 'put'
                            )
                            options_data.append({
                                "type": "put",
                                "strike": put['strike'],
                                "expiry": expiry,
                                "last_price": put['lastPrice'],
                                "bid": put['bid'],
                                "ask": put['ask'],
                                "volume": put['volume'],
                                "open_interest": put['openInterest'],
                                "implied_vol": put['impliedVolatility'],
                                "greeks": greeks
                            })
                            
                except Exception as e:
                    logger.error(f"Error processing options for expiry {expiry}: {e}")
                    continue
            
            if not options_data:
                return {"success": False, "error": f"No options data with volume found for {symbol}"}
            
            result = {
                "success": True,
                "symbol": symbol,
                "current_price": current_price,
                "options_data": options_data,
                "total_options": len(options_data),
                "last_updated": datetime.now().isoformat()
            }
            
            # Cache the result
            if self.cache:
                self.cache.set("options", symbol, result, symbol=symbol, expiry_filter=expiry_filter)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing stock options for {symbol}: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_index_futures(self, category: str = "INDEX_FUTURES") -> Dict[str, Any]:
        """Analyze index futures contracts."""
        try:
            # Check cache first
            if self.cache:
                cached_result = self.cache.get("futures", category, category=category)
                if cached_result:
                    logger.info(f"Using cached futures data for: {category}")
                    return cached_result
            
            if category not in self.derivatives_data:
                return {"success": False, "error": f"Category {category} not supported"}
            
            derivatives = self.derivatives_data[category]
            results = []
            
            for derivative in derivatives:
                try:
                    hist = await self.yahoo_client.get_historical_data(derivative.symbol, period="1d")
                    
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                        change = current_price - prev_close
                        change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
                        volume = hist['Volume'].iloc[-1]
                        
                        # Calculate volatility
                        returns = hist['Close'].pct_change().dropna()
                        volatility = returns.std() * np.sqrt(252) * 100  # Annualized volatility
                        
                        results.append({
                            "success": True,
                            "derivative_info": derivative,
                            "current_price": current_price,
                            "change": change,
                            "change_pct": change_pct,
                            "volume": volume,
                            "volatility": volatility,
                            "underlying": derivative.underlying,
                            "name": derivative.name,
                            "contract_size": derivative.contract_size
                        })
                    else:
                        results.append({
                            "success": False,
                            "derivative_info": derivative,
                            "error": "No price data available"
                        })
                        
                except Exception as e:
                    logger.error(f"Error fetching data for {derivative.symbol}: {e}")
                    results.append({
                        "success": False,
                        "derivative_info": derivative,
                        "error": str(e)
                    })
            
            # Count successful contracts
            successful_contracts = len([r for r in results if r.get("success", False)])
            
            result = {
                "success": True,
                "category": category,
                "futures": results,
                "total_contracts": len(results),
                "contracts_analyzed": successful_contracts,
                "last_updated": datetime.now().isoformat()
            }
            
            # Cache the result
            if self.cache:
                self.cache.set("futures", category, result, category=category)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing index futures: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_currency_derivatives(self) -> Dict[str, Any]:
        """Analyze currency derivatives."""
        return await self.analyze_index_futures("CURRENCY_DERIVATIVES")
    
    async def analyze_rates_derivatives(self) -> Dict[str, Any]:
        """Analyze interest rates derivatives."""
        return await self.analyze_index_futures("RATES_DERIVATIVES")
    
    async def analyze_crypto_derivatives(self) -> Dict[str, Any]:
        """Analyze cryptocurrency derivatives."""
        return await self.analyze_index_futures("CRYPTO_DERIVATIVES")
    
    async def get_volatility_surface(self, symbol: str) -> Dict[str, Any]:
        """Get implied volatility surface for options."""
        try:
            options_data = await self.analyze_stock_options(symbol)
            
            if not options_data.get("success", False):
                return options_data
            
            vol_surface = []
            
            # Group options by expiry
            options_by_expiry = {}
            for option in options_data["options_data"]:
                expiry = option["expiry"]
                if expiry not in options_by_expiry:
                    options_by_expiry[expiry] = []
                options_by_expiry[expiry].append(option)
            
            for expiry, expiry_options in options_by_expiry.items():
                # Calculate days to expiry
                try:
                    expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
                    days_to_expiry = (expiry_date - datetime.now()).days
                except:
                    days_to_expiry = 0
                
                # Combine calls and puts
                all_options = []
                for option in expiry_options:
                    all_options.append({
                        "strike": option["strike"],
                        "implied_vol": option["implied_vol"],
                        "option_type": option["type"],
                        "moneyness": option["strike"] / options_data["current_price"]
                    })
                
                vol_surface.append({
                    "expiry": expiry,
                    "days_to_expiry": days_to_expiry,
                    "options": all_options
                })
            
            return {
                "success": True,
                "symbol": symbol,
                "current_price": options_data["current_price"],
                "volatility_surface": vol_surface,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting volatility surface for {symbol}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_available_categories(self) -> List[str]:
        """Get list of available derivative categories."""
        return list(self.derivatives_data.keys())
    
    def get_category_instruments(self, category: str) -> List[DerivativeInfo]:
        """Get list of instruments for a specific category."""
        return self.derivatives_data.get(category, [])
    
    async def analyze_options_with_ai(self, options_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze options data using AI for insights and recommendations."""
        try:
            if not self.llm_client or not options_data.get("success", False):
                return {"success": False, "error": "No LLM client available or invalid options data"}
            
            symbol = options_data["symbol"]
            current_price = options_data["current_price"]
            
            # Prepare analysis data - group by expiry
            options_by_expiry = {}
            for option in options_data["options_data"]:
                expiry = option["expiry"]
                if expiry not in options_by_expiry:
                    options_by_expiry[expiry] = {"calls": [], "puts": []}
                
                if option["type"] == "call":
                    options_by_expiry[expiry]["calls"].append(option)
                else:
                    options_by_expiry[expiry]["puts"].append(option)
            
            analysis_summary = []
            for expiry, expiry_data in options_by_expiry.items():
                # Calculate days to expiry
                try:
                    expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
                    days_to_expiry = (expiry_date - datetime.now()).days
                except:
                    days_to_expiry = 0
                
                # Analyze call/put ratio
                total_call_volume = sum(call["volume"] for call in expiry_data["calls"])
                total_put_volume = sum(put["volume"] for put in expiry_data["puts"])
                call_put_ratio = total_call_volume / total_put_volume if total_put_volume > 0 else float('inf')
                
                # Find highest volume strikes
                top_call = max(expiry_data["calls"], key=lambda x: x["volume"]) if expiry_data["calls"] else None
                top_put = max(expiry_data["puts"], key=lambda x: x["volume"]) if expiry_data["puts"] else None
                
                # Calculate average implied volatility
                all_ivs = [call["implied_vol"] for call in expiry_data["calls"]] + \
                         [put["implied_vol"] for put in expiry_data["puts"]]
                avg_iv = sum(iv for iv in all_ivs if iv > 0) / len([iv for iv in all_ivs if iv > 0]) if all_ivs else 0
                
                analysis_summary.append({
                    "expiry": expiry,
                    "days_to_expiry": days_to_expiry,
                    "call_put_ratio": call_put_ratio,
                    "avg_implied_volatility": avg_iv,
                    "top_call_strike": top_call["strike"] if top_call else None,
                    "top_put_strike": top_put["strike"] if top_put else None,
                    "total_call_volume": total_call_volume,
                    "total_put_volume": total_put_volume
                })
            
            # Create AI analysis prompt
            prompt = f"""
Analyze the following options data for {symbol} (current price: ${current_price:.2f}) and provide insights:

OPTIONS SUMMARY:
{self._format_options_for_ai(analysis_summary)}

Please provide:
1. Market sentiment analysis based on call/put ratios and volume
2. Key support/resistance levels indicated by high-volume strikes
3. Implied volatility analysis and what it suggests about expected price movement
4. Risk assessment and potential trading strategies
5. Notable patterns or unusual activity

Focus on actionable insights for traders and risk managers.
"""
            
            # Get AI analysis with efficient call
            messages = [{"role": "user", "content": prompt}]
            if hasattr(self.llm_client, 'generate_response_async'):
                ai_result = await self.llm_client.generate_response_async(messages)
            else:
                ai_result = self.llm_client.generate_response(messages)
                if isinstance(ai_result, str):
                    ai_result = {"success": True, "content": ai_result}
                elif isinstance(ai_result, dict) and 'content' in ai_result:
                    ai_result["success"] = True
            
            if not ai_result.get("success", False):
                return {"success": False, "error": f"LLM request failed: {ai_result.get('error', 'Unknown error')}"}
            
            ai_response = ai_result["content"]
            
            return {
                "success": True,
                "symbol": symbol,
                "ai_analysis": ai_response,
                "analysis_summary": analysis_summary,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in AI options analysis: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_options_for_ai(self, analysis_summary: List[Dict]) -> str:
        """Format options analysis summary for AI prompt."""
        formatted = []
        for data in analysis_summary:
            formatted.append(f"""
Expiry: {data['expiry']} ({data['days_to_expiry']} days)
- Call/Put Ratio: {data['call_put_ratio']:.2f}
- Average IV: {data['avg_implied_volatility']:.1%}
- Highest Call Volume: ${data['top_call_strike']} ({data['total_call_volume']:,} contracts)
- Highest Put Volume: ${data['top_put_strike']} ({data['total_put_volume']:,} contracts)
""")
        return "\n".join(formatted)
    
    async def analyze_futures_with_ai(self, futures_data: Dict[str, Any], category: str) -> Dict[str, Any]:
        """Analyze futures data using AI for market insights."""
        try:
            if not self.llm_client or not futures_data.get("success", False):
                return {"success": False, "error": "No LLM client available or invalid futures data"}
            
            # Prepare analysis data
            market_summary = []
            for future in futures_data["futures"]:
                if future.get("success", False):
                    derivative_info = future.get("derivative_info", {})
                    market_summary.append({
                        "name": future.get("name", derivative_info.get("name", "Unknown")),
                        "symbol": derivative_info.get("symbol", "Unknown"),
                        "underlying": future.get("underlying", derivative_info.get("underlying", "")),
                        "price": future["current_price"],
                        "change_pct": future["change_pct"],
                        "volatility": future["volatility"]
                    })
            
            # Create category-specific prompt
            category_context = {
                "INDEX_FUTURES": "equity index futures and their implications for broader market sentiment",
                "CURRENCY_DERIVATIVES": "currency futures and their impact on forex markets and international trade",
                "RATES_DERIVATIVES": "interest rate derivatives and their signals about monetary policy expectations",
                "CRYPTO_DERIVATIVES": "cryptocurrency derivatives and their role in digital asset price discovery"
            }
            
            context = category_context.get(category, "derivative instruments")
            
            prompt = f"""
Analyze the following {context} data and provide market insights:

FUTURES ANALYSIS:
{self._format_futures_for_ai(market_summary)}

Please provide:
1. Overall market sentiment and directional bias
2. Key trends and patterns in the data
3. Risk factors and volatility assessment
4. Correlation analysis between instruments
5. Trading implications and strategic considerations
6. Economic or market events that might be influencing these movements

Focus on actionable market intelligence and risk management insights.
"""
            
            # Get AI analysis with efficient call
            messages = [{"role": "user", "content": prompt}]
            if hasattr(self.llm_client, 'generate_response_async'):
                ai_result = await self.llm_client.generate_response_async(messages)
            else:
                ai_result = self.llm_client.generate_response(messages)
                if isinstance(ai_result, str):
                    ai_result = {"success": True, "content": ai_result}
                elif isinstance(ai_result, dict) and 'content' in ai_result:
                    ai_result["success"] = True
            
            if not ai_result.get("success", False):
                return {"success": False, "error": f"LLM request failed: {ai_result.get('error', 'Unknown error')}"}
            
            ai_response = ai_result["content"]
            
            return {
                "success": True,
                "category": category,
                "ai_analysis": ai_response,
                "market_summary": market_summary,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in AI futures analysis: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_futures_for_ai(self, market_summary: List[Dict]) -> str:
        """Format futures analysis summary for AI prompt."""
        formatted = []
        for data in market_summary:
            formatted.append(f"""
{data['name']} ({data['symbol']})
- Current Price: {data['price']:.2f}
- Change: {data['change_pct']:+.2f}%
- Volatility: {data['volatility']:.1f}%
- Underlying: {data['underlying']}
""")
        return "\n".join(formatted)
    
    async def analyze_volatility_with_ai(self, vol_surface_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze volatility surface using AI for trading insights."""
        try:
            if not self.llm_client or not vol_surface_data.get("success", False):
                return {"success": False, "error": "No LLM client available or invalid volatility data"}
            
            symbol = vol_surface_data["symbol"]
            current_price = vol_surface_data["current_price"]
            
            # Analyze volatility patterns
            vol_analysis = []
            for surface_data in vol_surface_data["volatility_surface"]:
                expiry = surface_data["expiry"]
                days_to_expiry = surface_data["days_to_expiry"]
                options = surface_data["options"]
                
                # Group by moneyness
                atm_options = [opt for opt in options if 0.95 <= opt["moneyness"] <= 1.05]
                otm_calls = [opt for opt in options if opt["moneyness"] > 1.05 and opt["option_type"] == "call"]
                otm_puts = [opt for opt in options if opt["moneyness"] < 0.95 and opt["option_type"] == "put"]
                
                atm_iv = sum(opt["implied_vol"] for opt in atm_options) / len(atm_options) if atm_options else 0
                call_skew = sum(opt["implied_vol"] for opt in otm_calls[:3]) / min(3, len(otm_calls)) if otm_calls else 0
                put_skew = sum(opt["implied_vol"] for opt in otm_puts[:3]) / min(3, len(otm_puts)) if otm_puts else 0
                
                vol_analysis.append({
                    "expiry": expiry,
                    "days_to_expiry": days_to_expiry,
                    "atm_iv": atm_iv,
                    "call_skew": call_skew,
                    "put_skew": put_skew,
                    "skew_differential": put_skew - call_skew
                })
            
            prompt = f"""
Analyze the following volatility surface data for {symbol} (current price: ${current_price:.2f}):

VOLATILITY ANALYSIS:
{self._format_volatility_for_ai(vol_analysis)}

Please provide:
1. Volatility term structure analysis (short vs long-term expectations)
2. Volatility skew interpretation (put vs call skew implications)
3. Market fear/greed indicators from the volatility patterns
4. Optimal volatility trading strategies based on the surface
5. Risk management considerations for option positions
6. Expected price movement ranges based on implied volatility levels

Focus on practical trading applications and risk assessment.
"""
            
            # Get AI analysis with efficient call
            messages = [{"role": "user", "content": prompt}]
            if hasattr(self.llm_client, 'generate_response_async'):
                ai_result = await self.llm_client.generate_response_async(messages)
            else:
                ai_result = self.llm_client.generate_response(messages)
                if isinstance(ai_result, str):
                    ai_result = {"success": True, "content": ai_result}
                elif isinstance(ai_result, dict) and 'content' in ai_result:
                    ai_result["success"] = True
            
            if not ai_result.get("success", False):
                return {"success": False, "error": f"LLM request failed: {ai_result.get('error', 'Unknown error')}"}
            
            ai_response = ai_result["content"]
            
            return {
                "success": True,
                "symbol": symbol,
                "ai_analysis": ai_response,
                "volatility_analysis": vol_analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in AI volatility analysis: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_volatility_for_ai(self, vol_analysis: List[Dict]) -> str:
        """Format volatility analysis for AI prompt."""
        formatted = []
        for data in vol_analysis:
            formatted.append(f"""
Expiry: {data['expiry']} ({data['days_to_expiry']} days)
- ATM IV: {data['atm_iv']:.1%}
- Call Skew: {data['call_skew']:.1%}
- Put Skew: {data['put_skew']:.1%}
- Skew Differential: {data['skew_differential']:+.1%}
""")
        return "\n".join(formatted)
