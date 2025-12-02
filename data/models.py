"""
Data models for the MarketResearcher application.
Contains the Stock dataclass and other shared models.
"""

from dataclasses import dataclass


@dataclass
class Stock:
    """Stock information."""
    symbol: str
    name: str
    exchange: str
    jurisdiction: str
    sector: str
    industry: str
    market_cap_category: str  # large, mid, small
    currency: str
    description: str
