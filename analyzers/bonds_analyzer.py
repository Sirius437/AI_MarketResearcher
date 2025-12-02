"""
Bonds and Gilts Analyzer Module

This module provides analysis capabilities for government bonds and gilts from major markets:
- US Treasury bonds (2, 5, 10, 20, 30 year)
- UK Gilts
- European bonds (Germany, France, Italy)
- Other major markets (Japan, Canada, Australia)
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

from data.universal_cache import UniversalCache
from data.yahoo_client import YahooFinanceClient
from config.settings import MarketResearcherConfig

logger = logging.getLogger(__name__)

@dataclass
class BondInfo:
    """Bond information structure."""
    symbol: str
    name: str
    country: str
    maturity: str
    currency: str
    yield_symbol: str  # For yield data if different from price symbol

class BondsAnalyzer:
    """Analyzer for government bonds and gilts."""
    
    def __init__(self, llm_client=None, config=None):
        """Initialize the bonds analyzer."""
        self.bonds_data = self._initialize_bonds_data()
        self.llm_client = llm_client
        self.config = config
        self.cache = UniversalCache(config) if config else None
        self.yahoo_client = YahooFinanceClient()
        
    def _initialize_bonds_data(self) -> Dict[str, List[BondInfo]]:
        """Initialize bonds data for different markets."""
        return {
            "US_TREASURY": [
                BondInfo("^TNX", "US 10-Year Treasury", "United States", "10Y", "USD", "^TNX"),
                BondInfo("^FVX", "US 5-Year Treasury", "United States", "5Y", "USD", "^FVX"),
                BondInfo("^IRX", "US 3-Month Treasury", "United States", "3M", "USD", "^IRX"),
                BondInfo("^TYX", "US 30-Year Treasury", "United States", "30Y", "USD", "^TYX"),
                # Note: 2Y and 20Y yields may need different symbols or data sources
                BondInfo("2YY=F", "US 2-Year Treasury", "United States", "2Y", "USD", "2YY=F"),
            ],
            "UK_GILTS": [                
                BondInfo("UKG5.L", "UK 5-Year Gilt", "United Kingdom", "5Y", "GBP", "GILT5Y.L"),
                BondInfo("0P0001COEN.L", "Allianz UK & European Investment Funds - Allianz Index-Linked Gilt Fund", "United Kingdom", "10Y", "GBP","GILT30Y.L"),
                
            ],
            "EUROPEAN": [
                BondInfo("^TNX-DE", "German 10-Year Bund", "Germany", "10Y", "EUR", "^TNX-DE"),
                BondInfo("^TNX-FR", "French 10-Year OAT", "France", "10Y", "EUR", "^TNX-FR"),
                BondInfo("^TNX-IT", "Italian 10-Year BTP", "Italy", "10Y", "EUR", "^TNX-IT"),
                BondInfo("^TNX-ES", "Spanish 10-Year Bond", "Spain", "10Y", "EUR", "^TNX-ES"),
            ],
            "OTHER_MAJOR": [
                BondInfo("^TNX-JP", "Japanese 10-Year Bond", "Japan", "10Y", "JPY", "^TNX-JP"),
                BondInfo("^TNX-CA", "Canadian 10-Year Bond", "Canada", "10Y", "CAD", "^TNX-CA"),
                BondInfo("^TNX-AU", "Australian 10-Year Bond", "Australia", "10Y", "AUD", "^TNX-AU"),
                BondInfo("^TNX-CH", "Swiss 10-Year Bond", "Switzerland", "10Y", "CHF", "^TNX-CH"),
            ]
        }
    
    async def get_bond_data(self, bond_info: BondInfo, period: str = "1mo") -> Dict[str, Any]:
        """Get bond yield data for a specific bond."""
        try:
            hist = await self.yahoo_client.get_historical_data(bond_info.yield_symbol, period=period)
            
            if hist.empty:
                return {
                    "success": False,
                    "error": f"No data available for {bond_info.name}",
                    "bond_info": bond_info
                }
            
            current_yield = hist['Close'].iloc[-1] if not hist.empty else None
            prev_yield = hist['Close'].iloc[-2] if len(hist) > 1 else current_yield
            
            change = current_yield - prev_yield if prev_yield else 0
            change_pct = (change / prev_yield * 100) if prev_yield and prev_yield != 0 else 0
            
            # Calculate basic statistics
            high_52w = hist['High'].max() if len(hist) > 50 else hist['High'].max()
            low_52w = hist['Low'].min() if len(hist) > 50 else hist['Low'].min()
            avg_yield = hist['Close'].mean()
            
            return {
                "success": True,
                "bond_info": bond_info,
                "current_yield": current_yield,
                "previous_yield": prev_yield,
                "change": change,
                "change_pct": change_pct,
                "high_52w": high_52w,
                "low_52w": low_52w,
                "avg_yield": avg_yield,
                "last_updated": datetime.now().isoformat(),
                "data_points": len(hist)
            }
            
        except Exception as e:
            logger.error(f"Error fetching bond data for {bond_info.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "bond_info": bond_info
            }
    
    async def analyze_market_bonds(self, market: str, period: str = "1mo") -> Dict[str, Any]:
        """Analyze all bonds for a specific market."""
        # Check cache first
        if self.cache:
            cached_result = self.cache.get("bonds", market, market=market, period=period)
            if cached_result:
                logger.info(f"Using cached bonds data for market: {market}")
                return cached_result
        
        if market not in self.bonds_data:
            return {
                "success": False,
                "error": f"Market '{market}' not supported. Available: {list(self.bonds_data.keys())}"
            }
        
        bonds = self.bonds_data[market]
        results = []
        
        for bond in bonds:
            bond_data = await self.get_bond_data(bond, period)
            results.append(bond_data)
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
        
        # Calculate market summary
        successful_results = [r for r in results if r.get("success", False)]
        
        if not successful_results:
            return {
                "success": False,
                "error": f"No data available for any bonds in {market}",
                "market": market,
                "results": results
            }
        
        avg_yield = sum(r["current_yield"] for r in successful_results) / len(successful_results)
        avg_change = sum(r["change"] for r in successful_results) / len(successful_results)
        
        result = {
            "success": True,
            "market": market,
            "summary": {
                "average_yield": avg_yield,
                "average_change": avg_change,
                "bonds_analyzed": len(successful_results),
                "total_bonds": len(bonds)
            },
            "bonds": results,
            "last_updated": datetime.now().isoformat()
        }
        
        # Cache the result
        if self.cache:
            self.cache.set("bonds", market, result, market=market, period=period)
        
        return result
    
    async def get_yield_curve_data(self, country: str = "US") -> Dict[str, Any]:
        """Get yield curve data for visualization."""
        try:
            # Check cache first
            if self.cache:
                cached_result = self.cache.get("yield_curve", country, country=country)
                if cached_result:
                    logger.info(f"Using cached yield curve data for: {country}")
                    return cached_result
            
            if country == "US":
                bonds = self.bonds_data["US_TREASURY"]
            elif country == "UK":
                bonds = self.bonds_data["UK_GILTS"]
            else:
                return {"success": False, "error": f"Yield curve not available for {country}"}
            
            curve_data = []
            for bond in bonds:
                bond_data = await self.get_bond_data(bond)
                if bond_data.get("success", False):
                    # Extract maturity as numeric value for sorting
                    maturity_str = bond.maturity
                    if maturity_str.endswith('Y'):
                        maturity = float(maturity_str[:-1])
                    elif maturity_str.endswith('M'):
                        maturity = float(maturity_str[:-1]) / 12
                    else:
                        maturity = 0
                    
                    curve_data.append({
                        "maturity": maturity,
                        "yield": bond_data["current_yield"],
                        "name": bond.name
                    })
                
                await asyncio.sleep(0.1)  # Rate limiting
            
            # Sort by maturity
            curve_data.sort(key=lambda x: x["maturity"])
            
            result = {
                "success": True,
                "country": country,
                "curve_data": curve_data,
                "last_updated": datetime.now().isoformat()
            }
            
            # Cache the result
            if self.cache:
                self.cache.set("yield_curve", country, result, country=country)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting yield curve data: {e}")
            return {"success": False, "error": str(e)}
    
    async def compare_international_bonds(self, maturity: str = "10Y") -> Dict[str, Any]:
        """Compare bonds of similar maturity across different countries."""
        try:
            comparison_data = []
            
            # Find bonds with matching maturity across markets
            for market, bonds in self.bonds_data.items():
                matching_bonds = [bond for bond in bonds if bond.maturity == maturity]
                
                for bond in matching_bonds:
                    bond_data = await self.get_bond_data(bond, "1d")
                    if bond_data.get("success", False):
                        comparison_data.append({
                            "country": bond.country,
                            "market": market,
                            "name": bond.name,
                            "yield": bond_data["current_yield"],
                            "change": bond_data["change"],
                            "change_pct": bond_data["change_pct"],
                            "currency": bond.currency
                        })
                    
                    await asyncio.sleep(0.1)
            
            # Sort by yield (highest to lowest)
            comparison_data.sort(key=lambda x: x["yield"], reverse=True)
            
            return {
                "success": True,
                "maturity": maturity,
                "comparison": comparison_data,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error comparing international bonds: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_bond_trends(self, market: str, period: str = "3mo") -> Dict[str, Any]:
        """Analyze trends in bond yields over time."""
        try:
            if market not in self.bonds_data:
                return {
                    "success": False,
                    "error": f"Market '{market}' not supported"
                }
            
            trends = []
            
            for bond in self.bonds_data[market]:
                hist = await self.yahoo_client.get_historical_data(bond.yield_symbol, period=period)
                
                if not hist.empty:
                    # Calculate trend metrics
                    start_yield = hist['Close'].iloc[0]
                    end_yield = hist['Close'].iloc[-1]
                    total_change = end_yield - start_yield
                    total_change_pct = (total_change / start_yield * 100) if start_yield != 0 else 0
                    
                    # Calculate volatility
                    volatility = hist['Close'].std()
                    
                    # Determine trend direction
                    if total_change_pct > 1:
                        trend = "Rising"
                    elif total_change_pct < -1:
                        trend = "Falling"
                    else:
                        trend = "Stable"
                    
                    trends.append({
                        "bond": bond.name,
                        "maturity": bond.maturity,
                        "start_yield": start_yield,
                        "end_yield": end_yield,
                        "total_change": total_change,
                        "total_change_pct": total_change_pct,
                        "volatility": volatility,
                        "trend": trend,
                        "data_points": len(hist)
                    })
                
                await asyncio.sleep(0.1)
            
            return {
                "success": True,
                "market": market,
                "period": period,
                "trends": trends,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing bond trends: {e}")
            return {"success": False, "error": str(e)}
    
    def get_available_markets(self) -> List[str]:
        """Get list of available bond markets."""
        return list(self.bonds_data.keys())
    
    def get_market_bonds(self, market: str) -> List[BondInfo]:
        """Get list of bonds for a specific market."""
        return self.bonds_data.get(market, [])
    
    async def analyze_bonds_with_ai(self, bonds_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze bonds data using AI for market insights and monetary policy implications."""
        try:
            if not self.llm_client or not bonds_data.get("success", False):
                return {"success": False, "error": "No LLM client available or invalid bonds data"}
            
            market = bonds_data["market"]
            summary = bonds_data["summary"]
            bonds = bonds_data["bonds"]
            
            # Prepare analysis data
            bonds_summary = []
            for bond_data in bonds:
                if bond_data.get("success", False):
                    bond_info = bond_data["bond_info"]
                    bonds_summary.append({
                        "name": bond_info.name,
                        "maturity": bond_info.maturity,
                        "country": bond_info.country,
                        "current_yield": bond_data["current_yield"],
                        "change": bond_data["change"],
                        "change_pct": bond_data["change_pct"],
                        "high_52w": bond_data["high_52w"],
                        "low_52w": bond_data["low_52w"],
                        "avg_yield": bond_data["avg_yield"]
                    })
            
            # Create market-specific context
            market_context = {
                "US_TREASURY": "US Treasury bonds and their implications for Federal Reserve policy and economic outlook",
                "UK_GILTS": "UK Gilts and their signals about Bank of England policy and Brexit/economic impacts",
                "EUROPEAN": "European government bonds and their relationship to ECB policy and sovereign risk",
                "OTHER_MAJOR": "major international government bonds and global monetary policy coordination"
            }
            
            context = market_context.get(market, "government bonds")
            
            # Concise bonds analysis prompt
            avg_yield = summary['average_yield']
            avg_change = summary['average_change']
            bonds_count = summary['bonds_analyzed']
            
            # Get key bond data for prompt
            key_bonds = [b for b in bonds_summary[:3]]  # Limit to top 3 bonds
            bonds_text = '; '.join([f"{b['name']} {b['current_yield']:.2f}% ({b['change_pct']:+.1f}%)" for b in key_bonds])
            
            prompt = f"Analyze {market.replace('_', ' ').title()} bonds: Avg yield {avg_yield:.2f}%, Change {avg_change:+.2f}%. Key bonds: {bonds_text}. Provide brief analysis on monetary policy signals, economic outlook, inflation expectations, and investment strategy recommendations."
            
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
                "market": market,
                "ai_analysis": ai_response,
                "bonds_summary": bonds_summary,
                "market_summary": summary,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in AI bonds analysis: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_bonds_for_ai(self, bonds_summary: List[Dict]) -> str:
        """Format bonds analysis summary for AI prompt."""
        formatted = []
        for bond in bonds_summary:
            formatted.append(f"""
{bond['name']} ({bond['maturity']})
- Current Yield: {bond['current_yield']:.3f}%
- Change: {bond['change']:+.3f}% ({bond['change_pct']:+.2f}%)
- 52W Range: {bond['low_52w']:.3f}% - {bond['high_52w']:.3f}%
- Average: {bond['avg_yield']:.3f}%
""")
        return "\n".join(formatted)
    
    async def analyze_yield_curve_with_ai(self, curve_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze yield curve using AI for economic insights."""
        try:
            if not self.llm_client or not curve_data.get("success", False):
                return {"success": False, "error": "No LLM client available or invalid curve data"}
            
            country = curve_data["country"]
            curve_points = curve_data["curve_data"]
            
            # Analyze curve shape
            if len(curve_points) >= 2:
                short_term = min(curve_points, key=lambda x: x["maturity"])
                long_term = max(curve_points, key=lambda x: x["maturity"])
                slope = long_term["yield"] - short_term["yield"]
                
                # Determine curve shape
                if slope > 0.5:
                    curve_shape = "Steep Normal"
                elif slope > 0:
                    curve_shape = "Normal"
                elif slope > -0.5:
                    curve_shape = "Flat"
                else:
                    curve_shape = "Inverted"
            else:
                slope = 0
                curve_shape = "Insufficient Data"
            
            # Concise yield curve analysis prompt
            key_points = [f"{p['maturity']:.0f}Y: {p['yield']:.2f}%" for p in curve_points[:4]]  # Limit to 4 key points
            points_text = ', '.join(key_points)
            
            prompt = f"Analyze {country} yield curve: Shape {curve_shape}, Slope {slope:+.2f}%. Key points: {points_text}. Provide brief analysis on economic cycle implications, recession indicators, monetary policy expectations, and optimal investment strategies."
            
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
                "country": country,
                "curve_shape": curve_shape,
                "slope": slope,
                "ai_analysis": ai_response,
                "curve_points": curve_points,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in AI yield curve analysis: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_curve_for_ai(self, curve_points: List[Dict]) -> str:
        """Format yield curve points for AI prompt."""
        formatted = []
        for point in curve_points:
            maturity = point["maturity"]
            yield_val = point["yield"]
            name = point["name"]
            
            if maturity < 1:
                maturity_str = f"{int(maturity * 12)}M"
            else:
                maturity_str = f"{int(maturity)}Y"
            
            formatted.append(f"{maturity_str:>4} | {yield_val:>6.3f}% | {name}")
        
        return "\n".join(formatted)
    
    async def analyze_international_bonds_with_ai(self, comparison_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze international bond comparison using AI for global insights."""
        try:
            if not self.llm_client or not comparison_data.get("success", False):
                return {"success": False, "error": "No LLM client available or invalid comparison data"}
            
            maturity = comparison_data["maturity"]
            bonds = comparison_data["comparison"]
            
            # Calculate spreads vs benchmark (typically US Treasury)
            us_yield = None
            for bond in bonds:
                if bond["country"] == "United States":
                    us_yield = bond["yield"]
                    break
            
            spreads_analysis = []
            for bond in bonds:
                spread = bond["yield"] - us_yield if us_yield else 0
                spreads_analysis.append({
                    "country": bond["country"],
                    "yield": bond["yield"],
                    "spread": spread,
                    "change": bond["change"],
                    "change_pct": bond["change_pct"],
                    "currency": bond["currency"]
                })
            
            # Concise international bonds analysis prompt
            top_bonds = spreads_analysis[:4]  # Limit to top 4 countries
            bonds_text = '; '.join([f"{b['country']}: {b['yield']:.2f}% (spread {b['spread']:+.0f}bp)" for b in top_bonds])
            
            prompt = f"Analyze international {maturity} bonds: {bonds_text}. US benchmark: {us_yield:.2f}%. Provide brief analysis on global risk sentiment, currency implications, sovereign credit risk, and optimal international allocation strategies."
            
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
                "maturity": maturity,
                "ai_analysis": ai_response,
                "spreads_analysis": spreads_analysis,
                "benchmark_yield": us_yield,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in AI international bonds analysis: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_international_bonds_for_ai(self, spreads_analysis: List[Dict], benchmark_yield: float) -> str:
        """Format international bonds comparison for AI prompt."""
        formatted = []
        formatted.append(f"{'Country':<15} | {'Yield':<8} | {'Spread':<8} | {'Change':<8} | {'Currency'}")
        formatted.append("-" * 60)
        
        for bond in spreads_analysis:
            country = bond["country"]
            yield_val = bond["yield"]
            spread = bond["spread"]
            change_pct = bond["change_pct"]
            currency = bond["currency"]
            
            formatted.append(f"{country:<15} | {yield_val:>6.3f}% | {spread:>+6.0f}bp | {change_pct:>+5.1f}% | {currency}")
        
        if benchmark_yield:
            formatted.append(f"\nBenchmark (US Treasury): {benchmark_yield:.3f}%")
        
        return "\n".join(formatted)
    
    async def analyze_bond_trends_with_ai(self, trends_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze bond trends using AI for market direction insights."""
        try:
            if not self.llm_client or not trends_data.get("success", False):
                return {"success": False, "error": "No LLM client available or invalid trends data"}
            
            market = trends_data["market"]
            period = trends_data["period"]
            trends = trends_data["trends"]
            
            # Analyze overall market direction
            rising_count = sum(1 for trend in trends if trend["trend"] == "Rising")
            falling_count = sum(1 for trend in trends if trend["trend"] == "Falling")
            stable_count = sum(1 for trend in trends if trend["trend"] == "Stable")
            
            total_trends = len(trends)
            market_direction = "Mixed"
            if rising_count > total_trends * 0.6:
                market_direction = "Rising Yields"
            elif falling_count > total_trends * 0.6:
                market_direction = "Falling Yields"
            elif stable_count > total_trends * 0.6:
                market_direction = "Stable"
            
            # Concise bond trends analysis prompt
            key_trends = trends[:3]  # Limit to top 3 trends
            trends_text = '; '.join([f"{t['bond']} ({t['maturity']}): {t['trend']} {t['total_change_pct']:+.1f}%" for t in key_trends])
            
            prompt = f"Analyze {market.replace('_', ' ').title()} bond trends over {period}: Direction {market_direction} ({rising_count} rising, {falling_count} falling). Key trends: {trends_text}. Provide brief analysis on market momentum, central bank policy implications, and risk management considerations."
            
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
                "market": market,
                "period": period,
                "market_direction": market_direction,
                "trends_summary": {
                    "rising": rising_count,
                    "falling": falling_count,
                    "stable": stable_count,
                    "total": total_trends
                },
                "ai_analysis": ai_response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in AI bond trends analysis: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_trends_for_ai(self, trends: List[Dict]) -> str:
        """Format bond trends for AI prompt."""
        formatted = []
        for trend in trends:
            bond_name = trend["bond"]
            maturity = trend["maturity"]
            start_yield = trend["start_yield"]
            end_yield = trend["end_yield"]
            total_change_pct = trend["total_change_pct"]
            trend_direction = trend["trend"]
            volatility = trend["volatility"]
            
            formatted.append(f"""
{bond_name} ({maturity})
- Start: {start_yield:.3f}% → End: {end_yield:.3f}%
- Change: {total_change_pct:+.2f}%
- Trend: {trend_direction}
- Volatility: {volatility:.3f}%
""")
        return "\n".join(formatted)
