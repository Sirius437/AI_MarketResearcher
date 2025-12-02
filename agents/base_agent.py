"""Base agent class for cryptocurrency trading analysis."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime

from llm.local_client import LocalLLMClient
from llm.prompt_manager import PromptManager
from config.settings import MarketResearcherConfig

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all trading agents."""
    
    def __init__(self, llm_client: LocalLLMClient, prompt_manager: PromptManager, config: MarketResearcherConfig, agent_name: str):
        """Initialize base agent."""
        self.config = config
        self.agent_name = agent_name
        self.llm_client = llm_client
        self.prompt_manager = prompt_manager
        
        # Agent state
        self.last_analysis = {}
        self.analysis_history = []
        self.confidence_scores = []
        
        logger.info(f"Initialized {agent_name} agent")
    
    @abstractmethod
    def analyze(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform analysis for the given symbol and data."""
        pass
    
    @abstractmethod
    def get_agent_type(self) -> str:
        """Return the agent type identifier."""
        pass
    
    def _execute_llm_analysis(
        self, 
        messages: List[Dict[str, str]], 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute LLM analysis with error handling."""
        try:
            # Add conversation context if available
            messages_with_context = self.prompt_manager.add_conversation_context(
                self.get_agent_type(), 
                messages
            )
            
            # Generate response with higher token limit for detailed analysis
            response = self.llm_client.generate_response(
                messages_with_context, 
                max_tokens=8192,  # Increased from default to ensure complete responses
                temperature=0.7
            )
            
            if response["success"]:
                # Save conversation turn
                user_message = messages[-1]["content"] if messages else ""
                self.prompt_manager.save_conversation_turn(
                    self.get_agent_type(),
                    user_message,
                    response["content"]
                )
                
                # Parse and structure the response
                structured_response = self._parse_llm_response(response["content"])
                
                return {
                    "success": True,
                    "analysis": structured_response,
                    "raw_response": response["content"],
                    "timestamp": datetime.now().isoformat(),
                    "agent": self.agent_name,
                    "model_info": {
                        "model": response.get("model", "unknown"),
                        "usage": response.get("usage", {})
                    }
                }
            else:
                logger.error(f"LLM analysis failed for {self.agent_name}: {response.get('error')}")
                return {
                    "success": False,
                    "error": response.get("error", "Unknown LLM error"),
                    "agent": self.agent_name,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in LLM analysis for {self.agent_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.agent_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response into structured format."""
        try:
            # Default parsing - subclasses can override for specific formats
            lines = response_text.strip().split('\n')
            parsed = {
                "summary": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                "full_text": response_text,
                "key_points": []
            }
            
            # Extract numbered points or bullet points
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-')):
                    parsed["key_points"].append(line)
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return {
                "summary": "Response parsing failed",
                "full_text": response_text,
                "error": str(e)
            }
    
    def _extract_confidence_score(self, analysis_text: str) -> float:
        """Extract confidence score from analysis text."""
        try:
            # Look for confidence patterns in text
            import re
            
            # Pattern 1: "confidence: 8/10" or "confidence level: 8"
            confidence_patterns = [
                r'confidence[:\s]+(\d+)(?:/10)?',
                r'confidence level[:\s]+(\d+)',
                r'(\d+)/10\s*confidence',
                r'score[:\s]+(\d+)'
            ]
            
            for pattern in confidence_patterns:
                match = re.search(pattern, analysis_text.lower())
                if match:
                    score = int(match.group(1))
                    return min(10, max(1, score)) / 10.0
            
            # Default confidence based on text length and keywords
            positive_keywords = ['strong', 'confident', 'clear', 'definitive', 'certain']
            negative_keywords = ['uncertain', 'unclear', 'mixed', 'conflicting', 'weak']
            
            positive_count = sum(1 for word in positive_keywords if word in analysis_text.lower())
            negative_count = sum(1 for word in negative_keywords if word in analysis_text.lower())
            
            base_confidence = 0.6
            confidence_adjustment = (positive_count - negative_count) * 0.1
            
            return max(0.1, min(1.0, base_confidence + confidence_adjustment))
            
        except Exception as e:
            logger.error(f"Error extracting confidence score: {e}")
            return 0.5  # Default moderate confidence
    
    def _validate_analysis_data(self, data: Dict[str, Any]) -> bool:
        """Validate input data for analysis."""
        required_fields = ['symbol']
        
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field '{field}' in analysis data")
                return False
        
        return True
    
    def get_analysis_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent analysis history."""
        return self.analysis_history[-limit:] if self.analysis_history else []
    
    def get_average_confidence(self) -> float:
        """Get average confidence score from recent analyses."""
        if not self.confidence_scores:
            return 0.0
        
        recent_scores = self.confidence_scores[-10:]  # Last 10 analyses
        return sum(recent_scores) / len(recent_scores)
    
    def clear_history(self):
        """Clear analysis history and reset state."""
        self.analysis_history.clear()
        self.confidence_scores.clear()
        self.last_analysis.clear()
        self.prompt_manager.clear_conversation_history(self.get_agent_type())
        logger.info(f"Cleared history for {self.agent_name}")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics."""
        return {
            "agent_name": self.agent_name,
            "agent_type": self.get_agent_type(),
            "total_analyses": len(self.analysis_history),
            "average_confidence": self.get_average_confidence(),
            "last_analysis_time": self.last_analysis.get("timestamp"),
            "llm_endpoint": self.config.llm_endpoint,
            "llm_model": self.config.llm_model
        }
    
    def test_agent(self) -> Dict[str, Any]:
        """Test agent functionality with sample data."""
        try:
            # Test LLM connection
            llm_test = self.llm_client.test_connection()
            
            if not llm_test["success"]:
                return {
                    "success": False,
                    "error": "LLM connection failed",
                    "details": llm_test
                }
            
            # Test with minimal data
            test_data = {
                "symbol": "BTCUSDT",
                "price": 45000.0,
                "test_mode": True
            }
            
            # This will be implemented by subclasses
            result = self.analyze("BTCUSDT", test_data)
            
            return {
                "success": True,
                "message": f"{self.agent_name} test completed successfully",
                "llm_status": llm_test,
                "analysis_result": result.get("success", False)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": self.agent_name
            }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if hasattr(self, 'llm_client'):
            self.llm_client.close()
