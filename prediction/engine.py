"""Prediction engine for orchestrating multi-agent cryptocurrency analysis."""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import numpy as np

from agents import TechnicalAgent, SentimentAgent, NewsAgent, RiskAgent, TradingAgent
from data.market_data import MarketDataManager
from llm.local_client import LocalLLMClient
from llm.prompt_manager import PromptManager
from config.settings import MarketResearcherConfig

logger = logging.getLogger(__name__)


class PredictionEngine:
    """Main prediction engine that orchestrates multiple trading agents."""
    
    def __init__(self, agents: Dict, market_data: MarketDataManager, llm_client: LocalLLMClient, prompt_manager: PromptManager, config: MarketResearcherConfig):
        """Initialize prediction engine with shared components."""
        self.config = config
        self.market_data = market_data
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager
        self.agents = agents
        
        # Initialize LLM-free TradingAgent if not already present
        if 'trading' not in self.agents or self.agents['trading'] is None:
            try:
                from agents.trading_agent import TradingAgent
                self.agents['trading'] = TradingAgent(web_mode=True)
                logging.getLogger(__name__).info("Initialized LLM-free TradingAgent for web mode")
            except Exception as e:
                logging.getLogger(__name__).warning(f"Failed to initialize LLM-free TradingAgent: {e}")
        
        # Prediction state
        self.last_prediction = {}
        self.prediction_history = []
        
        logging.getLogger(__name__).info("Prediction engine initialized with all agents")
    
    async def predict(
        self, 
        symbol: str, 
        enriched_data: Optional[Dict[str, Any]] = None,
        include_agents: Optional[List[str]] = None,
        position_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive trading prediction for a symbol."""
        try:
            print(f"[DEBUG] Starting prediction for {symbol}")
            
            # Determine which agents to use
            active_agents = self._get_active_agents(include_agents)
            
            # Gather market data (use enriched data if provided)
            if enriched_data:
                # Use enriched data as primary source, supplement with basic market data if needed
                market_data = enriched_data.copy()
                
                # Only gather additional market data if enriched data is missing key components
                historical_data = market_data.get('historical_data')
                needs_basic_data = (not market_data.get('current_price') or 
                                  historical_data is None or 
                                  (hasattr(historical_data, 'empty') and historical_data.empty))
                
                if needs_basic_data:
                    basic_market_data = await self._gather_market_data(symbol)
                    if basic_market_data:
                        # Merge basic data under enriched data (enriched data takes precedence)
                        for key, value in basic_market_data.items():
                            if key not in market_data:
                                market_data[key] = value
                else:
                    # Even if we don't need basic data, we still need price change information
                    basic_market_data = await self._gather_market_data(symbol)
                    if basic_market_data:
                        # Add price change keys that are missing from enriched data
                        price_change_keys = ['price_change', 'price_change_percent', 'price_change_24h', 'volume', 'high_24h', 'low_24h']
                        for key in price_change_keys:
                            if key not in market_data and key in basic_market_data:
                                market_data[key] = basic_market_data[key]
            else:
                market_data = await self._gather_market_data(symbol)
                
            if not market_data:
                return {
                    "success": False,
                    "error": "Failed to gather market data",
                    "symbol": symbol
                }
            
            # Debug: Check what data is being passed to agents
            print(f"[DEBUG] Market data keys being passed to agents: {list(market_data.keys())}")
            print(f"[DEBUG] Price change data in market_data: price_change={market_data.get('price_change')}, price_change_24h={market_data.get('price_change_24h')}, price_change_percent={market_data.get('price_change_percent')}")
            if 'historical_data' in market_data:
                hist_data = market_data['historical_data']
                if hasattr(hist_data, 'columns'):
                    print(f"[DEBUG] Historical data columns in prediction engine: {list(hist_data.columns)}")
                    if 'rsi' in hist_data.columns:
                        latest_rsi = hist_data.iloc[-1]['rsi']
                        print(f"[DEBUG] Latest RSI in prediction engine: {latest_rsi}")
            
            # Run agent analyses
            agent_results = self._run_agent_analyses(symbol, market_data, active_agents, position_data)
            
            # Generate Investment Commentary
            investment_commentary = self._generate_investment_commentary(symbol, market_data, agent_results)
            if investment_commentary:
                agent_results['investment_commentary'] = investment_commentary
            
            # Synthesize final decision
            final_decision = self._synthesize_decision(symbol, agent_results, market_data)
            
            # Market data gathered successfully
            
            # Create comprehensive prediction result
            # Debug market data values before creating context
            print(f"[DEBUG] Current price: {market_data.get('current_price')}, type: {type(market_data.get('current_price'))}")
            print(f"[DEBUG] Price change: {market_data.get('price_change')}, type: {type(market_data.get('price_change'))}")
            print(f"[DEBUG] Price change percent: {market_data.get('price_change_percent')}, type: {type(market_data.get('price_change_percent'))}")
            print(f"[DEBUG] Volume: {market_data.get('volume')}, type: {type(market_data.get('volume'))}")
            
            # Ensure numeric values for market context
            current_price = float(market_data.get("current_price", 0))
            price_change = float(market_data.get("price_change", 0))
            price_change_percent = float(market_data.get("price_change_percent", 0))
            volume = float(market_data.get("volume", 0))
            
            prediction_result = {
                "success": True,
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "market_data": market_data,
                "market_context": {
                    "current_price": current_price,
                    "price_change": price_change,
                    "price_change_percent": price_change_percent,
                    "volume": volume
                },
                "agent_results": agent_results,
                "final_decision": final_decision,
                "confidence": self._calculate_overall_confidence(agent_results),
                "risk_assessment": agent_results.get("risk", {}).get("risk_score", 50)
            }
            
            # Store prediction
            self._store_prediction(prediction_result)
            
            logging.getLogger(__name__).info(f"Prediction completed for {symbol}: {final_decision.get('action', 'unknown')}")
            return prediction_result
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error in prediction for {symbol}: {e}")
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "timestamp": datetime.now().isoformat()
            }
    
    def batch_predict(
        self, 
        symbols: List[str], 
        max_concurrent: int = 3
    ) -> Dict[str, Dict[str, Any]]:
        """Generate predictions for multiple symbols concurrently."""
        try:
            async def predict_batch():
                semaphore = asyncio.Semaphore(max_concurrent)
                
                async def predict_single(symbol):
                    async with semaphore:
                        return await self.predict(symbol)
                
                tasks = [predict_single(symbol) for symbol in symbols]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                return {symbol: result for symbol, result in zip(symbols, results)}
            
            # Run batch prediction
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(predict_batch())
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(predict_batch())
                finally:
                    loop.close()
                    
        except Exception as e:
            logging.getLogger(__name__).error(f"Error in batch prediction: {e}")
            return {symbol: {"success": False, "error": str(e)} for symbol in symbols}
    
    def _get_active_agents(self, include_agents: Optional[List[str]]) -> List[str]:
        """Determine which agents should be active for analysis."""
        if include_agents:
            return [agent for agent in include_agents if agent in self.agents]
        
        # Default active agents based on configuration
        active = ["technical", "trading"]  # Always include technical and trading analysis
        
        if self.config.enable_sentiment_analysis:
            active.append("sentiment")
        
        if self.config.enable_news_analysis:
            active.append("news")
        
        active.append("risk")  # Always include risk assessment
        
        return active
    
    async def _gather_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Gather comprehensive market data for analysis."""
        try:
            # Get basic market overview
            overview = await self.market_data.get_market_overview([symbol])
            if not overview or symbol not in overview:
                logging.getLogger(__name__).error(f"Failed to get market overview for {symbol}")
                return None
            
            symbol_data = overview[symbol]
            
            # Get multi-timeframe data
            multi_tf_data = await self.market_data.get_multi_timeframe_data(symbol)
            
            # Get sentiment data
            sentiment_data = self.market_data.get_market_sentiment_data(symbol)
            
            # Get volatility metrics
            volatility_metrics = await self.market_data.get_volatility_metrics(symbol)
            
            # Get liquidity score
            liquidity_score = self.market_data.get_liquidity_score(symbol)
            
            # Get fresh ticker data for price changes - use appropriate data source
            ticker_data = {}
            # Only use Binance for crypto symbols (contain 'USDT', 'BTC', 'ETH', etc.)
            is_crypto = any(crypto_suffix in symbol.upper() for crypto_suffix in ['USDT', 'BTC', 'ETH', 'BNB', 'BUSD'])
            
            if is_crypto and self.market_data.binance_client:
                try:
                    ticker_data = self.market_data.binance_client.get_24hr_ticker(symbol)
                    logging.getLogger(__name__).info(f"Crypto ticker data for {symbol}: {ticker_data}")
                except Exception as e:
                    logging.getLogger(__name__).warning(f"Failed to get fresh crypto ticker data: {e}")
                    ticker_data = {}
            else:
                # For stocks, use Yahoo Finance or other stock data sources
                try:
                    # Use existing symbol_data which comes from appropriate stock sources
                    ticker_data = {
                        "price": symbol_data.get("price", 0),
                        "price_change": symbol_data.get("change_24h", 0),
                        "price_change_percent": symbol_data.get("change_percent_24h", 0)
                    }
                    logging.getLogger(__name__).info(f"Stock ticker data for {symbol}: {ticker_data}")
                except Exception as e:
                    logging.getLogger(__name__).warning(f"Failed to get fresh stock ticker data: {e}")
                    ticker_data = {}
            
            # Debug: Log symbol_data for fallback values
            logging.getLogger(__name__).info(f"Symbol data fallback values: change_24h={symbol_data.get('change_24h')}, change_percent_24h={symbol_data.get('change_percent_24h')}")
            logging.getLogger(__name__).info(f"Ticker data after processing: {ticker_data}")
            
            # Debug: Log volume discrepancy analysis
            if ticker_data and 'volume' in ticker_data and 'quoteVolume' in ticker_data:
                base_volume = ticker_data['volume']
                quote_volume = ticker_data['quoteVolume']
                logging.getLogger(__name__).info(f"Volume analysis - Base volume: {base_volume} {symbol[:3]}, Quote volume: ${quote_volume:,.0f} USD")
                logging.getLogger(__name__).info(f"Quote volume formatted: ${quote_volume/1e9:.2f}B USD")
            
            # Combine all data with proper Binance key mapping
            market_data = {
                "symbol": symbol,
                "current_price": ticker_data.get("price", symbol_data["price"]) if ticker_data else symbol_data["price"],
                "price_change": ticker_data.get("priceChange", ticker_data.get("price_change", symbol_data.get("change_24h", 0))),
                "price_change_percent": ticker_data.get("priceChangePercent", ticker_data.get("price_change_percent", symbol_data.get("change_percent_24h", 0))),
                "price_change_24h": ticker_data.get("priceChange", ticker_data.get("price_change", symbol_data.get("change_24h", 0))),
                "volume": ticker_data.get("quoteVolume", symbol_data["volume"]) if ticker_data and "quoteVolume" in ticker_data else symbol_data["volume"],
                "high_24h": symbol_data["high_24h"],
                "low_24h": symbol_data["low_24h"],
                "historical_data": multi_tf_data.get("1h", None),
                "multi_timeframe": multi_tf_data,
                "sentiment_data": sentiment_data,
                "volatility_metrics": volatility_metrics,
                "liquidity_score": liquidity_score
            }
            
            # Add market_overview to market_data for agent access
            market_data["market_overview"] = overview[symbol]
            
            return market_data
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error gathering market data for {symbol}: {e}")
            return None
    
    def _run_agent_analyses(
        self, 
        symbol: str, 
        market_data: Dict[str, Any], 
        active_agents: List[str],
        position_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Run analyses from all active agents."""
        agent_results = {}
        
        for agent_name in active_agents:
            try:
                agent = self.agents[agent_name]
                
                # Prepare agent-specific data
                agent_data = self._prepare_agent_data(agent_name, market_data, position_data)
                
                # Run agent analysis
                result = agent.analyze(symbol, agent_data)
                agent_results[agent_name] = result
                
                print(f"[DEBUG] {agent_name} analysis completed for {symbol}")
                
            except Exception as e:
                logging.getLogger(__name__).error(f"Error in {agent_name} analysis for {symbol}: {e}")
                agent_results[agent_name] = {
                    "success": False,
                    "error": str(e),
                    "agent": agent_name
                }
        
        return agent_results
    
    def _prepare_agent_data(
        self, 
        agent_name: str, 
        market_data: Dict[str, Any],
        position_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare data specific to each agent type with reduced token usage."""
        # Create minimal base data
        base_data = {
            "symbol": market_data.get("symbol"),
            "current_price": market_data.get("current_price", 0),
            "price_change_24h": market_data.get("price_change_24h", 0),
            "price_change_percent": market_data.get("price_change_percent", 0),
            "volume": market_data.get("volume", 0),
            "high_24h": market_data.get("high_24h", 0),
            "low_24h": market_data.get("low_24h", 0)
        }
        
        # Add enriched data if available (OHLCV, technical indicators, etc.)
        if "ohlcv_30d" in market_data:
            base_data["ohlcv_30d"] = market_data["ohlcv_30d"]
        if "technical_indicators" in market_data:
            base_data["technical_indicators"] = market_data["technical_indicators"]
        if "technical_context" in market_data:
            base_data["technical_context"] = market_data["technical_context"]
        
        if agent_name == "technical":
            # Technical agent gets the full historical DataFrame for proper analysis
            historical_data = market_data.get("historical_data")
            if historical_data is not None and not historical_data.empty:
                print(f"[DEBUG] Passing historical_data to technical agent with shape: {historical_data.shape}")
                base_data["historical_data"] = historical_data
                
            # Add market_overview for volume data access
            if "market_overview" in market_data:
                base_data["market_overview"] = market_data["market_overview"]
                
            # Also extract latest indicators for quick reference if historical data exists
            if historical_data is not None and not historical_data.empty:
                latest = historical_data.iloc[-1]
                base_data.update({
                    "rsi": latest.get('rsi', 50),
                    "macd_line": latest.get('macd_line', 0),
                    "macd_signal": latest.get('macd_signal', 0),
                    "bb_upper": latest.get('bb_upper', 0),
                    "bb_lower": latest.get('bb_lower', 0)
                })
                print(f"[DEBUG] Latest indicators passed to technical agent: RSI={latest.get('rsi')}, MACD={latest.get('macd_line')}")
            
        elif agent_name == "sentiment":
            # Sentiment agent gets only sentiment metrics
            sentiment_info = market_data.get("sentiment_data", {})
            base_data.update({
                "bid_ask_ratio": sentiment_info.get("bid_ask_ratio", 1.0),
                "buy_sell_ratio": sentiment_info.get("buy_sell_ratio", 1.0),
                "order_book_depth": sentiment_info.get("order_book_depth", 0)
            })
            
        elif agent_name == "news":
            # News agent gets minimal news context
            pass  # News data would be added here
            
        elif agent_name == "risk":
            # Risk agent gets only volatility metrics
            volatility_info = market_data.get("volatility_metrics", {})
            base_data.update({
                "volatility_1d": volatility_info.get("volatility_1d", 0),
                "volatility_7d": volatility_info.get("volatility_7d", 0),
                "max_drawdown": volatility_info.get("max_drawdown", 0),
                "var_95": volatility_info.get("var_95", 0)
            })
        
        elif agent_name == "trading":
            # Trading agent gets full market data for unified signal generation
            historical_data = market_data.get("historical_data")
            if historical_data is not None and not historical_data.empty:
                base_data["historical_data"] = historical_data
            
            # Add all market data for comprehensive signal analysis
            base_data.update({
                "multi_timeframe": market_data.get("multi_timeframe", {}),
                "sentiment_data": market_data.get("sentiment_data", {}),
                "volatility_metrics": market_data.get("volatility_metrics", {}),
                "liquidity_score": market_data.get("liquidity_score", 0)
            })
        
        # Add minimal position data if provided
        if position_data:
            base_data.update({
                "position_size": position_data.get("position_size", 0.1),
                "entry_price": position_data.get("entry_price", base_data["current_price"])
            })
        else:
            # Default minimal position data
            base_data.update({
                "position_size": 0.1,
                "entry_price": base_data["current_price"],
                "available_cash": self.config.initial_balance * 0.5
            })
        
        return base_data
    
    def _summarize_agent_reports(self, agent_results: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
        """Summarize agent reports to reduce token usage."""
        summaries = {}
        for agent_name, result in agent_results.items():
            if isinstance(result, dict) and result.get("success"):
                analysis = result.get("analysis", {})
                if isinstance(analysis, dict):
                    # Extract only key metrics for synthesis
                    if agent_name == "technical":
                        summaries[agent_name] = f"Score: {analysis.get('technical_score', 50)}, Trend: {analysis.get('trend', 'neutral')}"
                    elif agent_name == "sentiment":
                        summaries[agent_name] = f"Score: {analysis.get('sentiment_score', 50)}, Sentiment: {analysis.get('overall_sentiment', 'neutral')}"
                    elif agent_name == "news":
                        summaries[agent_name] = f"Score: {analysis.get('news_score', 50)}, Impact: {analysis.get('news_impact', 'neutral')}"
                    elif agent_name == "risk":
                        summaries[agent_name] = f"Risk: {analysis.get('risk_score', 50)}, Level: {analysis.get('risk_level', 'medium')}"
                    elif agent_name == "trading":
                        # Handle simplified trading agent results
                        trading_strategy = analysis.get('trading_strategy', {})
                        if isinstance(trading_strategy, dict):
                            recommendation = trading_strategy.get('recommendation', 'HOLD')
                            signal_strength = trading_strategy.get('signal_strength', 0)
                            summaries[agent_name] = f"Action: {recommendation}, Strength: {signal_strength:.2f}"
                        else:
                            summaries[agent_name] = f"Action: {analysis.get('position_direction', 'HOLD')}"
                    else:
                        summaries[agent_name] = str(analysis.get("summary", ""))[:100]
                else:
                    summaries[agent_name] = str(analysis)[:100]
            else:
                summaries[agent_name] = f"Failed: {result.get('error', 'Unknown')}"
        return summaries

    def _generate_investment_commentary(self, symbol: str, market_data: Dict[str, Any], agent_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive investment commentary based on all agent analyses."""
        try:
            # Extract key data points from market data and agent results
            current_price = market_data.get('current_price', 0)
            # Try both key variations for price change
            price_change = market_data.get('price_change', market_data.get('price_change_24h', 0))
            price_change_pct = market_data.get('price_change_percent', 0)
            
            # Debug: Log the values being used for Investment Commentary
            logging.getLogger(__name__).info(f"Investment Commentary data - Price: {current_price}, Change: {price_change}, Change %: {price_change_pct}")
            logging.getLogger(__name__).info(f"Available market_data keys for commentary: {list(market_data.keys())}")
            
            # Get insights from each agent
            technical_insights = agent_results.get('technical_agent', {}).get('analysis', 'No technical analysis available')
            sentiment_insights = agent_results.get('sentiment_agent', {}).get('analysis', 'No sentiment analysis available')
            news_insights = agent_results.get('news_agent', {}).get('analysis', 'No news analysis available')
            risk_insights = agent_results.get('risk_agent', {}).get('analysis', 'No risk analysis available')
            # Handle simplified trading agent results
            trading_result = agent_results.get('trading', {})
            if trading_result.get('success') and 'trading_strategy' in trading_result:
                trading_strategy = trading_result['trading_strategy']
                if isinstance(trading_strategy, dict):
                    recommendation = trading_strategy.get('recommendation', 'HOLD')
                    reasoning = trading_strategy.get('reasoning', 'No reasoning provided')
                    trading_insights = f"Recommendation: {recommendation}. {reasoning}"
                else:
                    trading_insights = str(trading_strategy)
            else:
                trading_insights = agent_results.get('trading_agent', {}).get('analysis', 'No trading analysis available')
            
            # Create prompt for investment commentary
            prompt = f"""Generate a comprehensive investment commentary for {symbol} at ${current_price:.2f} (24h change: {price_change_pct:.2f}%).
            
            Synthesize the following agent analyses into a cohesive investment commentary:
            
            Technical Analysis: {technical_insights[:500]}...
            
            Sentiment Analysis: {sentiment_insights[:500]}...
            
            News Analysis: {news_insights[:500]}...
            
            Risk Analysis: {risk_insights[:500]}...
            
            Trading Analysis: {trading_insights[:500]}...
            
            Structure the investment commentary with these sections:
            1. Market Assessment - Overall market conditions and trends
            2. Research Synthesis - Key findings from all analyses
            3. Historical Context - How current conditions compare to past market cycles
            4. Scenario Analysis - Potential future scenarios and probabilities
            5. Risk Considerations - Key risks to monitor
            6. Market Education - Key learning points about market behavior
            7. Monitoring Framework - Important metrics to track
            
            Format the commentary with markdown, including tables where appropriate.
            Title it "Investment Commentary" and include the current price and trend.
            """
            
            # Generate investment commentary
            response = self.llm_client.generate_response([{"role": "user", "content": prompt}])
            
            if isinstance(response, dict) and 'content' in response:
                return {
                    'success': True,
                    'symbol': symbol,
                    'content': response['content'],
                    'raw_analysis': response['content']
                }
            else:
                logging.getLogger(__name__).warning(f"Failed to generate investment commentary for {symbol}")
                return None
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Error generating investment commentary for {symbol}: {e}")
            return None
    
    def _synthesize_decision(
        self, 
        symbol: str, 
        agent_results: Dict[str, Dict[str, Any]], 
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize final trading decision from agent analyses."""
        try:
            # Summarize agent reports to reduce token usage
            agent_summaries = self._summarize_agent_reports(agent_results)
            
            # Create synthesis prompt with summarized data
            messages = self.prompt_manager.create_decision_synthesis_prompt(
                symbol=symbol,
                agent_reports=agent_summaries,
                market_context={
                    "current_price": market_data["current_price"],
                    "market_conditions": self._assess_market_conditions(market_data),
                    "available_capital": self.config.initial_balance * 0.5
                }
            )
            
            # Get LLM decision
            llm_result = self.llm_client.generate_response(messages)
            
            if llm_result["success"]:
                decision = self._parse_final_decision(llm_result["content"])
            else:
                # Fallback to rule-based decision
                decision = {"action": "hold", "confidence": 0.5}
                decision.update(self._calculate_decision_metrics(agent_results))
            
            # Store the raw LLM content for display
            decision["llm_analysis"] = llm_result.get("content", "")
            
            return decision
        except Exception as e:
            logging.getLogger(__name__).error(f"Error synthesizing decision: {e}")
            return self._fallback_decision(agent_results, market_data)
    
    def _assess_market_conditions(self, market_data: Dict[str, Any]) -> str:
        """Assess overall market conditions."""
        try:
            volatility_metrics = market_data.get("volatility_metrics", {})
            volatility = volatility_metrics.get("volatility_1d", 0) if isinstance(volatility_metrics, dict) else 0
            price_change = market_data.get("price_change_24h", 0)
            
            if volatility > 0.1:
                vol_desc = "High Volatility"
            elif volatility > 0.05:
                vol_desc = "Medium Volatility"
            else:
                vol_desc = "Low Volatility"
            
            if price_change > 5:
                trend_desc = "Strong Uptrend"
            elif price_change > 2:
                trend_desc = "Uptrend"
            elif price_change < -5:
                trend_desc = "Strong Downtrend"
            elif price_change < -2:
                trend_desc = "Downtrend"
            else:
                trend_desc = "Sideways"
            
            return f"{trend_desc}, {vol_desc}"
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error assessing market conditions: {e}")
            return "Unknown Market Conditions"
    
    def _parse_final_decision(self, llm_response: str) -> Dict[str, Any]:
        """Parse final decision from LLM response."""
        try:
            decision = {
                "action": "hold",
                "confidence": 0.5,
                "reasoning": llm_response[:200] + "..." if len(llm_response) > 200 else llm_response,
                "position_size": 0.05,
                "stop_loss": None,
                "take_profit": None,
                "timeline": "short-term"
            }
            
            response_lower = llm_response.lower()
            
            # Extract action
            if "strong buy" in response_lower:
                decision["action"] = "strong_buy"
            elif "buy" in response_lower:
                decision["action"] = "buy"
            elif "strong sell" in response_lower:
                decision["action"] = "strong_sell"
            elif "sell" in response_lower:
                decision["action"] = "sell"
            
            # Extract confidence (look for numbers 1-10)
            import re
            confidence_match = re.search(r'confidence[:\s]+(\d+)', response_lower)
            if confidence_match:
                confidence_num = int(confidence_match.group(1))
                decision["confidence"] = min(10, max(1, confidence_num)) / 10.0
            
            return decision
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error parsing final decision: {e}")
            return {"action": "hold", "confidence": 0.5, "reasoning": "Decision parsing failed"}
    
    def _calculate_decision_metrics(self, agent_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate quantitative metrics for the decision."""
        try:
            metrics = {
                "technical_score": 50,
                "sentiment_score": 50,
                "news_score": 50,
                "risk_score": 50,
                "overall_score": 50
            }
            
            # Extract scores from agent results - check if agent result is dict
            if "technical" in agent_results and isinstance(agent_results["technical"], dict) and agent_results["technical"].get("success"):
                metrics["technical_score"] = agent_results["technical"].get("technical_score", 50)
            
            if "sentiment" in agent_results and isinstance(agent_results["sentiment"], dict) and agent_results["sentiment"].get("success"):
                metrics["sentiment_score"] = agent_results["sentiment"].get("sentiment_score", 50)
            
            if "news" in agent_results and isinstance(agent_results["news"], dict) and agent_results["news"].get("success"):
                metrics["news_score"] = agent_results["news"].get("news_score", 50)
            
            if "risk" in agent_results and isinstance(agent_results["risk"], dict) and agent_results["risk"].get("success"):
                metrics["risk_score"] = 100 - agent_results["risk"].get("risk_score", 50)  # Invert risk score
            
            # Handle simplified trading agent results
            if "trading" in agent_results and isinstance(agent_results["trading"], dict) and agent_results["trading"].get("success"):
                trading_result = agent_results["trading"]
                trading_strategy = trading_result.get('trading_strategy', {})
                if isinstance(trading_strategy, dict):
                    signal_strength = trading_strategy.get('signal_strength', 0.5)
                    trading_score = signal_strength * 100  # Convert to 0-100 scale
                    
                    # Adjust score based on recommendation
                    recommendation = trading_strategy.get('recommendation', 'HOLD').upper()
                    if recommendation == 'BUY':
                        trading_score = max(trading_score, 70)  # Ensure BUY gets at least 70
                    elif recommendation == 'SELL':
                        trading_score = min(trading_score, 30)  # Ensure SELL gets at most 30
                    # HOLD stays as signal_strength * 100
                    
                    metrics["trading_score"] = trading_score
                else:
                    metrics["trading_score"] = 50
            
            # Calculate overall score (weighted average) - include trading score
            weights = {"technical": 0.3, "trading": 0.3, "sentiment": 0.15, "news": 0.15, "risk": 0.1}
            total_score = 0
            total_weight = 0
            
            for agent, weight in weights.items():
                if f"{agent}_score" in metrics:
                    total_score += metrics[f"{agent}_score"] * weight
                    total_weight += weight
            
            if total_weight > 0:
                metrics["overall_score"] = total_score / total_weight
            
            return metrics
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error calculating decision metrics: {e}")
            return {"overall_score": 50}
    
    def _fallback_decision(self, agent_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Return no decision when LLM synthesis fails - no fallback decisions."""
        return {"action": None, "confidence": 0.0, "reasoning": "No decision available - LLM synthesis required"}
    
    def _calculate_overall_confidence(self, agent_results: Dict[str, Dict[str, Any]]) -> float:
        """Calculate overall confidence from agent results."""
        try:
            confidences = []
            
            for agent_name, result in agent_results.items():
                if result.get("success") and "confidence" in result:
                    confidences.append(result["confidence"])
            
            if confidences:
                return sum(confidences) / len(confidences)
            else:
                return 0.5
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Error calculating overall confidence: {e}")
            return 0.5
    
    def _store_prediction(self, prediction_result: Dict[str, Any]):
        """Store prediction result in history."""
        try:
            self.last_prediction = prediction_result
            self.prediction_history.append(prediction_result)
            
            # Keep only recent history
            max_history = 100
            if len(self.prediction_history) > max_history:
                self.prediction_history = self.prediction_history[-max_history:]
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Error storing prediction: {e}")
    
    def get_prediction_history(self, symbol: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get prediction history, optionally filtered by symbol."""
        try:
            history = self.prediction_history
            
            if symbol:
                history = [p for p in history if p.get("symbol") == symbol]
            
            return history[-limit:] if history else []
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error getting prediction history: {e}")
            return []
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        try:
            status = {}
            for agent_name, agent in self.agents.items():
                status[agent_name] = agent.get_agent_status()
            
            return {
                "agents": status,
                "total_predictions": len(self.prediction_history),
                "last_prediction": self.last_prediction.get("timestamp") if self.last_prediction else None,
                "llm_endpoint": self.config.llm_endpoint
            }
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error getting agent status: {e}")
            return {"error": str(e)}
    
    async def test_system(self) -> Dict[str, Any]:
        """Test the entire prediction system."""
        try:
            results = {"overall": True, "components": {}}
            
            # Test LLM connection
            llm_test = self.llm_client.test_connection()
            results["components"]["llm"] = llm_test["success"]
            
            # Test each agent
            for agent_name, agent in self.agents.items():
                agent_test = agent.test_agent()
                results["components"][agent_name] = agent_test["success"]
                if not agent_test["success"]:
                    results["overall"] = False
            
            # Test market data
            try:
                test_data = await self.market_data.get_market_overview(["BTCUSDT"])
                results["components"]["market_data"] = bool(test_data)
            except Exception as e:
                results["components"]["market_data"] = False
                results["overall"] = False
            
            return results
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error testing system: {e}")
            return {"overall": False, "error": str(e)}
    
    def close(self):
        """Clean up resources."""
        try:
            self.llm_client.close()
            for agent in self.agents.values():
                if hasattr(agent, 'close'):
                    agent.close()
            logging.getLogger(__name__).info("Prediction engine closed")
        except Exception as e:
            logging.getLogger(__name__).error(f"Error closing prediction engine: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
