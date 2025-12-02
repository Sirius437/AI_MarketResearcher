"""
Example integration showing how to use LLMResponseParser with the display utilities.
This demonstrates the complete flow from LLM responses to structured display.
"""

from llm_response_parser import LLMResponseParser
from analysis_display_utils import WebAnalysisDisplayUtils
import streamlit as st

# Example LLM responses (based on your actual log output)
example_llm_responses = [
    # Technical Agent Response
    {
        "choices": [{
            "message": {
                "content": """**1. Trend Assessment**  
- **Short‑term motion:** The 24‑hour dip of –0.46 % signals a modest pullback in the very near term.  
- **Medium/long‑term direction:** With no 30‑day price history or key oscillators available, we cannot confirm whether BTCUSDT is in an uptrend, downtrend, or range‑bound consolidation. A single daily move is insufficient to determine a sustained trend.

**2. Technical Indicators**  
| Indicator | Current Status | Typical Significance |
|-----------|-----------------|----------------------|
| RSI (14) | **N/A** | Overbought (>70) → potential reversal; Oversold (<30) → potential bounce. |
| MACD (12,26,9) | **N/A** | Bullish cross indicates buying momentum; bearish cross signals selling pressure. |
| Bollinger Bands | **Upper/Lower N/A** | Price touching the upper band often signals overbought conditions; lower band contact may signal oversold. |

*Bottom Line for Investors:*  
BTCUSDT is currently experiencing a slight short‑term decline at $110,988.28, but the lack of key technical inputs and historical price data means we cannot confidently assert any trend direction."""
            }
        }]
    },
    # Trading Agent Response
    {
        "choices": [{
            "message": {
                "content": """```json
{
  "strategyRecommendation": {
    "type": "LONG BUY",
    "description": "The current setup shows a potential bullish reversal at $110,988.28 with a 4% stop‑loss at $106,548.75 and multiple upside targets. The recommended exposure is low (1%) to keep risk minimal."
  },
  "riskManagementAssessment": {
    "positionSizing": {
      "recommendedExposure": "1%",
      "maxAllowedPosition": "15%"
    },
    "stopLossDetails": {
      "price": 106548.7488,
      "percentageFromEntry": "-4.0%"
    },
    "profitTargets": [
      {"price": 113208.0456, "expectedReturnPct": "+2.5%"},
      {"price": 116537.694, "expectedReturnPct": "+5.1%"},
      {"price": 122087.108, "expectedReturnPct": "+10.4%"}
    ],
    "trailingStop": {
      "activateAt": 112653.1042,
      "distanceFromPeak": "2.0%"
    },
    "riskRewardRatio": "2.4:1",
    "overallRiskScore": "6.0/100"
  },
  "confidenceLevel": 7
}
```"""
            }
        }]
    },
    # Sentiment Agent Response
    {
        "choices": [{
            "message": {
                "content": "BTCUSDT remains in a neutral zone—sentiment score zero and Fear & Greed at fifty reflect balanced emotions, neither bullish nor bearish. Social media shows no mentions, indicating minimal public chatter and limited sentiment data. With no clear signals or volume spikes, confidence in short‑term direction stays moderate."
            }
        }]
    },
    # News Agent Response
    {
        "choices": [{
            "message": {
                "content": "**Key news impact:** The Trump‑backed Bitcoin firm's 110 % debut created a short‑term buying spike but soon retreated, showing hype can be volatile. **Market sentiment shift:** Optimism is cooling as the $112 k ceiling appears firm; bearish October forecasts and SEC calls for quantum‑proofing add regulatory uncertainty, tilting sentiment toward caution. **Price implications:** Current $110,988 sits just below the psychological $112 k level—likely a short‑term support zone."
            }
        }]
    },
    # Risk Agent Response
    {
        "choices": [{
            "message": {
                "content": """Risk level evaluation: Minimal due to negligible position and reported zero volatility; yet a $0 stop‑loss exposes you to unlimited loss if price moves against you.
Position sizing impact: 0.1% exposure is trivial, but any adverse move magnifies the absolute loss because no downside protection exists.
Key risk factors: Market shock, liquidity dry‑up, exchange outage, regulatory crackdowns, and data integrity errors.
⚠️ Risk Signals:
Risk Level: Very Low
Position Sizing: Appropriate
Risk Factors: []
Mitigation Needed: No
Risk Score: 63/100
💡 Recommendation:
Action: REDUCE
Strength: Moderate
Score: 63/100
Confidence: 60.0%"""
            }
        }]
    },
    # Investment Commentary (Final Summary)
    {
        "choices": [{
            "message": {
                "content": """**Investment Commentary – BTCUSDT (USD‑Tether Pair)**  
*Current price:* **$112 353.24**  
*Market state (as of the latest tick):* Sideways, low volatility, neutral sentiment  

---

### 1. Market Assessment  
| Dimension | Observation | Implication |
|-----------|-------------|-------------|
| **Technical** | Momentum is flat; no clear trend. Price oscillates within a tight range around $112k‑$115k. | Expect continuation of consolidation until a decisive breakout or breakdown occurs. |
| **Sentiment** | Fear‑Greed Index ≈ 50 → equilibrium. No prevailing bullish or bearish bias among retail/ institutional players. | Market is "waiting" – small catalysts can tip the balance. |
| **Fundamental** | Sora Ventures launched a $1 B treasury fund that has entered BTC. Institutional capital flow suggests confidence in long‑term value. | Potential liquidity injection could support upward moves once price exits the current range. |
| **Risk Profile** | Volatility is near zero; exposure under 0.1% of portfolio. Stop‑loss at $0 (i.e., no hard stop) indicates a "hold‑and‑watch" stance. | Risk is minimal in the short term, but any sudden reversal could erode gains quickly if not protected. |

**Bottom line:** BTC is in a classic consolidation phase – neither trending nor emotional. The market is poised for either a breakout, a breakdown, or an extended sideways period.

---

### 2. Research Synthesis  
| Source | Key Findings |
|--------|--------------|
| **Technical Analysis** | Momentum neutral; price range $112k‑$115k; resistance at ~$116k, support near $110k. |
| **Sentiment Analysis** | Fear‑Greed = 50 → equilibrium; no dominant bias. |
| **News / Fundamental Analysis** | Sora Ventures' $1B treasury fund signals institutional confidence; may increase buying pressure. |
| **Risk Assessment** | Negligible volatility, 0.1% exposure; minimal risk but stop‑loss at $0 indicates potential for loss if price breaks support. |

---

### 3. Historical Context  
- **2019–2020:** BTC hovered around $8k–$11k with low volatility before a massive rally to ~ $60k in early 2021.  
- **2022‑23:** Decline to ~$20k, high volatility, then a sideways phase from late 2023 (~$30k) leading to a breakout toward ~$60k.  
- **Current Cycle (2024):** BTC at $112k, which is roughly midway between the 2017 peak ($19k) and the 2021 all‑time high ($69k). The market is in a *consolidation* stage after a bullish run since mid‑2023.  

**Takeaway:** Sideways periods historically precede large directional moves (either up or down). BTC's current consolidation mirrors past patterns that led to significant rallies."""
            }
        }]
    }
]

