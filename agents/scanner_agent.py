"""
Scanner Agent for systematic trading opportunity detection using Interactive Brokers market scanners.

This agent leverages IB's market scanner functionality to identify trading opportunities
across different markets and asset types, providing systematic screening capabilities
for the MarketResearcher platform.
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json

from agents.base_agent import BaseAgent
from data.interactive_brokers_client import InteractiveBrokersClient
from llm.local_client import LocalLLMClient
from llm.prompt_manager import PromptManager
from config.settings import MarketResearcherConfig

# Import scanner samples for predefined scanner configurations
try:
    import sys
    import os
    ib_samples_path = "# Path to your IB API samples directory"  # Example: "/path/to/twsapi/samples/Python/Testbed"
    sys.path.insert(0, ib_samples_path)
    from ScannerSubscriptionSamples import ScannerSubscriptionSamples
    from ibapi.scanner import ScannerSubscription
    SCANNER_SAMPLES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import ScannerSubscriptionSamples: {e}")
    SCANNER_SAMPLES_AVAILABLE = False

logger = logging.getLogger(__name__)


class TradingOpportunityScorer:
    """Advanced scoring system for ranking trading opportunities from scanner results."""
    
    def __init__(self):
        self.scoring_weights = {
            'volume_score': 0.25,      # Trading volume importance
            'price_change_score': 0.30, # Price movement significance
            'volatility_score': 0.20,   # Volatility assessment
            'market_cap_score': 0.15,   # Market capitalization preference
            'liquidity_score': 0.10     # Bid-ask spread tightness
        }
        
        # Thresholds for scoring
        self.volume_thresholds = {
            'high': 10_000_000,    # 10M+ volume
            'medium': 1_000_000,   # 1M+ volume
            'low': 100_000         # 100K+ volume
        }
        
        self.market_cap_thresholds = {
            'large': 10_000_000_000,    # 10B+ (large cap)
            'mid': 1_000_000_000,       # 1B+ (mid cap)
            'small': 100_000_000        # 100M+ (small cap)
        }
    
    def calculate_opportunity_score(self, scanner_data: Dict) -> float:
        """Calculate composite opportunity score (0-100) for a security."""
        try:
            # Volume score - higher volume indicates better liquidity and interest
            volume = float(scanner_data.get('volume', 0))
            if volume >= self.volume_thresholds['high']:
                volume_score = 100
            elif volume >= self.volume_thresholds['medium']:
                volume_score = 75
            elif volume >= self.volume_thresholds['low']:
                volume_score = 50
            else:
                volume_score = max(0, (volume / self.volume_thresholds['low']) * 50)
            
            # Price change score - significant moves indicate opportunity
            price_change = abs(float(scanner_data.get('changePercent', 0)))
            if price_change >= 10:      # 10%+ move
                price_change_score = 100
            elif price_change >= 5:     # 5%+ move
                price_change_score = 80
            elif price_change >= 2:     # 2%+ move
                price_change_score = 60
            else:
                price_change_score = min(100, price_change * 30)
            
            # Volatility score - moderate volatility preferred (not too high/low)
            volatility = float(scanner_data.get('volatility', 20))
            if 15 <= volatility <= 35:  # Sweet spot
                volatility_score = 100
            elif 10 <= volatility <= 50:  # Acceptable range
                volatility_score = 80
            else:
                volatility_score = max(20, 100 - abs(volatility - 25) * 2)
            
            # Market cap score - preference for established companies
            market_cap = float(scanner_data.get('marketCap', 0))
            if market_cap >= self.market_cap_thresholds['large']:
                market_cap_score = 95
            elif market_cap >= self.market_cap_thresholds['mid']:
                market_cap_score = 85
            elif market_cap >= self.market_cap_thresholds['small']:
                market_cap_score = 70
            else:
                market_cap_score = 40
            
            # Liquidity score - tight spreads indicate good liquidity
            bid = float(scanner_data.get('bid', 0))
            ask = float(scanner_data.get('ask', 0))
            if bid > 0 and ask > 0:
                spread_pct = ((ask - bid) / bid) * 100
                if spread_pct <= 0.1:      # Very tight spread
                    liquidity_score = 100
                elif spread_pct <= 0.5:    # Good spread
                    liquidity_score = 80
                elif spread_pct <= 1.0:    # Acceptable spread
                    liquidity_score = 60
                else:
                    liquidity_score = max(20, 100 - spread_pct * 20)
            else:
                liquidity_score = 50  # Unknown spread
            
            # Calculate weighted composite score
            total_score = (
                volume_score * self.scoring_weights['volume_score'] +
                price_change_score * self.scoring_weights['price_change_score'] +
                volatility_score * self.scoring_weights['volatility_score'] +
                market_cap_score * self.scoring_weights['market_cap_score'] +
                liquidity_score * self.scoring_weights['liquidity_score']
            )
            
            return round(total_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating opportunity score: {e}")
            return 0.0
    
    def rank_opportunities(self, scanner_results: List[Dict]) -> List[Dict]:
        """Rank and sort trading opportunities by composite score."""
        scored_results = []
        
        for result in scanner_results:
            score = self.calculate_opportunity_score(result)
            result['opportunity_score'] = score
            result['score_breakdown'] = self._get_score_breakdown(result)
            scored_results.append(result)
        
        # Sort by score (highest first)
        return sorted(scored_results, key=lambda x: x['opportunity_score'], reverse=True)
    
    def _get_score_breakdown(self, scanner_data: Dict) -> Dict[str, float]:
        """Get detailed score breakdown for transparency."""
        volume = float(scanner_data.get('volume', 0))
        price_change = abs(float(scanner_data.get('changePercent', 0)))
        volatility = float(scanner_data.get('volatility', 20))
        market_cap = float(scanner_data.get('marketCap', 0))
        
        return {
            'volume_score': min(100, (volume / 1_000_000) * 10),
            'price_change_score': min(100, price_change * 10),
            'volatility_score': max(0, 100 - abs(volatility - 20) * 2),
            'market_cap_score': 90 if market_cap > 10_000_000_000 else 70,
            'liquidity_score': 75  # Default estimate
        }


class ScannerAgent(BaseAgent):
    """Agent for systematic trading opportunity detection using market scanners."""
    
    def __init__(self, llm_client: LocalLLMClient, prompt_manager: PromptManager, config: MarketResearcherConfig):
        """Initialize Scanner Agent."""
        super().__init__(llm_client, prompt_manager, config, "Scanner Agent")
        
        self.ib_client = None
        self.scorer = TradingOpportunityScorer()
        self.scanner_cache = {}
        self.last_scan_time = {}
        
        # Scanner configurations
        self.available_scanners = {
            'hot_us_volume': {
                'name': 'Hot US Stocks by Volume',
                'method': 'HotUSStkByVolume',
                'description': 'US stocks with highest trading volume',
                'market': 'US',
                'asset_type': 'stocks'
            },
            'top_gainers_ibis': {
                'name': 'Top % Gainers (IBIS)',
                'method': 'TopPercentGainersIbis',
                'description': 'European stocks with highest percentage gains',
                'market': 'EU',
                'asset_type': 'stocks'
            },
            'active_futures_eurex': {
                'name': 'Most Active Futures (EUREX)',
                'method': 'MostActiveFutEurex',
                'description': 'Most actively traded European futures',
                'market': 'EU',
                'asset_type': 'futures'
            },
            'high_option_volume': {
                'name': 'High Option Volume P/C Ratio',
                'method': 'HighOptVolumePCRatioUSIndexes',
                'description': 'US indexes with high option volume put/call ratios',
                'market': 'US',
                'asset_type': 'indexes'
            },
            'complex_orders': {
                'name': 'Complex Orders and Trades',
                'method': 'ComplexOrdersAndTrades',
                'description': 'Complex option combination trades',
                'market': 'US',
                'asset_type': 'options'
            }
        }
        
        logger.info("Scanner Agent initialized with opportunity scoring system")
    
    def get_agent_type(self) -> str:
        """Return agent type identifier."""
        return "scanner"
    
    def analyze(self, symbol: str = None, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform comprehensive scanner analysis to find trading opportunities.
        
        Args:
            symbol: Optional specific symbol to focus on
            data: Optional analysis parameters (scanner_types, max_results, etc.)
        """
        try:
            logger.info(f"Starting scanner analysis for trading opportunities")
            
            # Setup parameters
            scanner_types = data.get('scanner_types', ['hot_us_volume']) if data else ['hot_us_volume']
            max_results = data.get('max_results', 20) if data else 20
            use_cache = data.get('use_cache', True) if data else True
            
            # Connect to IB if needed
            if not self._ensure_ib_connection():
                return {
                    "success": False,
                    "error": "Could not establish IB connection",
                    "timestamp": datetime.now().isoformat(),
                    "agent": self.agent_name
                }
            
            # Run scanners
            scanner_results = {}
            all_opportunities = []
            
            for scanner_type in scanner_types:
                if scanner_type not in self.available_scanners:
                    logger.warning(f"Unknown scanner type: {scanner_type}")
                    continue
                
                logger.info(f"Running scanner: {self.available_scanners[scanner_type]['name']}")
                
                # Get scanner data
                results = self._run_scanner(scanner_type, max_results, use_cache)
                
                if results:
                    scanner_results[scanner_type] = {
                        'name': self.available_scanners[scanner_type]['name'],
                        'description': self.available_scanners[scanner_type]['description'],
                        'results_count': len(results),
                        'results': results[:10]  # Store top 10 for analysis
                    }
                    
                    # Add to opportunities pool
                    all_opportunities.extend(results)
                    
                    logger.info(f"Scanner {scanner_type} found {len(results)} opportunities")
                else:
                    scanner_results[scanner_type] = {
                        'name': self.available_scanners[scanner_type]['name'],
                        'error': 'No results or scanner failed'
                    }
            
            # Rank all opportunities
            if all_opportunities:
                ranked_opportunities = self.scorer.rank_opportunities(all_opportunities)
                top_opportunities = ranked_opportunities[:10]
            else:
                top_opportunities = []
            
            # Generate LLM analysis of opportunities
            llm_analysis = self._generate_opportunity_analysis(top_opportunities, scanner_results)
            
            # Prepare final analysis
            analysis_result = {
                "success": True,
                "scanner_results": scanner_results,
                "top_opportunities": top_opportunities,
                "opportunities_count": len(all_opportunities),
                "llm_analysis": llm_analysis,
                "timestamp": datetime.now().isoformat(),
                "agent": self.agent_name,
                "parameters": {
                    "scanner_types": scanner_types,
                    "max_results": max_results,
                    "use_cache": use_cache
                }
            }
            
            # Update agent state
            self.last_analysis = analysis_result
            self.analysis_history.append(analysis_result)
            
            # Extract confidence score
            confidence = self._extract_confidence_score(
                llm_analysis.get('analysis', {}).get('full_text', '')
            )
            self.confidence_scores.append(confidence)
            
            logger.info(f"Scanner analysis completed. Found {len(all_opportunities)} total opportunities")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in scanner analysis: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "agent": self.agent_name
            }
    
    def _ensure_ib_connection(self) -> bool:
        """Ensure Interactive Brokers connection is established."""
        try:
            if not self.ib_client:
                self.ib_client = InteractiveBrokersClient()
            
            if not self.ib_client.is_connected():
                logger.info("Establishing IB connection for scanner analysis...")
                
                # Use asyncio to handle async connection
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    connected = loop.run_until_complete(self.ib_client.connect())
                    if connected:
                        logger.info("✅ Connected to Interactive Brokers for scanning")
                        time.sleep(2)  # Allow connection to stabilize
                        return True
                    else:
                        logger.error("❌ Failed to connect to Interactive Brokers")
                        return False
                finally:
                    loop.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error establishing IB connection: {e}")
            return False
    
    def _run_scanner(self, scanner_type: str, max_results: int, use_cache: bool) -> List[Dict]:
        """Run a specific scanner and return results."""
        try:
            # Check cache first
            cache_key = f"{scanner_type}_{max_results}"
            if use_cache and cache_key in self.scanner_cache:
                cache_time = self.last_scan_time.get(cache_key, 0)
                if time.time() - cache_time < 300:  # 5 minute cache
                    logger.info(f"Using cached results for {scanner_type}")
                    return self.scanner_cache[cache_key]
            
            if not SCANNER_SAMPLES_AVAILABLE:
                logger.error("Scanner samples not available")
                return []
            
            # Get scanner subscription from samples
            scanner_config = self.available_scanners[scanner_type]
            method_name = scanner_config['method']
            
            if not hasattr(ScannerSubscriptionSamples, method_name):
                logger.error(f"Scanner method {method_name} not found")
                return []
            
            # Get scanner subscription
            method = getattr(ScannerSubscriptionSamples, method_name)
            scanner_subscription = method()
            
            # Run scanner
            results = self.ib_client.get_scanner_data(scanner_subscription, max_results)
            
            # Cache results
            if results:
                self.scanner_cache[cache_key] = results
                self.last_scan_time[cache_key] = time.time()
            
            return results
            
        except Exception as e:
            logger.error(f"Error running scanner {scanner_type}: {e}")
            return []
    
    def _generate_opportunity_analysis(self, opportunities: List[Dict], scanner_results: Dict) -> Dict[str, Any]:
        """Generate LLM analysis of trading opportunities."""
        try:
            if not opportunities:
                return {
                    "success": False,
                    "error": "No opportunities to analyze"
                }
            
            # Prepare context for LLM
            context = self._prepare_scanner_context(opportunities, scanner_results)
            
            # Create analysis prompt
            messages = [
                {
                    "role": "system",
                    "content": self.prompt_manager.get_prompt("scanner_analysis_system")
                },
                {
                    "role": "user", 
                    "content": self.prompt_manager.format_scanner_analysis_prompt(context)
                }
            ]
            
            # Execute LLM analysis
            llm_result = self._execute_llm_analysis(messages, context)
            
            return llm_result
            
        except Exception as e:
            logger.error(f"Error generating opportunity analysis: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_scanner_context(self, opportunities: List[Dict], scanner_results: Dict) -> Dict[str, Any]:
        """Prepare context data for LLM analysis."""
        return {
            "top_opportunities": opportunities[:5],  # Top 5 for detailed analysis
            "total_opportunities": len(opportunities),
            "scanner_summary": {
                name: {
                    "results_count": result.get('results_count', 0),
                    "description": result.get('description', '')
                }
                for name, result in scanner_results.items()
            },
            "market_conditions": self._assess_market_conditions(opportunities),
            "timestamp": datetime.now().isoformat()
        }
    
    def _assess_market_conditions(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """Assess overall market conditions from scanner results."""
        try:
            if not opportunities:
                return {"condition": "unknown", "reason": "no data"}
            
            # Analyze price changes
            price_changes = [float(opp.get('changePercent', 0)) for opp in opportunities]
            avg_change = sum(price_changes) / len(price_changes)
            
            # Analyze volumes
            volumes = [float(opp.get('volume', 0)) for opp in opportunities if opp.get('volume', 0) > 0]
            avg_volume = sum(volumes) / len(volumes) if volumes else 0
            
            # Determine market condition
            if avg_change > 2:
                condition = "bullish"
            elif avg_change < -2:
                condition = "bearish"
            else:
                condition = "neutral"
            
            # Determine activity level
            if avg_volume > 5_000_000:
                activity = "high"
            elif avg_volume > 1_000_000:
                activity = "moderate"
            else:
                activity = "low"
            
            return {
                "condition": condition,
                "activity_level": activity,
                "avg_price_change": round(avg_change, 2),
                "avg_volume": int(avg_volume),
                "opportunities_analyzed": len(opportunities)
            }
            
        except Exception as e:
            logger.error(f"Error assessing market conditions: {e}")
            return {"condition": "unknown", "error": str(e)}
    
    def get_available_scanners(self) -> Dict[str, Dict]:
        """Get list of available scanner configurations."""
        return self.available_scanners
    
    def run_specific_scanner(self, scanner_type: str, max_results: int = 20) -> Dict[str, Any]:
        """Run a specific scanner and return results."""
        try:
            if scanner_type not in self.available_scanners:
                return {
                    "success": False,
                    "error": f"Unknown scanner type: {scanner_type}",
                    "available_scanners": list(self.available_scanners.keys())
                }
            
            # Ensure IB connection
            if not self._ensure_ib_connection():
                return {
                    "success": False,
                    "error": "Could not establish IB connection"
                }
            
            # Run scanner
            results = self._run_scanner(scanner_type, max_results, use_cache=False)
            
            if results:
                # Score and rank results
                ranked_results = self.scorer.rank_opportunities(results)
                
                return {
                    "success": True,
                    "scanner_type": scanner_type,
                    "scanner_name": self.available_scanners[scanner_type]['name'],
                    "results_count": len(results),
                    "results": ranked_results,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "No results returned from scanner"
                }
                
        except Exception as e:
            logger.error(f"Error running specific scanner {scanner_type}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if self.ib_client:
                # Check if there's already an event loop running
                try:
                    loop = asyncio.get_running_loop()
                    # If we're in an async context, schedule the disconnect
                    asyncio.create_task(self.ib_client.disconnect())
                    logger.info("Scheduled disconnect from Interactive Brokers")
                except RuntimeError:
                    # No running loop, create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        loop.run_until_complete(self.ib_client.disconnect())
                        logger.info("Disconnected from Interactive Brokers")
                    finally:
                        loop.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()


# Prompt extensions for scanner analysis
def add_scanner_prompts(prompt_manager: PromptManager):
    """Add scanner-specific prompts to the prompt manager."""
    
    scanner_system_prompt = """You are a professional market scanner analyst specializing in identifying trading opportunities from market scanner data.

Your role is to:
1. Analyze scanner results from multiple market scanners
2. Identify the most promising trading opportunities
3. Assess market conditions and trends
4. Provide actionable trading insights
5. Rank opportunities by potential and risk

Focus on:
- Volume and liquidity analysis
- Price movement significance
- Market timing considerations
- Risk/reward assessments
- Entry and exit strategies

Provide clear, actionable analysis with specific reasoning for your recommendations."""

    scanner_analysis_template = """Analyze the following market scanner results and trading opportunities:

TOP OPPORTUNITIES:
{top_opportunities}

SCANNER SUMMARY:
{scanner_summary}

MARKET CONDITIONS:
{market_conditions}

Please provide:
1. Analysis of the top 3 trading opportunities
2. Overall market condition assessment
3. Recommended trading strategies
4. Risk considerations
5. Timing recommendations
6. Confidence level (1-10)

Focus on actionable insights for active traders."""

    # Add prompts to manager
    prompt_manager.prompts["scanner_analysis_system"] = scanner_system_prompt
    prompt_manager.prompt_templates["scanner_analysis"] = scanner_analysis_template
    
    # Add formatting method
    def format_scanner_analysis_prompt(context: Dict[str, Any]) -> str:
        return scanner_analysis_template.format(
            top_opportunities=json.dumps(context.get('top_opportunities', []), indent=2),
            scanner_summary=json.dumps(context.get('scanner_summary', {}), indent=2),
            market_conditions=json.dumps(context.get('market_conditions', {}), indent=2)
        )
    
    # Bind method to prompt manager
    prompt_manager.format_scanner_analysis_prompt = format_scanner_analysis_prompt
