"""
Token usage tracking system for MarketResearcher web interface.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import threading
from contextlib import contextmanager

class TokenUsageTracker:
    """Track and manage token usage for users."""
    
    def __init__(self, db_path: str = "web/token_usage.db"):
        """Initialize token usage tracker."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS token_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    session_id TEXT,
                    analysis_type TEXT NOT NULL,
                    symbol TEXT,
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    cost_estimate REAL DEFAULT 0.0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    model_name TEXT,
                    request_id TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_token_limits (
                    username TEXT PRIMARY KEY,
                    daily_limit INTEGER DEFAULT 10000,
                    monthly_limit INTEGER DEFAULT 100000,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_username_timestamp 
                ON token_usage(username, timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_analysis_type 
                ON token_usage(analysis_type)
            """)
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper locking."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
    
    def track_usage(self, 
                   username: str,
                   analysis_type: str,
                   prompt_tokens: int = 0,
                   completion_tokens: int = 0,
                   model_name: str = "gpt-3.5-turbo",
                   symbol: str = None,
                   session_id: str = None,
                   request_id: str = None) -> Dict[str, Any]:
        """Track token usage for a user."""
        total_tokens = prompt_tokens + completion_tokens
        cost_estimate = self._calculate_cost(model_name, prompt_tokens, completion_tokens)
        
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO token_usage 
                (username, session_id, analysis_type, symbol, prompt_tokens, 
                 completion_tokens, total_tokens, cost_estimate, model_name, request_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (username, session_id, analysis_type, symbol, prompt_tokens,
                  completion_tokens, total_tokens, cost_estimate, model_name, request_id))
            
            usage_id = cursor.lastrowid
        
        return {
            "usage_id": usage_id,
            "total_tokens": total_tokens,
            "cost_estimate": cost_estimate,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_user_usage(self, username: str, days: int = 30) -> Dict[str, Any]:
        """Get token usage statistics for a user."""
        start_date = datetime.now() - timedelta(days=days)
        
        with self._get_connection() as conn:
            # Get total usage
            total_stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(prompt_tokens) as total_prompt_tokens,
                    SUM(completion_tokens) as total_completion_tokens,
                    SUM(total_tokens) as total_tokens,
                    SUM(cost_estimate) as total_cost
                FROM token_usage 
                WHERE username = ? AND timestamp >= ?
            """, (username, start_date)).fetchone()
            
            # Get usage by analysis type
            by_analysis = conn.execute("""
                SELECT 
                    analysis_type,
                    COUNT(*) as requests,
                    SUM(total_tokens) as tokens,
                    SUM(cost_estimate) as cost
                FROM token_usage 
                WHERE username = ? AND timestamp >= ?
                GROUP BY analysis_type
                ORDER BY tokens DESC
            """, (username, start_date)).fetchall()
            
            # Get daily usage for the last 7 days
            daily_usage = conn.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as requests,
                    SUM(total_tokens) as tokens,
                    SUM(cost_estimate) as cost
                FROM token_usage 
                WHERE username = ? AND timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
                LIMIT 7
            """, (username, datetime.now() - timedelta(days=7))).fetchall()
            
            # Get recent requests
            recent_requests = conn.execute("""
                SELECT 
                    analysis_type, symbol, total_tokens, cost_estimate, 
                    timestamp, model_name
                FROM token_usage 
                WHERE username = ? 
                ORDER BY timestamp DESC 
                LIMIT 10
            """, (username,)).fetchall()
        
        return {
            "username": username,
            "period_days": days,
            "total_stats": dict(total_stats) if total_stats else {},
            "by_analysis_type": [dict(row) for row in by_analysis],
            "daily_usage": [dict(row) for row in daily_usage],
            "recent_requests": [dict(row) for row in recent_requests]
        }
    
    def get_daily_usage(self, username: str, date: datetime = None) -> Dict[str, Any]:
        """Get token usage for a specific day."""
        if date is None:
            date = datetime.now()
        
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        with self._get_connection() as conn:
            daily_stats = conn.execute("""
                SELECT 
                    COUNT(*) as requests,
                    SUM(prompt_tokens) as prompt_tokens,
                    SUM(completion_tokens) as completion_tokens,
                    SUM(total_tokens) as total_tokens,
                    SUM(cost_estimate) as cost
                FROM token_usage 
                WHERE username = ? AND timestamp >= ? AND timestamp < ?
            """, (username, start_of_day, end_of_day)).fetchone()
        
        return dict(daily_stats) if daily_stats else {}
    
    def get_monthly_usage(self, username: str, year: int = None, month: int = None) -> Dict[str, Any]:
        """Get token usage for a specific month."""
        if year is None or month is None:
            now = datetime.now()
            year = now.year
            month = now.month
        
        start_of_month = datetime(year, month, 1)
        if month == 12:
            end_of_month = datetime(year + 1, 1, 1)
        else:
            end_of_month = datetime(year, month + 1, 1)
        
        with self._get_connection() as conn:
            monthly_stats = conn.execute("""
                SELECT 
                    COUNT(*) as requests,
                    SUM(prompt_tokens) as prompt_tokens,
                    SUM(completion_tokens) as completion_tokens,
                    SUM(total_tokens) as total_tokens,
                    SUM(cost_estimate) as cost
                FROM token_usage 
                WHERE username = ? AND timestamp >= ? AND timestamp < ?
            """, (username, start_of_month, end_of_month)).fetchone()
        
        return dict(monthly_stats) if monthly_stats else {}
    
    def check_limits(self, username: str) -> Dict[str, Any]:
        """Check if user is within their token limits."""
        # Get user limits
        with self._get_connection() as conn:
            limits = conn.execute("""
                SELECT daily_limit, monthly_limit 
                FROM user_token_limits 
                WHERE username = ?
            """, (username,)).fetchone()
        
        if not limits:
            # Set default limits
            self.set_user_limits(username)
            limits = {"daily_limit": 10000, "monthly_limit": 100000}
        else:
            limits = dict(limits)
        
        # Get current usage
        daily_usage = self.get_daily_usage(username)
        monthly_usage = self.get_monthly_usage(username)
        
        daily_tokens = daily_usage.get("total_tokens", 0) or 0
        monthly_tokens = monthly_usage.get("total_tokens", 0) or 0
        
        return {
            "daily_limit": limits["daily_limit"],
            "monthly_limit": limits["monthly_limit"],
            "daily_used": daily_tokens,
            "monthly_used": monthly_tokens,
            "daily_remaining": max(0, limits["daily_limit"] - daily_tokens),
            "monthly_remaining": max(0, limits["monthly_limit"] - monthly_tokens),
            "daily_exceeded": daily_tokens > limits["daily_limit"],
            "monthly_exceeded": monthly_tokens > limits["monthly_limit"]
        }
    
    def set_user_limits(self, username: str, daily_limit: int = 10000, monthly_limit: int = 100000):
        """Set token limits for a user."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO user_token_limits 
                (username, daily_limit, monthly_limit, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (username, daily_limit, monthly_limit))
    
    def _calculate_cost(self, model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost based on model and token usage."""
        # Pricing per 1K tokens (as of 2024)
        pricing = {
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "gpt-3.5-turbo": {"prompt": 0.001, "completion": 0.002},
            "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
            "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
            "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125}
        }
        
        model_pricing = pricing.get(model_name, pricing["gpt-3.5-turbo"])
        
        prompt_cost = (prompt_tokens / 1000) * model_pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * model_pricing["completion"]
        
        return round(prompt_cost + completion_cost, 6)
    
    def get_all_users_usage(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get usage statistics for all users."""
        start_date = datetime.now() - timedelta(days=days)
        
        with self._get_connection() as conn:
            users_stats = conn.execute("""
                SELECT 
                    username,
                    COUNT(*) as total_requests,
                    SUM(total_tokens) as total_tokens,
                    SUM(cost_estimate) as total_cost,
                    MAX(timestamp) as last_activity
                FROM token_usage 
                WHERE timestamp >= ?
                GROUP BY username
                ORDER BY total_tokens DESC
            """, (start_date,)).fetchall()
        
        return [dict(row) for row in users_stats]
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old token usage data."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with self._get_connection() as conn:
            result = conn.execute("""
                DELETE FROM token_usage 
                WHERE timestamp < ?
            """, (cutoff_date,))
            
            deleted_count = result.rowcount
        
        return {"deleted_records": deleted_count, "cutoff_date": cutoff_date.isoformat()}

# Global instance
token_tracker = TokenUsageTracker()
