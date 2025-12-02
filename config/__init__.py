"""Configuration module for MarketResearcher trading system."""

from .settings import MarketResearcherConfig, get_config
from .prompts import PromptTemplates

__all__ = ["MarketResearcherConfig", "get_config", "PromptTemplates"]
