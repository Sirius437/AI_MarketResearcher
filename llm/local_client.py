"""Local LLM client for cryptocurrency trading analysis."""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Union
import httpx
import requests
from datetime import datetime

from config.settings import MarketResearcherConfig

logger = logging.getLogger(__name__)


class LocalLLMClient:
    """Client for interacting with local LLM endpoints."""
    
    def __init__(self, config: MarketResearcherConfig):
        """Initialize local LLM client."""
        self.config = config
        self.endpoint = config.llm_endpoint
        self.model = config.llm_model
        self.temperature = config.llm_temperature
        self.max_tokens = config.llm_max_tokens
        self.timeout = config.llm_timeout
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    async def initialize(self):
        """Initialize and test connection to local LLM."""
        try:
            # Test connection to LLM endpoint
            test_messages = [{"role": "user", "content": "Hello"}]
            self.generate_response(test_messages)
            logger.info(f"Successfully connected to LLM at {self.endpoint}")
        except Exception as e:
            logger.warning(f"Could not connect to LLM at {self.endpoint}: {e}")
            # Don't raise - allow system to continue without LLM
    
    def _prepare_request(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare request payload for LLM API."""
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "stream": kwargs.get("stream", False)
        }
        
        # Add optional parameters if provided
        if "top_p" in kwargs:
            payload["top_p"] = kwargs["top_p"]
        if "frequency_penalty" in kwargs:
            payload["frequency_penalty"] = kwargs["frequency_penalty"]
        if "presence_penalty" in kwargs:
            payload["presence_penalty"] = kwargs["presence_penalty"]
        
        return payload
    
    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response from local LLM."""
        try:
            url = f"{self.endpoint.rstrip('/')}/chat/completions"
            payload = self._prepare_request(messages, **kwargs)
            
            logger.debug(f"Sending request to {url}")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = self.session.post(
                url, 
                json=payload, 
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract response content
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                finish_reason = result["choices"][0].get("finish_reason", "unknown")
                
                # Log if content is empty or truncated
                if not content or content.strip() == "":
                    logger.warning(f"LLM returned empty content. Finish reason: {finish_reason}")
                    logger.debug(f"Full response: {result}")
                
                return {
                    "success": True,
                    "content": content,
                    "usage": result.get("usage", {}),
                    "model": result.get("model", self.model),
                    "timestamp": datetime.now().isoformat(),
                    "finish_reason": finish_reason
                }
            else:
                logger.error(f"Unexpected response format: {result}")
                return {
                    "success": False,
                    "error": "Unexpected response format",
                    "raw_response": result
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout after {self.timeout} seconds")
            return {
                "success": False,
                "error": "Request timeout",
                "timeout": self.timeout
            }
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to LLM endpoint: {self.endpoint}")
            return {
                "success": False,
                "error": "Connection failed",
                "endpoint": self.endpoint
            }
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}",
                "response_text": e.response.text
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_response_async(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response from local LLM asynchronously."""
        try:
            url = f"{self.endpoint.rstrip('/')}/chat/completions"
            payload = self._prepare_request(messages, **kwargs)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    return {
                        "success": True,
                        "content": content,
                        "usage": result.get("usage", {}),
                        "model": result.get("model", self.model),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": "Unexpected response format",
                        "raw_response": result
                    }
                    
        except Exception as e:
            logger.error(f"Async request error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_with_context(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        context_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Analyze data with system and user prompts."""
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add context data if provided
        if context_data:
            context_str = self._format_context_data(context_data)
            messages.append({
                "role": "user", 
                "content": f"Context Data:\n{context_str}\n\n{user_prompt}"
            })
        else:
            messages.append({"role": "user", "content": user_prompt})
        
        return self.generate_response(messages, **kwargs)
    
    def _format_context_data(self, context_data: Dict[str, Any]) -> str:
        """Format context data for LLM consumption."""
        formatted_lines = []
        
        for key, value in context_data.items():
            if isinstance(value, (dict, list)):
                formatted_lines.append(f"{key}: {json.dumps(value, indent=2)}")
            else:
                formatted_lines.append(f"{key}: {value}")
        
        return "\n".join(formatted_lines)
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to local LLM endpoint."""
        try:
            test_messages = [
                {"role": "user", "content": "Hello, please respond with 'Connection successful'"}
            ]
            
            response = self.generate_response(test_messages, max_tokens=50)
            
            if response["success"]:
                return {
                    "success": True,
                    "message": "LLM connection successful",
                    "endpoint": self.endpoint,
                    "model": self.model,
                    "response_content": response["content"]
                }
            else:
                return {
                    "success": False,
                    "message": "LLM connection failed",
                    "error": response.get("error", "Unknown error")
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": "LLM connection test failed",
                "error": str(e)
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models."""
        try:
            url = f"{self.endpoint.rstrip('/')}/models"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return {
                "success": True,
                "models": result.get("data", []),
                "endpoint": self.endpoint
            }
            
        except Exception as e:
            logger.error(f"Error fetching model info: {e}")
            return {
                "success": False,
                "error": str(e),
                "endpoint": self.endpoint
            }
    
    def batch_analyze(
        self, 
        requests: List[Dict[str, Any]], 
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """Process multiple analysis requests concurrently."""
        async def process_batch():
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def process_single_request(request_data):
                async with semaphore:
                    messages = request_data.get("messages", [])
                    kwargs = request_data.get("kwargs", {})
                    return await self.generate_response_async(messages, **kwargs)
            
            tasks = [process_single_request(req) for req in requests]
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(process_batch())
        except RuntimeError:
            # Create new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(process_batch())
            finally:
                loop.close()
    
    def close(self):
        """Close the session and clean up resources."""
        if self.session:
            self.session.close()
            logger.info("LLM client session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