def demonstrate_llm_integration():
    """Demonstrate complete LLM response parsing and display."""
    
    # Parse LLM responses into structured format
    agent_results = LLMResponseParser.parse_agent_responses(example_llm_responses, "BTCUSDT")
    
    # Add Investment Commentary manually since it's missing from the agent results
    agent_results['investment_commentary'] = {
        'success': True,
        'symbol': 'BTCUSDT',
        'content': """**BTCUSDT – Investment Commentary (as of 05 Sep 2025)**  
*Price:* **$112 313.15**  
*Trend:* Sideways, low‑volatility regime  
*Key signal:* Sora Ventures' $1 B treasury fund inflow

---

## 1. Market Assessment  

| Dimension | Observation | Implication |
|-----------|-------------|-------------|
| **Technical** | Spot price sits near the mid‑point of a tight channel (112k–115k). 50‑day MA ≈ 113k, 200‑day MA ≈ 109k – both bullish but not yet divergent. | BTC is in a consolidation phase; breakout potential on either side. |
| **Sentiment** | Sentiment score = 0 (neutral), fear‑greed index = 50 (exactly balanced). | No clear market bias—traders are "waiting for the next move." |
| **Fundamental / News** | Sora Ventures' $1 B treasury fund is being deployed into BTC.  Institutional inflows have been steady over the past month, with on‑chain data showing a net purchase of ~0.5 M BTC in exchanges. | Positive pressure from large players; could act as support if price dips. |
| **Volatility** | Implied volatility (cryptovix) ≈ 18 % – lower than historical averages (~30–40 %). | Reduced risk‑premium, but also less "exciting" opportunities for swing traders. |

> **Bottom line:** BTC is in a *quiet consolidation* with **neutral sentiment** and **strong institutional backing**. The market is poised either to break out or continue sideways until an external catalyst (regulatory change, macro shock, technical trigger) nudges it.""",
        'raw_analysis': """**BTCUSDT – Investment Commentary (as of 05 Sep 2025)**  
*Price:* **$112 313.15**  
*Trend:* Sideways, low‑volatility regime  
*Key signal:* Sora Ventures' $1 B treasury fund inflow

---

## 1. Market Assessment  

| Dimension | Observation | Implication |
|-----------|-------------|-------------|
| **Technical** | Spot price sits near the mid‑point of a tight channel (112k–115k). 50‑day MA ≈ 113k, 200‑day MA ≈ 109k – both bullish but not yet divergent. | BTC is in a consolidation phase; breakout potential on either side. |
| **Sentiment** | Sentiment score = 0 (neutral), fear‑greed index = 50 (exactly balanced). | No clear market bias—traders are "waiting for the next move." |
| **Fundamental / News** | Sora Ventures' $1 B treasury fund is being deployed into BTC.  Institutional inflows have been steady over the past month, with on‑chain data showing a net purchase of ~0.5 M BTC in exchanges. | Positive pressure from large players; could act as support if price dips. |
| **Volatility** | Implied volatility (cryptovix) ≈ 18 % – lower than historical averages (~30–40 %). | Reduced risk‑premium, but also less "exciting" opportunities for swing traders. |

> **Bottom line:** BTC is in a *quiet consolidation* with **neutral sentiment** and **strong institutional backing**. The market is poised either to break out or continue sideways until an external catalyst (regulatory change, macro shock, technical trigger) nudges it."""
    }
    
    # Create mock result structure for display
    result = {
        'success': True,
        'symbol': 'BTCUSDT',
        'final_decision': {'action': 'HOLD'},
        'confidence': 0.5,
        'risk_score': 63.0,
        'agent_results': agent_results,
        'market_context': {
            'current_price': 110988.28,
            'price_change': -0.46,
            'price_change_percent': -0.46,
            'volume': 11450.5
        }
    }
    
    # Display using unified display utilities
    st.subheader(f"Analysis Results for {result['symbol']}")
    
    # Market context
    WebAnalysisDisplayUtils.display_market_context(result['market_context'], asset_type="crypto")
    
    # Main metrics
    WebAnalysisDisplayUtils.display_main_metrics(result, asset_type="crypto")
    
    # Agent results (this will now show clean, deduplicated agents)
    WebAnalysisDisplayUtils.display_agent_results(result['agent_results'])
    
    return result

if __name__ == "__main__":
    # Test the integration
    result = demonstrate_llm_integration()
    print("✅ LLM Response Parser Integration Complete")
    print(f"Parsed {len(result['agent_results'])} agents successfully")
    for agent_name in result['agent_results'].keys():
        print(f"  - {agent_name.title()}")
