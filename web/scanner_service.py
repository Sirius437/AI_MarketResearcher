#!/usr/bin/env python3
"""
Standalone Scanner Service - Runs IB scanners in isolated process.
This service runs independently of Streamlit to avoid threading conflicts.
"""

import asyncio
import json
import sys
import os
from flask import Flask, request, jsonify

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.scanner_agent import ScannerAgent
from llm.local_client import LocalLLMClient
from llm.prompt_manager import PromptManager
from config.settings import MarketResearcherConfig

app = Flask(__name__)

# Global scanner agent instance
scanner_agent = None

def initialize_scanner():
    """Initialize scanner agent with unique client ID."""
    global scanner_agent
    try:
        config = MarketResearcherConfig()
        llm_client = LocalLLMClient(config)
        prompt_manager = PromptManager(config)
        
        # Create scanner agent with service-specific client ID to avoid collisions
        scanner_agent = ScannerAgent(
            llm_client=llm_client,
            prompt_manager=prompt_manager,
            config=config
        )
        
        # Initialize IB connection for scanner service
        if hasattr(scanner_agent, '_ensure_ib_connection'):
            connection_success = scanner_agent._ensure_ib_connection()
            if connection_success and hasattr(scanner_agent, 'ib_client') and scanner_agent.ib_client:
                scanner_agent.ib_client.client_id = 9001
                print(f"Scanner service connected with client ID: 9001")
            else:
                print("Warning: Could not establish IB connection for scanner service")
        
        print("Scanner service initialized successfully")
        return True
    except Exception as e:
        print(f"Failed to initialize scanner: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with IB connection status."""
    try:
        if scanner_agent and hasattr(scanner_agent, 'ib_client') and scanner_agent.ib_client:
            ib_connected = scanner_agent.ib_client.is_connected()
            return jsonify({
                "status": "healthy", 
                "service": "scanner",
                "ib_connected": ib_connected,
                "client_id": getattr(scanner_agent.ib_client, 'client_id', None)
            })
        else:
            return jsonify({
                "status": "healthy", 
                "service": "scanner",
                "ib_connected": False,
                "client_id": None
            })
    except Exception as e:
        return jsonify({
            "status": "error", 
            "service": "scanner",
            "error": str(e),
            "ib_connected": False
        })

@app.route('/scanner/execute', methods=['POST'])
def execute_scanner():
    """Execute market scanners."""
    try:
        data = request.get_json()
        
        if not scanner_agent:
            return jsonify({"success": False, "error": "Scanner not initialized"})
        
        # Prepare analysis data
        analysis_data = {
            'scanner_types': data.get('scanner_types', ['hot_us_volume']),
            'max_results': data.get('max_results', 20),
            'use_cache': data.get('use_cache', True)
        }
        
        # Execute scanner
        result = scanner_agent.analyze(None, analysis_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/scanner/available', methods=['GET'])
def get_available_scanners():
    """Get list of available scanners."""
    try:
        if not scanner_agent:
            return jsonify({"success": False, "error": "Scanner not initialized"})
        
        return jsonify({
            "success": True,
            "scanners": scanner_agent.available_scanners
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    print("Starting Scanner Service...")
    
    if initialize_scanner():
        print("Scanner service running on #http://your-server-ip:5000")  # Update with your server IP
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=False)
    else:
        print("Failed to start scanner service")
        sys.exit(1)
