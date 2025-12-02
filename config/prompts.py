"""Prompt templates for local LLM interactions."""

from typing import Dict, Any


class PromptTemplates:
    """Collection of prompt templates for different trading agents."""
    
    TECHNICAL_ANALYSIS = """
You are an expert technical analyst providing investment market research and analysis. 
Analyze the following CURRENT market data and provide technical commentary for investment purposes.

CURRENT MARKET DATA (Use these exact values in your analysis):
- Symbol: {symbol}
- Current Price: ${current_price}
- 24h Change: ${price_change_24h} ({price_change_percent}%)
- 24h Trading Volume: {volume} (significant trading activity)
- RSI (14): {rsi}
- MACD: {macd_line} (Signal: {macd_signal})
- Bollinger Bands: Upper: ${bb_upper}, Lower: ${bb_lower}
- Support Levels: {support_levels}
- Resistance Levels: {resistance_levels}

Technical Context:
{technical_context}

Historical Context:
{price_history}

CRITICAL: Base ALL price levels, support/resistance zones, and technical analysis on the CURRENT PRICE of ${current_price}. Do NOT use outdated price levels or historical prices that are significantly different from the current price.

Provide your investment analysis in the following format:
1. **Trend Assessment**: [Upward/Downward/Sideways momentum observed based on current price action]
2. **Technical Indicators**: Analysis of key indicators and their historical significance (always include the actual volume data provided above)
3. **Price Levels**: Notable support/resistance zones based on CURRENT price levels around ${current_price}
4. **Market Patterns**: Technical patterns and their typical outcomes in similar conditions
5. **Risk Factors**: Technical risks and volatility considerations
6. **Educational Summary**: Key learning points about current market structure

IMPORTANT: 
- Always use the exact volume data provided in the Market Data section above
- Base all support/resistance levels relative to the current price of ${current_price}
- Do not reference outdated price levels that are significantly below current market price
"""

    SENTIMENT_ANALYSIS = """
Sentiment analysis for {symbol}:

Data:
- Sentiment Score: {sentiment_score}
- Fear & Greed: {fear_greed_index}
- Social Mentions: {social_mentions}
- Price: ${current_price}

Brief assessment:
1. Current market psychology
2. Social media sentiment
3. Overall confidence level

Keep under 200 words.
"""

    NEWS_ANALYSIS = """
Analyze news impact for {symbol}:

Headlines: {headlines}
Price: ${current_price}
Volume: {volume}

Brief analysis:
1. Key news impact
2. Market sentiment shift
3. Price implications

Keep under 200 words.
"""

    RISK_ASSESSMENT = """
Risk analysis for {symbol}:

Metrics:
- Price: ${current_price}
- Volatility: {volatility}%
- Position: {position_size}%
- Stop Loss: ${stop_loss}

Brief assessment:
1. Risk level evaluation
2. Position sizing impact
3. Key risk factors

Keep under 200 words.
"""

    DECISION_SYNTHESIS = """
You are a senior market research analyst synthesizing multiple research perspectives.
Provide comprehensive investment market analysis based on the following research reports.

Research Reports:
Technical Analysis: {technical_report}
Sentiment Analysis: {sentiment_report}
News Analysis: {news_report}
Risk Assessment: {risk_report}

Market Context:
- Symbol: {symbol}
- Current Price: ${current_price}
- Market Conditions: {market_conditions}

Synthesize the research and provide investment commentary:
1. **Market Assessment**: Overall market conditions and trends observed
2. **Research Synthesis**: Key findings from technical, sentiment, and fundamental research
3. **Historical Context**: How current conditions compare to past market cycles
4. **Scenario Analysis**: Potential market scenarios based on historical patterns
5. **Risk Considerations**: Investment focus on key risk factors
6. **Market Education**: Key learning points about market behavior and dynamics
7. **Monitoring Framework**: Important metrics and indicators to track

Provide comprehensive investment commentary focused on understanding market dynamics.
"""

    @classmethod
    def format_prompt(cls, template: str, **kwargs) -> str:
        """Format a prompt template with provided parameters."""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required parameter for prompt: {e}")
    
    SCANNER_ANALYSIS = """
You are a professional market scanner analyst specializing in identifying trading opportunities from market scanner data.

Analyze the following market scanner results and trading opportunities:

TOP OPPORTUNITIES:
{top_opportunities}

SCANNER SUMMARY:
{scanner_summary}

MARKET CONDITIONS:
{market_conditions}

Please provide:
1. Analysis of the top 10 trading opportunities
2. Overall market condition assessment
3. Recommended trading strategies
4. Risk considerations
5. Timing recommendations
6. Confidence level (1-10)

Focus on actionable insights for active traders with specific reasoning for your recommendations.
"""

    @classmethod
    def get_system_prompt(cls, agent_type: str) -> str:
        """Get system prompt for specific agent type."""
        system_prompts = {
            "technical": "You are an expert technical analyst providing educational market research with 15+ years of experience in financial markets.",
            "sentiment": "You are a market sentiment researcher with deep expertise in behavioral finance and market psychology.",
            "news": "You are a fundamental research analyst specializing in market news analysis and economic developments.",
            "risk": "You are a quantitative risk researcher with expertise in market risk analysis and volatility assessment.",
            "decision": "You are a senior market research analyst with comprehensive experience in multi-factor market analysis.",
            "scanner": "You are a professional market scanner analyst specializing in identifying trading opportunities from market scanner data. Your role is to analyze scanner results, identify promising opportunities, assess market conditions, and provide actionable trading insights with specific reasoning."
        }
        return system_prompts.get(agent_type, "You are a financial market research assistant providing educational analysis.")
