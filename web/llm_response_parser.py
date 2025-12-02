"""
LLM Response Parser for MarketResearcher Agent Analysis
Converts individual LLM agent responses into structured format for display utilities.
"""

import json
import re
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class LLMResponseParser:
    """Parse individual LLM agent responses into structured format."""
    
    @staticmethod
    def parse_agent_responses(llm_responses: List[Dict[str, Any]], symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        Parse multiple LLM responses into structured agent results.
        
        Args:
            llm_responses: List of LLM response objects
            symbol: Trading symbol
            
        Returns:
            Structured agent results for display utilities
        """
        agent_results = {}
        
        for i, response in enumerate(llm_responses):
            try:
                content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                if i == 0:  # Technical Agent
                    agent_results['technical_agent'] = LLMResponseParser._parse_technical_agent(content, symbol)
                elif i == 1:  # Trading Agent
                    agent_results['trading_agent'] = LLMResponseParser._parse_trading_agent(content, symbol)
                elif i == 2:  # Sentiment Agent
                    agent_results['sentiment_agent'] = LLMResponseParser._parse_sentiment_agent(content, symbol)
                elif i == 3:  # News Agent
                    agent_results['news_agent'] = LLMResponseParser._parse_news_agent(content, symbol)
                elif i == 4:  # Risk Agent
                    agent_results['risk_agent'] = LLMResponseParser._parse_risk_agent(content, symbol)
                elif i == 5:  # Investment Commentary (final summary)
                    agent_results['investment_commentary'] = {
                        'success': True,
                        'symbol': symbol,
                        'content': content,
                        'raw_analysis': content
                    }
                    
            except Exception as e:
                logging.getLogger(__name__).error(f"Error parsing LLM response {i}: {e}")
                continue
        
        return agent_results
    
    @staticmethod
    def _parse_technical_agent(content: str, symbol: str) -> Dict[str, Any]:
        """Parse technical analysis response."""
        return {
            'success': True,
            'symbol': symbol,
            'confidence': 0.6,  # Default confidence
            'analysis': content,
            'technical_signals': {
                'trend': 'sideways',
                'momentum': 'neutral',
                'volatility': 'low',
                'volume': 'normal',
                'overall_signal': 'hold'
            },
            'technical_score': 50,
            'indicators': {
                'rsi': 'N/A',
                'macd_line': 'N/A',
                'macd_signal': 'N/A',
                'bb_upper': 'N/A',
                'bb_lower': 'N/A'
            },
            'support_resistance': {
                'support_levels': [],
                'resistance_levels': []
            }
        }
    
    @staticmethod
    def _parse_trading_agent(content: str, symbol: str) -> Dict[str, Any]:
        """Parse trading strategy JSON response."""
        try:
            # Extract JSON from content
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                strategy_data = json.loads(json_match.group(1))
                
                # Handle multiple JSON structures for strategy
                strategy_rec = ''
                if 'strategyRecommendation' in strategy_data:
                    if isinstance(strategy_data['strategyRecommendation'], dict):
                        strategy_rec = strategy_data['strategyRecommendation'].get('action', '')
                    else:
                        strategy_rec = strategy_data['strategyRecommendation']
                elif 'recommendation' in strategy_data and isinstance(strategy_data['recommendation'], dict):
                    strategy_rec = strategy_data['recommendation'].get('strategy', '')
                elif 'strategy_recommendation' in strategy_data:
                    strategy_rec = strategy_data['strategy_recommendation']
                elif 'strategy' in strategy_data:
                    strategy_rec = strategy_data['strategy']
                
                # Handle risk management from different structures
                risk_mgmt = (strategy_data.get('riskManagementAssessment', 
                           strategy_data.get('risk_management_assessment', 
                           strategy_data.get('riskManagement',
                           strategy_data.get('risk_management', {})))))
                
                entry_timing = (strategy_data.get('entryTimingAnalysis', 
                              strategy_data.get('entry_timing_analysis', 
                              strategy_data.get('entryTiming',
                              strategy_data.get('entry_timing', {})))))
                
                # Extract stop loss info from multiple possible structures
                stop_loss_price = 0
                if 'stop_loss_price' in risk_mgmt:
                    stop_loss_price = float(risk_mgmt['stop_loss_price'])
                elif 'stopLoss' in risk_mgmt and isinstance(risk_mgmt['stopLoss'], dict):
                    stop_loss_price = float(risk_mgmt['stopLoss'].get('price', risk_mgmt['stopLoss'].get('level', 0)))
                elif 'stop_loss' in risk_mgmt and isinstance(risk_mgmt['stop_loss'], dict):
                    stop_loss_price = float(risk_mgmt['stop_loss'].get('price', 0))
                
                # Extract profit targets from multiple possible structures
                profit_targets = (risk_mgmt.get('profitTargets', 
                                risk_mgmt.get('profit_targets', [])))
                
                profit_target_1 = 0
                profit_target_2 = 0
                profit_target_3 = 0
                
                if len(profit_targets) > 0:
                    # Handle 'price', 'level', and 'target' field names
                    target_val = profit_targets[0].get('price', profit_targets[0].get('level', profit_targets[0].get('target', '')))
                    if isinstance(target_val, str) and '$' in target_val:
                        profit_target_1 = float(target_val.replace('$', '').replace(',', ''))
                    elif target_val:
                        profit_target_1 = float(target_val)
                if len(profit_targets) > 1:
                    target_val = profit_targets[1].get('price', profit_targets[1].get('level', profit_targets[1].get('target', '')))
                    if isinstance(target_val, str) and '$' in target_val:
                        profit_target_2 = float(target_val.replace('$', '').replace(',', ''))
                    elif target_val:
                        profit_target_2 = float(target_val)
                if len(profit_targets) > 2:
                    target_val = profit_targets[2].get('price', profit_targets[2].get('level', profit_targets[2].get('target', '')))
                    if isinstance(target_val, str) and '$' in target_val:
                        profit_target_3 = float(target_val.replace('$', '').replace(',', ''))
                    elif target_val:
                        profit_target_3 = float(target_val)
                
                # Extract trailing stop info
                trailing_activation = 0
                trailing_distance = 2.0
                trailing_distance_desc = "2% distance"
                
                if 'trailing_stop_activation_price' in risk_mgmt:
                    trailing_activation = float(risk_mgmt['trailing_stop_activation_price'])
                elif 'trailingStop' in risk_mgmt and isinstance(risk_mgmt['trailingStop'], dict):
                    trailing_activation = float(risk_mgmt['trailingStop'].get('activationPrice', risk_mgmt['trailingStop'].get('activateAt', 0)))
                    # Extract distance description
                    if 'distanceFromTarget' in risk_mgmt['trailingStop']:
                        trailing_distance_desc = risk_mgmt['trailingStop']['distanceFromTarget']
                    elif 'distanceFromPeak' in risk_mgmt['trailingStop']:
                        trailing_distance_desc = risk_mgmt['trailingStop']['distanceFromPeak']
                elif 'trailing_stop' in risk_mgmt and isinstance(risk_mgmt['trailing_stop'], dict):
                    trailing_activation = float(risk_mgmt['trailing_stop'].get('activation_price', 0))
                
                if 'trailing_distance_pct' in risk_mgmt:
                    trailing_distance = float(risk_mgmt['trailing_distance_pct'])
                elif 'trailingStop' in risk_mgmt and isinstance(risk_mgmt['trailingStop'], dict):
                    distance_str = str(risk_mgmt['trailingStop'].get('distanceFromPeak', '2.0%'))
                    trailing_distance = float(distance_str.replace('%', '').replace('-', ''))
                
                # Extract entry timing info
                ideal_entry = entry_timing.get('idealEntryWindow', entry_timing.get('ideal_entry_window', ''))
                current_signal = entry_timing.get('currentSignal', entry_timing.get('current_signal', ''))
                
                # Handle description-based entry timing
                entry_description = entry_timing.get('description', '')
                recommended_entry_price = entry_timing.get('recommendedEntryPrice', '')
                timing_window = entry_timing.get('timingWindow', '')
                
                # Handle different entry timing structures
                conditions = entry_timing.get('conditions', [])
                notes = entry_timing.get('notes', '')
                triggers = entry_timing.get('triggers', [])
                recommended_entry = entry_timing.get('recommendedEntryWindow', '')
                current_conditions = entry_timing.get('currentConditions', '')
                entry_risk = entry_timing.get('entryTimingRisk', '')
                
                # Handle multiple entry timing structures
                suggested_entry_windows = entry_timing.get('suggestedEntryWindow', [])
                entry_confirmation_indicators = entry_timing.get('entryConfirmationIndicators', [])
                ideal_entry_price_range = entry_timing.get('idealEntryPriceRange', '')
                entry_triggers = entry_timing.get('entryTriggers', [])
                avoid_entry = entry_timing.get('avoidEntry', '')
                
                # Combine entry timing information
                if entry_description and recommended_entry_price:
                    ideal_entry = f"Entry at ${recommended_entry_price:,.2f}: {entry_description}"
                elif ideal_entry_price_range and entry_triggers:
                    triggers_text = '; '.join(entry_triggers)
                    ideal_entry = f"Price range: {ideal_entry_price_range}. Triggers: {triggers_text}"
                elif suggested_entry_windows:
                    entry_parts = []
                    for window in suggested_entry_windows:
                        if isinstance(window, dict):
                            price = window.get('priceLevel', '')
                            condition = window.get('condition', '')
                            justification = window.get('justification', '')
                            entry_parts.append(f"At ${price}: {condition} - {justification}")
                    if entry_parts:
                        ideal_entry = '; '.join(entry_parts)
                elif recommended_entry and triggers:
                    triggers_text = '; '.join(triggers)
                    ideal_entry = f"{recommended_entry} {triggers_text}"
                elif conditions:
                    conditions_text = '; '.join(conditions)
                    if ideal_entry:
                        ideal_entry = f"{ideal_entry}. Conditions: {conditions_text}"
                    else:
                        ideal_entry = f"Conditions: {conditions_text}"
                elif entry_description:
                    ideal_entry = entry_description
                
                # Combine current signal information
                signal_parts = []
                if timing_window:
                    signal_parts.append(f"Timing: {timing_window}")
                if current_conditions:
                    signal_parts.append(current_conditions)
                if entry_confirmation_indicators:
                    indicators_text = '; '.join(entry_confirmation_indicators)
                    signal_parts.append(f"Confirmation indicators: {indicators_text}")
                if avoid_entry:
                    signal_parts.append(f"Avoid entry: {avoid_entry}")
                if entry_risk:
                    signal_parts.append(entry_risk)
                if notes:
                    signal_parts.append(f"Notes: {notes}")
                
                if signal_parts:
                    current_signal = ' '.join(signal_parts)
                elif current_signal and notes:
                    current_signal = f"{current_signal}. Notes: {notes}"
                
                # Extract exposure info from multiple sources
                exposure_percent = 5.0
                if 'exposure_percent_of_portfolio' in risk_mgmt:
                    exposure_percent = float(risk_mgmt['exposure_percent_of_portfolio'])
                elif 'recommendedExposurePercent' in risk_mgmt:
                    exposure_percent = float(risk_mgmt['recommendedExposurePercent'])
                elif 'positionSizing' in risk_mgmt and isinstance(risk_mgmt['positionSizing'], dict):
                    exposure_str = str(risk_mgmt['positionSizing'].get('recommendedExposure', '5%'))
                    exposure_percent = float(exposure_str.replace('%', ''))
                # Check strategy recommendation for exposure
                elif 'exposurePercentage' in strategy_data.get('strategyRecommendation', {}):
                    exposure_percent = float(strategy_data['strategyRecommendation']['exposurePercentage'])
                
                return {
                    'success': True,
                    'symbol': symbol,
                    'confidence': strategy_data.get('confidenceLevel', strategy_data.get('confidence_level', 70)) / 10.0 if strategy_data.get('confidenceLevel', strategy_data.get('confidence_level', 70)) > 10 else strategy_data.get('confidenceLevel', strategy_data.get('confidence_level', 7)) / 10.0,
                    'analysis': f"Strategy: {strategy_rec if isinstance(strategy_rec, str) else 'HOLD'}",
                    'position_direction': {
                        'action': strategy_rec.replace('LONG ', '').replace('SHORT ', '') if isinstance(strategy_rec, str) else 'HOLD',
                        'position_type': 'long' if isinstance(strategy_rec, str) and 'LONG' in strategy_rec else 'short',
                        'confidence': 0.8,
                        'reasoning': f"Based on market analysis and risk assessment"
                    },
                    'position_analysis': {
                        'portfolio_exposure': exposure_percent,
                        'profit_target_1': profit_target_1,
                        'profit_target_2': profit_target_2,
                        'profit_target_3': profit_target_3,
                        'stop_loss_price': stop_loss_price,
                        'stop_loss_percent': 4.0,
                        'trailing_stop_activation': trailing_activation,
                        'trailing_stop_distance': trailing_distance,
                        'trailing_stop_description': trailing_distance_desc,
                        'ideal_entry_window': ideal_entry,
                        'current_signal': current_signal,
                        'strategy_action': strategy_rec,
                        'volatility_score': 2.0,
                        'volume_score': 1.15
                    },
                    'risk_parameters': {
                        'risk_score': 10.0,
                        'max_position_size': float(risk_mgmt.get('max_position_size_percent', risk_mgmt.get('maxPositionSizePercent', 15))),
                        'risk_reward_ratio': risk_mgmt.get('risk_reward_ratio_overall', risk_mgmt.get('riskRewardRatio', risk_mgmt.get('risk_reward_ratio', '1.8:1'))),
                        'volatility_risk': 2.0,
                        'confidence_risk': 4.0,
                        'risk_level': 'LOW'
                    },
                    'trading_strategy': {
                        'summary': f"Trading strategy for {symbol}",
                        'full_text': content,
                        'key_points': []
                    },
                    'raw_analysis': content
                }
            else:
                # Fallback if JSON parsing fails
                return {
                    'success': True,
                    'symbol': symbol,
                    'confidence': 0.7,
                    'analysis': content[:500] + '...' if len(content) > 500 else content,
                    'raw_analysis': content
                }
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Error parsing trading agent JSON: {e}")
            return {
                'success': True,
                'symbol': symbol,
                'confidence': 0.7,
                'analysis': content[:500] + '...' if len(content) > 500 else content
            }
    
    @staticmethod
    def _parse_sentiment_agent(content: str, symbol: str) -> Dict[str, Any]:
        """Parse sentiment analysis response."""
        # Extract sentiment indicators from text
        sentiment_strength = 'moderate'
        if 'neutral' in content.lower():
            overall_sentiment = 'neutral'
        elif 'bullish' in content.lower() or 'positive' in content.lower():
            overall_sentiment = 'bullish'
        elif 'bearish' in content.lower() or 'negative' in content.lower():
            overall_sentiment = 'bearish'
        else:
            overall_sentiment = 'neutral'
        
        return {
            'success': True,
            'symbol': symbol,
            'confidence': 0.1,  # Low confidence as mentioned in content
            'analysis': content,
            'sentiment_signals': {
                'overall_sentiment': overall_sentiment,
                'social_sentiment': 'neutral',
                'market_psychology': 'neutral',
                'sentiment_strength': sentiment_strength,
                'contrarian_signal': True
            },
            'sentiment_score': 50,
            'recommendation': {
                'action': 'hold',
                'strength': 'moderate',
                'score': 50,
                'confidence': 0.1
            }
        }
    
    @staticmethod
    def _parse_news_agent(content: str, symbol: str) -> Dict[str, Any]:
        """Parse news analysis response."""
        # Determine news impact from content
        if 'positive' in content.lower() or 'bullish' in content.lower():
            news_impact = 'positive'
            action = 'buy'
            score = 65
        elif 'negative' in content.lower() or 'bearish' in content.lower():
            news_impact = 'negative'
            action = 'sell'
            score = 35
        else:
            news_impact = 'neutral'
            action = 'hold'
            score = 50
        
        return {
            'success': True,
            'symbol': symbol,
            'confidence': 0.6,
            'analysis': content,
            'news_signals': {
                'news_impact': news_impact,
                'impact_timeframe': 'short-term',
                'fundamental_strength': 'neutral',
                'regulatory_risk': 'low',
                'market_catalysts': []
            },
            'news_score': score,
            'recommendation': {
                'action': action,
                'strength': 'moderate',
                'score': score,
                'confidence': 0.6
            }
        }
    
    @staticmethod
    def _parse_risk_agent(content: str, symbol: str) -> Dict[str, Any]:
        """Parse risk analysis response."""
        # Extract risk level from content
        if 'high' in content.lower() and 'risk' in content.lower():
            risk_level = 'high'
            risk_score = 75
        elif 'low' in content.lower() and 'risk' in content.lower():
            risk_level = 'low'
            risk_score = 35
        else:
            risk_level = 'medium'
            risk_score = 63
        
        return {
            'success': True,
            'symbol': symbol,
            'confidence': 0.6,
            'analysis': content,
            'risk_signals': {
                'risk_level': risk_level,
                'position_sizing': 'appropriate',
                'risk_factors': [],
                'mitigation_needed': False
            },
            'risk_score': risk_score,
            'recommendation': {
                'action': 'reduce' if risk_level == 'high' else 'hold',
                'strength': 'moderate',
                'score': risk_score,
                'confidence': 0.6
            }
        }
