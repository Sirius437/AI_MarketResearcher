"""Local LLM interface module for CryptoBot trading system."""

from .local_client import LocalLLMClient
from .prompt_manager import PromptManager

__all__ = ["LocalLLMClient", "PromptManager"]
