"""Core configuration settings for MarketResearcher."""

import os
from typing import Dict, List, Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field
try:
    from pydantic import field_validator
except ImportError:
    from pydantic import validator as field_validator
from dotenv import load_dotenv

load_dotenv()


class MarketResearcherConfig(BaseSettings):
    """Main configuration class for MarketResearcher trading system."""
    
    # Binance API Configuration
    binance_api_key: str = ""
    binance_secret_key: str = ""
    binance_testnet: bool = Field(default=False, env="BINANCE_TESTNET")
    
    # Finnhub API Configuration
    finnhub_api_key: str = ""
    
    # Polygon.io API Configuration
    polygon_api_key: str = ""
    
    # Alpha Vantage API Configuration
    alpha_vantage_api_key: str = ""
    
    # FRED API Configuration
    fred_api_key: str = ""
    
    # Local LLM Configuration
    llm_endpoint: str = Field(default="http://127.0.0.1:1234/v1", env="LLM_ENDPOINT")
    llm_model: str = Field(default="llama3", env="LLM_MODEL")
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=32768, env="LLM_MAX_TOKENS")
    llm_timeout: int = Field(default=120, env="LLM_TIMEOUT")
    
    # Trading Configuration
    default_symbols: List[str] = Field(
        default=["BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT", "XRPUSDT"]
    )
    analysis_timeframes: List[str] = Field(default=["1h", "4h", "1d"])
    max_position_size: float = Field(default=0.1, env="MAX_POSITION_SIZE")
    risk_tolerance: float = Field(default=0.02, env="RISK_TOLERANCE")
    
    # Agent Configuration
    max_debate_rounds: int = Field(default=2, env="MAX_DEBATE_ROUNDS")
    agent_timeout: int = Field(default=120, env="AGENT_TIMEOUT")
    enable_sentiment_analysis: bool = Field(default=True, env="ENABLE_SENTIMENT")
    enable_news_analysis: bool = Field(default=True, env="ENABLE_NEWS")
    
    # Data Configuration
    data_cache_dir: str = Field(default="./data/cache", env="DATA_CACHE_DIR")
    historical_days: int = Field(default=30, env="HISTORICAL_DAYS")
    price_update_interval: int = Field(default=60, env="PRICE_UPDATE_INTERVAL")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="./logs/marketresearcher.log", env="LOG_FILE")
    
    # Portfolio Configuration
    initial_balance: float = Field(default=10000.0, env="INITIAL_BALANCE")
    base_currency: str = Field(default="USDT", env="BASE_CURRENCY")
    

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from environment


def get_config() -> MarketResearcherConfig:
    """Get the global configuration instance."""
    return MarketResearcherConfig()


# Technical Analysis Configuration
TECHNICAL_INDICATORS = {
    "rsi": {"period": 14, "overbought": 70, "oversold": 30},
    "macd": {"fast": 12, "slow": 26, "signal": 9},
    "bollinger": {"period": 20, "std": 2},
    "sma": {"periods": [20, 50, 200]},
    "ema": {"periods": [12, 26]},
    "stoch": {"k_period": 14, "d_period": 3},
    "atr": {"period": 14}
}

# Risk Management Configuration
RISK_PARAMETERS = {
    "max_drawdown": 0.15,
    "max_daily_loss": 0.05,
    "position_sizing": "kelly",
    "stop_loss_pct": 0.02,
    "take_profit_pct": 0.06,
    "correlation_threshold": 0.7
}

# News and Sentiment Sources
NEWS_SOURCES = {
    "crypto_news": [
        "https://cointelegraph.com/rss",
        "https://cryptonews.com/news/feed/",
        "https://www.coindesk.com/arc/outboundfeeds/rss/"
    ],
    "stock_news": [
        "https://feeds.finance.yahoo.com/rss/2.0/headline",
        "https://www.marketwatch.com/rss/topstories",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://feeds.bloomberg.com/markets/news.rss",
        "https://www.reuters.com/business/finance/rss",
        "https://seekingalpha.com/market_currents.xml",
        "https://www.fool.com/feeds/index.aspx"
    ],
    "financial_news": [
        "https://www.ft.com/rss/home/us",
        "https://www.wsj.com/xml/rss/3_7085.xml",
        "https://feeds.barrons.com/public/resources/documents/MarketWatch_TopStories.xml",
        "https://www.investing.com/rss/news.rss",
        "https://feeds.feedburner.com/zerohedge/feed"
    ],
    "reddit_subs": [
        "cryptocurrency", "bitcoin", "ethereum", "cryptomarkets",
        "stocks", "investing", "SecurityAnalysis", "ValueInvesting", 
        "StockMarket", "wallstreetbets", "financialindependence"
    ],
    "twitter_keywords": [
        "#bitcoin", "#ethereum", "#crypto", "#defi",
        "#stocks", "#investing", "#trading", "#finance", 
        "#earnings", "#markets", "#NYSE", "#NASDAQ"
    ]
}
