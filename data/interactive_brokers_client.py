"""
Interactive Brokers API client for comprehensive market data and trading.
Uses the IB Python API (ibapi) for real-time and historical data.
"""

import asyncio
import logging
import threading
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from queue import Queue, Empty
import json
from collections import deque, defaultdict
import hashlib
import pandas as pd

# Import symbol mappers
from .exchanges.klse_ib_mapper import get_ib_symbol_for_data as get_klse_ib_symbol
from .exchanges.asx_ib_mapper import get_ib_symbol_for_data as get_asx_ib_symbol
from .exchanges.sgx_ib_mapper import get_ib_symbol_for_data as get_sgx_ib_symbol

try:
    from ibapi.client import EClient
    from ibapi.wrapper import EWrapper
    from ibapi.contract import Contract
    from ibapi.order import Order
    from ibapi.ticktype import TickTypeEnum
    from ibapi.common import BarData, TickerId
    from ibapi.scanner import ScannerSubscription
    from ibapi.tag_value import TagValue
    IB_AVAILABLE = True
except ImportError:
    IB_AVAILABLE = False
    print("Warning: ibapi not installed. Run: pip install ibapi")

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for IB API requests with multiple constraints."""
    
    def __init__(self):
        # 50 messages per second limit
        self.message_timestamps = deque()
        
        # Historical data: max 5 requests within 2 seconds
        self.historical_timestamps = deque()
        
        # 59 requests in any 10 minute period
        self.ten_minute_timestamps = deque()
        
        # Duplicate request prevention: same request within 15 seconds
        self.request_cache = {}
        
        self.lock = threading.Lock()
    
    def _clean_old_timestamps(self, timestamps: deque, max_age: float):
        """Remove timestamps older than max_age seconds."""
        current_time = time.time()
        while timestamps and current_time - timestamps[0] > max_age:
            timestamps.popleft()
    
    def _generate_request_hash(self, request_type: str, **kwargs) -> str:
        """Generate hash for request deduplication."""
        request_str = f"{request_type}:{sorted(kwargs.items())}"
        return hashlib.md5(request_str.encode()).hexdigest()
    
    async def wait_for_rate_limit(self, request_type: str = "general", **request_params):
        """Wait if necessary to comply with rate limits."""
        with self.lock:
            current_time = time.time()
            
            # Check for duplicate request within 15 seconds
            request_hash = self._generate_request_hash(request_type, **request_params)
            if request_hash in self.request_cache:
                last_request_time = self.request_cache[request_hash]
                if current_time - last_request_time < 15:
                    wait_time = 15 - (current_time - last_request_time)
                    logger.info(f"Duplicate request detected, waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    current_time = time.time()
            
            # Clean old timestamps
            self._clean_old_timestamps(self.message_timestamps, 1.0)  # 1 second
            self._clean_old_timestamps(self.historical_timestamps, 2.0)  # 2 seconds
            self._clean_old_timestamps(self.ten_minute_timestamps, 600.0)  # 10 minutes
            
            # Check 50 messages per second limit
            if len(self.message_timestamps) >= 50:
                wait_time = 1.0 - (current_time - self.message_timestamps[0])
                if wait_time > 0:
                    logger.info(f"Message rate limit reached, waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    current_time = time.time()
                    self._clean_old_timestamps(self.message_timestamps, 1.0)
            
            # Check historical data limit (5 requests within 2 seconds)
            if request_type == "historical":
                if len(self.historical_timestamps) >= 5:
                    wait_time = 2.0 - (current_time - self.historical_timestamps[0])
                    if wait_time > 0:
                        logger.info(f"Historical data rate limit reached, waiting {wait_time:.1f}s")
                        await asyncio.sleep(wait_time)
                        current_time = time.time()
                        self._clean_old_timestamps(self.historical_timestamps, 2.0)
                self.historical_timestamps.append(current_time)
            
            # Check 10-minute limit (59 requests)
            if len(self.ten_minute_timestamps) >= 59:
                wait_time = 600.0 - (current_time - self.ten_minute_timestamps[0])
                if wait_time > 0:
                    logger.info(f"10-minute rate limit reached, waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    current_time = time.time()
                    self._clean_old_timestamps(self.ten_minute_timestamps, 600.0)
            
            # Record this request
            self.message_timestamps.append(current_time)
            self.ten_minute_timestamps.append(current_time)
            
            # Cache this request
            self.request_cache[request_hash] = current_time
            
            # Clean old cache entries
            keys_to_remove = []
            for h, t in self.request_cache.items():
                if current_time - t > 15:
                    keys_to_remove.append(h)
            for h in keys_to_remove:
                del self.request_cache[h]
    
    async def wait_if_needed(self):
        """Simple wait method for general rate limiting."""
        await self.wait_for_rate_limit("general")


class IBWrapper(EWrapper):
    """Wrapper class to handle IB API callbacks."""
    
    def __init__(self, client):
        EWrapper.__init__(self)
        self.client = client
        
    def nextValidId(self, orderId: int):
        """Callback for next valid order ID."""
        super().nextValidId(orderId)
        self.client.next_order_id = orderId
        self.client.connected_event.set()
        logger.info(f"Connected to IB. Next order ID: {orderId}")
        
    def connectAck(self):
        """Connection acknowledgment callback."""
        super().connectAck()
        logger.info("Connection acknowledged by IB")
        
    def connectionClosed(self):
        """Connection closed callback."""
        super().connectionClosed()
        logger.info("Connection closed by IB")
        self.client.connected_event.clear()
        
    def error(self, *args, **kwargs):
        """Handle API errors with flexible signature for version compatibility."""
        # Handle different ibapi versions with varying error signatures
        reqId = None
        errorTime = None
        errorCode = None
        errorString = ""
        advancedOrderRejectJson = ""
        
        # Parse arguments based on length
        if len(args) >= 3:
            reqId = args[0]
            if len(args) == 3:
                # Old signature: error(reqId, errorCode, errorString)
                errorCode = args[1]
                errorString = args[2]
            elif len(args) >= 4:
                # New signature: error(reqId, errorTime, errorCode, errorString, ...)
                errorTime = args[1]
                errorCode = args[2]
                errorString = args[3]
                if len(args) >= 5:
                    advancedOrderRejectJson = args[4]
        
        # Filter out informational messages
        if errorCode in [2104, 2107, 2158]:  # Market data farm status messages
            logger.info(f"IB Info - Code: {errorCode}, Message: {errorString}")
        elif errorCode in [502, 504, 1100, 1101, 1102]:  # Connection errors
            logger.error(f"IB Connection Error - Code: {errorCode}, Message: {errorString}")
            self.client.connected_event.clear()
        elif errorCode == 10089:  # Market data subscription required
            logger.warning(f"IB Market Data Subscription Required - Code: {errorCode}, Message: {errorString}")
            # Mark request as failed for market data subscription issues
            if reqId > 0 and reqId in self.client.data_ready_events:
                self.client.data_ready_events[reqId].set()
        elif errorCode == 326:  # Client ID already in use
            logger.error(f"IB Client ID Collision - Code: {errorCode}, Message: {errorString}")
            self.client.connected_event.clear()
        elif errorCode in [2119, 300]:  # Market data farm connecting, EId not found
            logger.debug(f"IB Debug - Code: {errorCode}, Message: {errorString}")
        else:
            logger.error(f"IB Error - ReqId: {reqId}, Code: {errorCode}, Message: {errorString}")
            
    def tickPrice(self, reqId: TickerId, tickType: int, price: float, attrib):
        """Handle real-time price ticks."""
        tick_name = TickTypeEnum.toStr(tickType)
        if reqId not in self.client.tick_data:
            self.client.tick_data[reqId] = {}
        self.client.tick_data[reqId][tick_name] = price
        logger.debug(f"Price tick - ReqId: {reqId}, Type: {tick_name}, Price: {price}")
        
    def tickSize(self, reqId: TickerId, tickType: int, size: int):
        """Handle real-time size ticks."""
        tick_name = TickTypeEnum.toStr(tickType)
        if reqId not in self.client.tick_data:
            self.client.tick_data[reqId] = {}
        self.client.tick_data[reqId][f"{tick_name}_size"] = size
        logger.debug(f"Size tick - ReqId: {reqId}, Type: {tick_name}, Size: {size}")
        
    def historicalData(self, reqId: int, bar: BarData):
        """Handle historical data bars."""
        if reqId not in self.client.historical_data:
            self.client.historical_data[reqId] = []
        bar_dict = {
            'date': bar.date,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume,
            'wap': bar.wap,
            'count': getattr(bar, 'count', 0)  # Handle missing count attribute
        }
        self.client.historical_data[reqId].append(bar_dict)
        
    def historicalDataEnd(self, reqId: int, start: str, end: str):
        """Signal end of historical data."""
        logger.info(f"Historical data complete for reqId {reqId}: {start} to {end}")
        if reqId in self.client.data_ready_events:
            self.client.data_ready_events[reqId].set()
            
    def scannerData(self, reqId: int, rank: int, contractDetails, distance: str, benchmark: str, projection: str, legsStr: str):
        """Handle scanner results."""
        if reqId not in self.client.scanner_results:
            self.client.scanner_results[reqId] = []
        
        scanner_item = {
            'rank': rank,
            'symbol': contractDetails.contract.symbol,
            'secType': contractDetails.contract.secType,
            'exchange': contractDetails.contract.exchange,
            'currency': contractDetails.contract.currency,
            'distance': distance,
            'benchmark': benchmark,
            'projection': projection,
            'longName': getattr(contractDetails, 'longName', ''),
            'industry': getattr(contractDetails, 'industry', ''),
            'category': getattr(contractDetails, 'category', '')
        }
        self.client.scanner_results[reqId].append(scanner_item)
        
    def scannerDataEnd(self, reqId: int):
        """Signal end of scanner data."""
        logger.info(f"Scanner data complete for reqId {reqId}")
        if reqId in self.client.data_ready_events:
            self.client.data_ready_events[reqId].set()
    
    def fundamentalData(self, reqId: TickerId, data: str):
        """Handle fundamental data response."""
        try:
            logger.info(f"Received fundamental data for reqId {reqId}, data length: {len(data)}")
            self.client.fundamental_data[reqId] = data
            if reqId in self.client.data_ready_events:
                self.client.data_ready_events[reqId].set()
        except Exception as e:
            logger.error(f"Error processing fundamental data for reqId {reqId}: {e}")
            self.client.fundamental_data[reqId] = {"error": str(e)}


class InteractiveBrokersClient:
    """Interactive Brokers API client with async support."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 4002, client_id: Optional[int] = None):
        """Initialize IB client."""
        if not IB_AVAILABLE:
            raise ImportError("ibapi package not installed. Run: pip install ibapi")
            
        self.host = host
        self.port = port
        # Generate unique client ID if not provided to avoid collisions
        self.client_id = client_id if client_id is not None else self._generate_unique_client_id()
        
        # IB API components
        self.wrapper = IBWrapper(self)
        self.client = EClient(self.wrapper)
        
        # Connection management
        self.connected_event = threading.Event()
        self.api_thread = None
        self.next_order_id = None
        
        # Data storage
        self.tick_data = {}
        self.historical_data = {}
        self.contract_details = {}
        self.scanner_results = {}
        self.news_headlines = {}
        self.news_articles = {}
        self.fundamental_data = {}
        self.data_ready_events = {}
        
        # Request ID management
        self.request_id = 1000
        
        # Rate limiting
        self.rate_limiter = RateLimiter()
        
    def _generate_unique_client_id(self) -> int:
        """Generate a unique client ID based on timestamp and random number."""
        import time
        # Use current timestamp (last 4 digits) + random number for uniqueness
        timestamp_part = int(str(int(time.time()))[-4:])
        random_part = random.randint(100, 999)
        return int(f"{timestamp_part}{random_part}")
        
    def get_next_request_id(self) -> int:
        """Get next available request ID."""
        self.request_id += 1
        return self.request_id
        
    async def connect(self, timeout: int = 10) -> bool:
        """Connect to IB Gateway/TWS."""
        try:
            # Generate new client ID for each connection to avoid collisions
            self.client_id = self._generate_unique_client_id()
            logger.info(f"Connecting to IB at {self.host}:{self.port} with client ID {self.client_id}")
            
            # Connect to IB first
            self.client.connect(self.host, self.port, self.client_id)
            
            # Start API thread after connection
            self.api_thread = threading.Thread(target=self._run_api, daemon=True)
            self.api_thread.start()
            
            # Give a moment for the thread to start
            await asyncio.sleep(0.5)
            
            # Wait for connection - check multiple conditions
            start_time = time.time()
            connection_confirmed = False
            
            while time.time() - start_time < timeout and not connection_confirmed:
                if self.client.isConnected():
                    logger.info("Socket connection established")
                    
                    # Wait for nextValidId callback (indicates full API readiness)
                    for _ in range(50):  # 5 second wait in 0.1s increments
                        if self.connected_event.is_set():
                            logger.info("Successfully connected to Interactive Brokers")
                            return True
                        elif self.next_order_id is not None:
                            logger.info("Connected to Interactive Brokers (via order ID)")
                            self.connected_event.set()
                            return True
                        await asyncio.sleep(0.1)
                    
                    # If we have a stable connection but no nextValidId, proceed anyway
                    logger.warning("Connected but no nextValidId received - proceeding anyway")
                    logger.info("This is normal for read-only market data access")
                    self.connected_event.set()
                    return True
                    
                await asyncio.sleep(0.1)
            
            logger.error("Connection timeout - IB Gateway/TWS may not be running")
            return False
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
            
    def _run_api(self):
        """Run the IB API message loop."""
        self.client.run()
        
    async def disconnect(self):
        """Disconnect from Interactive Brokers."""
        try:
            if self.client and self.is_connected():
                self.client.disconnect()
                # Wait a bit for clean disconnection
                await asyncio.sleep(0.5)
            self.connected_event.clear()
            if self.api_thread and self.api_thread.is_alive():
                self.api_thread.join(timeout=2)
            # Clear data storage
            self.tick_data.clear()
            self.historical_data.clear()
            self.contract_details.clear()
            self.scanner_results.clear()
            self.news_headlines.clear()
            self.news_articles.clear()
            self.fundamental_data.clear()
            self.data_ready_events.clear()
            logger.info("Disconnected from Interactive Brokers")
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
        finally:
            # Reset connection state
            self.connected = False
            self.next_order_id = None
            
    async def close(self):
        """Alias for disconnect() to maintain compatibility."""
        await self.disconnect()
            
    def create_stock_contract(self, symbol: str, exchange: str = "SMART", currency: str = "USD") -> Contract:
        """Create a stock contract."""
        # Check if this is a numeric KLSE code and apply mapping
        from .exchanges.klse_numeric_to_symbol_map import is_numeric_klse_code
        
        # Handle KLSE stocks
        if is_numeric_klse_code(symbol) or currency == "MYR" or exchange == "BURSAMY":
            ib_symbol = get_klse_ib_symbol(symbol)
            # For KLSE stocks, use correct exchange and currency
            if is_numeric_klse_code(symbol):
                exchange = "BURSAMY"
                currency = "MYR"
        # Handle ASX stocks
        elif currency == "AUD" or exchange == "ASX":
            ib_symbol = get_asx_ib_symbol(symbol)
            exchange = "ASX"
            currency = "AUD"
        else:
            ib_symbol = symbol
        
        contract = Contract()
        contract.symbol = ib_symbol
        contract.secType = "STK"
        contract.exchange = exchange
        contract.currency = currency
        return contract
        
    def create_forex_contract(self, base_currency: str, quote_currency: str = "USD") -> Contract:
        """Create a forex contract."""
        contract = Contract()
        contract.symbol = base_currency
        contract.secType = "CASH"
        contract.currency = quote_currency
        # Use MIDPOINT data for forex instead of TRADES
        contract.exchange = "IDEALPRO"
        return contract
        
    def create_crypto_contract(self, symbol: str, exchange: str = "PAXOS") -> Contract:
        """Create a crypto contract."""
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "CRYPTO"
        contract.exchange = exchange
        contract.currency = "USD"
        return contract
        
        working_contracts = {
            # Spot commodities (CMDTY on SMART)
            'XAUUSD': {'symbol': 'XAUUSD', 'exchange': 'SMART', 'secType': 'CMDTY'},  # Gold spot - WORKING
            'XAGUSD': {'symbol': 'XAGUSD', 'exchange': 'SMART', 'secType': 'CMDTY'},  # Silver spot
            'XPTUSD': {'symbol': 'XPTUSD', 'exchange': 'SMART', 'secType': 'CMDTY'},  # Platinum spot
            
            # Continuous futures (CONTFUT on proper exchanges)
            'GC': {'symbol': 'GC', 'exchange': 'COMEX', 'secType': 'CONTFUT'},       # Gold continuous - WORKING
            'CL': {'symbol': 'CL', 'exchange': 'NYMEX', 'secType': 'CONTFUT', 'multiplier': '1000'},  # Oil continuous - WORKING
            'NG': {'symbol': 'NG', 'exchange': 'NYMEX', 'secType': 'CONTFUT'},       # Natural Gas continuous
            'HG': {'symbol': 'HG', 'exchange': 'COMEX', 'secType': 'CONTFUT'},       # Copper continuous
            'SI': {'symbol': 'SI', 'exchange': 'COMEX', 'secType': 'CONTFUT'},       # Silver continuous
            'PL': {'symbol': 'PL', 'exchange': 'NYMEX', 'secType': 'CONTFUT'},       # Platinum continuous
        }
        
        contract = Contract()
        
        # Check if we have a working mapping for this symbol
        if symbol in working_contracts:
            mapping = working_contracts[symbol]
            contract.symbol = mapping['symbol']
            contract.secType = mapping['secType']
            contract.exchange = mapping['exchange']
            contract.currency = currency
            if 'multiplier' in mapping:
                contract.multiplier = mapping['multiplier']
        else:
            # Fallback to spot commodity for unknown symbols
            contract.symbol = symbol
            contract.secType = "CMDTY"
            contract.exchange = exchange
            contract.currency = currency
            
        return contract
        
    async def get_quote(self, symbol: str, asset_type: str = "stock", exchange: str = None) -> Dict[str, Any]:
        """Get quote using historical data (avoids expensive live data subscriptions)."""
        try:
            if not self.is_connected():
                logger.error("Not connected to IB")
                return {}
            
            # Use historical data to get latest price - no subscription required
            df = await self.get_historical_data(
                symbol=symbol,
                duration="1 D",  # Get last day of data
                bar_size="1 min",  # 1-minute bars for recent price
                asset_type=asset_type,
                exchange=exchange
            )
            
            if df.empty:
                return {"error": "No historical data available"}
            
            # Get the most recent bar
            latest_bar = df.iloc[-1]
            
            # Calculate change from previous close
            if len(df) > 1:
                prev_close = df.iloc[-2]['close']
                change_pct = ((latest_bar['close'] - prev_close) / prev_close * 100) if prev_close > 0 else 0
            else:
                change_pct = 0
            
            return {
                "symbol": symbol,
                "price": float(latest_bar['close']),
                "open": float(latest_bar['open']),
                "high": float(latest_bar['high']),
                "low": float(latest_bar['low']),
                "close": float(latest_bar['close']),
                "volume": int(latest_bar['volume']) if latest_bar['volume'] else 0,
                "change_percent": round(change_pct, 2),
                "source": "Interactive Brokers (Historical)",
                "asset_type": asset_type,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Quote request failed for {symbol}: {e}")
            return {"error": str(e)}
            
    async def get_historical_data(self, symbol: str, duration: str = "1 Y", bar_size: str = "1 day", 
                                 asset_type: str = "stock", exchange: str = None, currency: str = None) -> pd.DataFrame:
        """Get historical data for a symbol."""
        try:
            # Apply rate limiting for historical data
            await self.rate_limiter.wait_for_rate_limit("historical", symbol=symbol, duration=duration, bar_size=bar_size, asset_type=asset_type)
            
            # Handle exchange-specific settings
            exchange_settings = self._get_exchange_settings(symbol, exchange, asset_type)
            
            # Use provided currency if specified, otherwise use exchange default
            if currency:
                exchange_settings['currency'] = currency
            
            # Check if we have alternative symbols for fallback
            alternatives = exchange_settings.get('alternatives', [])
            
            # Create appropriate contract
            if asset_type.lower() == "stock":
                # Try primary symbol first
                contract = self.create_stock_contract(
                    symbol=exchange_settings['symbol'],
                    exchange=exchange_settings['exchange'],
                    currency=exchange_settings['currency']
                )
                
                # If we have alternatives, try them if primary fails
                if alternatives:
                    df = await self._request_historical_data(contract, symbol, duration, bar_size)
                    if not df.empty:
                        return df
                    
                    # Primary symbol failed, try alternatives
                    logger.info(f"Primary symbol {exchange_settings['symbol']} failed, trying {len(alternatives)} alternatives")
                    for alt_symbol in alternatives:
                        if alt_symbol == exchange_settings['symbol']:
                            continue  # Skip primary symbol
                        
                        try:
                            logger.info(f"Trying alternative symbol: {alt_symbol}")
                            alt_contract = self.create_stock_contract(
                                symbol=alt_symbol,
                                exchange=exchange_settings['exchange'],
                                currency=exchange_settings['currency']
                            )
                            df = await self._request_historical_data(alt_contract, symbol, duration, bar_size)
                            if not df.empty:
                                logger.info(f"Successfully retrieved data using alternative symbol: {alt_symbol}")
                                return df
                        except Exception as e:
                            logger.warning(f"Failed with alternative symbol {alt_symbol}: {e}")
                    
                    # All alternatives failed
                    logger.warning(f"All symbol alternatives failed for {symbol}")
                    return pd.DataFrame()
            elif asset_type.lower() == "forex":
                if "/" in symbol:
                    base, quote = symbol.split("/")
                    contract = self.create_forex_contract(base, quote)
                else:
                    contract = self.create_forex_contract(symbol[:3], symbol[3:])
            elif asset_type.lower() == "crypto":
                contract = self.create_crypto_contract(symbol, exchange or "PAXOS")
            elif asset_type.lower() == "index":
                contract = self.create_index_contract(symbol, exchange or "CBOE")
            elif asset_type.lower() == "commodity":
                contract = self.create_commodity_contract(symbol, exchange or "SMART")
            else:
                return pd.DataFrame()
                
            return await self._request_historical_data(contract, symbol, duration, bar_size)
                
        except Exception as e:
            logger.error(f"Historical data request failed for {symbol}: {e}")
            return pd.DataFrame()
    
    async def _get_asx_historical_data(self, symbol: str, duration: str, bar_size: str, exchange: str) -> pd.DataFrame:
        """Get historical data for ASX stocks with fallback mechanism."""
        from .exchanges.asx_ib_mapper import get_asx_ib_mapper
        
        # Get all possible symbol alternatives
        mapper = get_asx_ib_mapper()
        
        # Strip .AX suffix if present
        if symbol.endswith(".AX"):
            symbol = symbol[:-3]
        
        # Get all alternative symbols
        alternatives = mapper.get_all_symbol_alternatives(symbol)
        
        # If no alternatives found, try with default mapping
        if not alternatives:
            ib_symbol = mapper.get_ib_symbol_for_data(symbol)
            alternatives = [ib_symbol]
        
        # Try each alternative until one works
        for i, alt_symbol in enumerate(alternatives):
            try:
                if i > 0:
                    logger.info(f"Trying alternative symbol for {symbol}: {alt_symbol}")
                
                contract = Contract()
                contract.symbol = alt_symbol
                contract.secType = "STK"
                contract.exchange = "ASX"
                contract.currency = "AUD"
                
                df = await self._request_historical_data(contract, symbol, duration, bar_size)
                
                if not df.empty:
                    logger.info(f"Successfully retrieved data using alternative symbol: {alt_symbol}")
                    return df
            except Exception as e:
                logger.warning(f"Failed with alternative symbol {alt_symbol}: {e}")
        
        logger.error(f"All symbol alternatives failed for {symbol}")
        return pd.DataFrame()
        
    def _get_exchange_settings(self, symbol: str, exchange: str = None, asset_type: str = "stock") -> dict:
        """Get exchange-specific settings for a symbol."""
        # Default settings
        settings = {
            'symbol': symbol,
            'exchange': exchange or "SMART",
            'currency': "USD"
        }
        
        # Handle ASX (Australian) stocks
        if exchange == "ASX" or (not exchange and symbol.endswith(".AX")):
            # Clean symbol by removing .AX suffix if present
            clean_symbol = symbol[:-3] if symbol.endswith(".AX") else symbol
            settings.update({
                'symbol': clean_symbol,
                'exchange': "ASX",
                'currency': "AUD"
            })
            
            # Try to use ASX mapper if available
            try:
                from .exchanges.asx_ib_mapper import get_asx_contract_details
                contract_details = get_asx_contract_details(clean_symbol)
                settings.update(contract_details)
            except (ImportError, AttributeError):
                pass
        
        # Handle SGX (Singapore) stocks
        elif exchange == "SGX" or (not exchange and symbol.endswith(".SI")):
            # Clean symbol by removing .SI suffix if present
            clean_symbol = symbol[:-3] if symbol.endswith(".SI") else symbol
            settings.update({
                'symbol': clean_symbol,
                'exchange': "SGX",
                'currency': "SGD"
            })
            
            # Try to use SGX mapper if available
            try:
                from .exchanges.sgx_ib_mapper import get_sgx_ib_mapper
                mapper = get_sgx_ib_mapper()
                ib_symbol = mapper.get_ib_symbol_for_data(clean_symbol)
                settings['symbol'] = ib_symbol
            except (ImportError, AttributeError):
                pass
        
        # Handle LSE (London) stocks
        elif exchange == "LSE" or (not exchange and symbol.endswith(".L")):
            # Clean symbol by removing .L suffix if present
            clean_symbol = symbol[:-2] if symbol.endswith(".L") else symbol
            settings.update({
                'symbol': clean_symbol,
                'exchange': "LSE",
                'currency': "GBP"
            })
        
        # Handle TSE (Tokyo) stocks
        elif exchange == "TSE" or (not exchange and symbol.endswith(".T")):
            # Clean symbol by removing .T suffix if present
            clean_symbol = symbol[:-2] if symbol.endswith(".T") else symbol
            settings.update({
                'symbol': clean_symbol,
                'exchange': "TSE",
                'currency': "JPY"
            })
        
        # Handle HKEX (Hong Kong) stocks
        elif exchange == "HKEX" or (not exchange and ".HK" in symbol):
            # Clean symbol by removing .HK suffix if present
            clean_symbol = symbol.split(".HK")[0] if ".HK" in symbol else symbol
            settings.update({
                'symbol': clean_symbol,
                'exchange': "HKEX",
                'currency': "HKD"
            })
        
        # Handle TSX (Toronto) stocks
        elif exchange == "TSX" or (not exchange and symbol.endswith(".TO")):
            # Clean symbol by removing .TO suffix if present
            clean_symbol = symbol[:-3] if symbol.endswith(".TO") else symbol
            settings.update({
                'symbol': clean_symbol,
                'exchange': "TSX",
                'currency': "CAD"
            })
            
        return settings
    
    async def _request_historical_data(self, contract: Contract, symbol: str, duration: str, bar_size: str) -> pd.DataFrame:
        """Request historical data using the specified contract."""
        req_id = self.get_next_request_id()
        self.historical_data[req_id] = []
        self.data_ready_events[req_id] = threading.Event()
        
        # Request historical data with proper timezone formatting
        end_date = ""  # Empty string means "now" - avoids timezone issues
        
        # Use appropriate data type based on contract type
        what_to_show = "TRADES"
        if contract.secType == "CASH":  # Forex
            what_to_show = "MIDPOINT"  # Forex uses MIDPOINT data
        
        self.client.reqHistoricalData(
            req_id, contract, end_date, duration, bar_size,
            what_to_show, 1, 1, False, []
        )
        
        # Wait for data (with timeout)
        if self.data_ready_events[req_id].wait(timeout=30):
            data = self.historical_data[req_id]
            
            if data:
                df = pd.DataFrame(data)
                # Handle datetime parsing with timezone info
                try:
                    # Handle various IB date formats with different timezone formats
                    if any(' Hongkong' in str(d) for d in df['date']):
                        # Handle IB's Hongkong timezone format
                        df['date'] = df['date'].str.replace(' Hongkong', '')
                        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H:%M:%S')
                    elif any(' Australia/NSW' in str(d) for d in df['date']):
                        # Handle IB's Australia/NSW timezone format
                        df['date'] = df['date'].str.replace(' Australia/NSW', '')
                        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H:%M:%S')
                    elif any(' US/Eastern' in str(d) for d in df['date']):
                        # Handle IB's US/Eastern timezone format
                        df['date'] = df['date'].str.replace(' US/Eastern', '')
                        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H:%M:%S')
                    else:
                        try:
                            # Standard format
                            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H:%M:%S')
                        except ValueError:
                            # Daily bars only have date (no time)
                            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
                except Exception as e:
                    logger.warning(f"Date parsing fallback for {symbol}: {e}")
                    # Last resort fallback
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                
                df.set_index('date', inplace=True)
                # Keep lowercase column names for consistency
                df = df[['open', 'high', 'low', 'close', 'volume']]
                
                logger.info(f"Retrieved {len(df)} historical bars for {symbol}")
                return df
            else:
                logger.warning(f"No historical data received for {symbol}")
                return pd.DataFrame()
        else:
            logger.error(f"Historical data request timeout for {symbol}")
            return pd.DataFrame()
            
    async def get_contract_details(self, symbol: str, asset_type: str = "stock", exchange: str = None) -> Dict[str, Any]:
        """Get contract details for a symbol."""
        try:
            # Apply rate limiting
            await self.rate_limiter.wait_for_rate_limit("contract_details", symbol=symbol, asset_type=asset_type)
            
            # Create appropriate contract
            if asset_type.lower() == "stock":
                contract = self.create_stock_contract(symbol, exchange or "SMART")
            elif asset_type.lower() == "forex":
                if "/" in symbol:
                    base, quote = symbol.split("/")
                    contract = self.create_forex_contract(base, quote)
                else:
                    contract = self.create_forex_contract(symbol[:3], symbol[3:])
            elif asset_type.lower() == "crypto":
                contract = self.create_crypto_contract(symbol, exchange or "PAXOS")
            elif asset_type.lower() == "index":
                contract = self.create_index_contract(symbol, exchange or "CBOE")
            elif asset_type.lower() == "commodity":
                contract = self.create_commodity_contract(symbol, exchange or "SMART")
            else:
                return {"error": f"Unsupported asset type: {asset_type}"}
                
            req_id = self.get_next_request_id()
            self.contract_details[req_id] = None
            self.data_ready_events[req_id] = threading.Event()
            
            # Request contract details
            self.client.reqContractDetails(req_id, contract)
            
            # Wait for response
            if self.data_ready_events[req_id].wait(timeout=10):
                details = self.contract_details[req_id]
                if details:
                    contract_info = details.contract
                    return {
                        "symbol": contract_info.symbol,
                        "secType": contract_info.secType,
                        "exchange": contract_info.exchange,
                        "currency": contract_info.currency,
                        "longName": details.longName,
                        "industry": getattr(details, 'industry', ''),
                        "category": getattr(details, 'category', ''),
                        "minTick": details.minTick,
                        "marketName": details.marketName,
                        "tradingHours": details.tradingHours,
                        "source": "Interactive Brokers"
                    }
                else:
                    return {"error": f"No contract details found for {symbol}"}
            else:
                return {"error": f"Contract details request timeout for {symbol}"}
                
        except Exception as e:
            logger.error(f"Contract details request failed for {symbol}: {e}")
            return {"error": str(e)}
            
    async def get_market_data_snapshot(self, symbols: List[str], asset_type: str = "stock") -> Dict[str, Dict[str, Any]]:
        """Get market data snapshots for multiple symbols."""
        results = {}
        for symbol in symbols:
            try:
                # Rate limiting is handled within get_quote
                quote = await self.get_quote(symbol, asset_type)
                results[symbol] = quote
            except Exception as e:
                logger.error(f"Failed to get data for {symbol}: {e}")
                results[symbol] = {"error": str(e)}
        return results
        
    def is_connected(self) -> bool:
        """Check if connected to IB."""
        return self.client.isConnected() and (self.connected_event.is_set() or self.next_order_id is not None)
        
    async def get_account_summary(self) -> Dict[str, Any]:
        """Get account summary (requires live account)."""
        # This would require additional implementation for account data
        # For now, return basic connection status
        return {
            "connected": self.is_connected(),
            "next_order_id": self.next_order_id,
            "client_id": self.client_id,
            "host": self.host,
            "port": self.port
        }
        
    async def get_news_headlines(self, symbol: str, asset_type: str = "stock", max_headlines: int = 10) -> List[Dict[str, Any]]:
        """Get news headlines for a symbol."""
        try:
            if not self.is_connected():
                logger.error("Not connected to IB")
                return []
            
            # Apply rate limiting
            await self.rate_limiter.wait_for_rate_limit("news", symbol=symbol)
            
            # Create appropriate contract
            if asset_type.lower() == "stock":
                contract = self.create_stock_contract(symbol)
            elif asset_type.lower() == "forex":
                if "/" in symbol:
                    base, quote = symbol.split("/")
                    contract = self.create_forex_contract(base, quote)
                else:
                    contract = self.create_forex_contract(symbol[:3], symbol[3:])
            else:
                contract = self.create_stock_contract(symbol)
            
            req_id = self.get_next_request_id()
            self.data_ready_events[req_id] = threading.Event()
            
            # Request news headlines
            self.client.reqMktData(req_id, contract, "mdoff,292", False, False, [])
            
            # Wait for headlines (shorter timeout for news)
            if self.data_ready_events[req_id].wait(timeout=10):
                headlines = self.news_headlines.get(req_id, [])
                # Sort by timestamp (newest first) and limit results
                headlines.sort(key=lambda x: x['timestamp'], reverse=True)
                return headlines[:max_headlines]
            else:
                logger.warning(f"News headlines request timeout for {symbol}")
                return []
                
        except Exception as e:
            logger.error(f"News headlines request failed for {symbol}: {e}")
            return []
            
    async def get_news_article(self, article_id: str) -> Dict[str, Any]:
        """Get full news article by ID."""
        try:
            if not self.is_connected():
                logger.error("Not connected to IB")
                return {}
            
            # Apply rate limiting
            await self.rate_limiter.wait_for_rate_limit("news_article", article_id=article_id)
            
            req_id = self.get_next_request_id()
            self.data_ready_events[req_id] = threading.Event()
            
            # Request full article
            self.client.reqNewsArticle(req_id, "BZ", article_id, [])
            
            # Wait for article
            if self.data_ready_events[req_id].wait(timeout=15):
                articles = self.news_articles.get(req_id, [])
                if articles:
                    return {
                        "article_id": article_id,
                        "content": articles[0]['text'],
                        "type": articles[0]['type']
                    }
                else:
                    return {"error": f"No article content received for {article_id}"}
            else:
                logger.warning(f"News article request timeout for {article_id}")
                return {"error": "Request timeout"}
                
        except Exception as e:
            logger.error(f"News article request failed for {article_id}: {e}")
            return {"error": str(e)}
        
    def get_supported_exchanges(self) -> Dict[str, List[str]]:
        """Get supported exchanges by asset type."""
        return {
            "stocks": ["SMART", "NYSE", "NASDAQ", "ARCA", "BATS"],
            "forex": ["IDEALPRO"],
            "crypto": ["PAXOS"],
            "indices": ["CBOE", "CME"],
            "futures": ["CME", "CBOT", "NYMEX", "COMEX"],
            "options": ["SMART", "CBOE"]
        }
        
    def format_symbol_for_ib(self, symbol: str, asset_type: str) -> str:
        """Format symbol for IB API."""
        if asset_type.lower() == "forex":
            if "/" in symbol:
                return symbol.replace("/", "")
            return symbol
        elif asset_type.lower() == "crypto":
            return symbol.replace("-", "").replace("USD", "")
        else:
            return symbol.upper()
    
    # Market Scanner Methods
    async def scan_market(self, scan_type: str = "hot_by_volume", instrument: str = "STK", 
                         location: str = "STK.US.MAJOR", num_rows: int = 20) -> List[Dict[str, Any]]:
        """Run market scanner to find securities matching criteria."""
        try:
            if not self.is_connected():
                logger.error("Not connected to IB")
                return []
            
            # Apply rate limiting
            await self.rate_limiter.wait_for_rate_limit("scanner", scan_type=scan_type, instrument=instrument, location=location)
            
            req_id = self.get_next_request_id()
            self.scanner_results[req_id] = []
            self.data_ready_events[req_id] = threading.Event()
            
            # Create scanner subscription
            scanner_sub = ScannerSubscription()
            scanner_sub.instrument = instrument
            scanner_sub.locationCode = location
            scanner_sub.scanCode = scan_type.upper()
            scanner_sub.numberOfRows = num_rows
            
            # Request scanner data
            self.client.reqScannerSubscription(req_id, scanner_sub, [], [])
            
            # Wait for results
            if self.data_ready_events[req_id].wait(timeout=15):
                results = self.scanner_results.get(req_id, [])
                logger.info(f"Scanner returned {len(results)} results")
                return results
            else:
                logger.error("Scanner request timeout")
                return []
                
        except Exception as e:
            logger.error(f"Market scanner error: {e}")
            return []
    
    async def get_hot_stocks_by_volume(self, num_stocks: int = 20) -> List[Dict[str, Any]]:
        """Get hot US stocks by volume."""
        return await self.scan_market("HOT_BY_VOLUME", "STK", "STK.US.MAJOR", num_stocks)
    
    async def get_top_gainers(self, num_stocks: int = 20) -> List[Dict[str, Any]]:
        """Get top percentage gainers."""
        return await self.scan_market("TOP_PERC_GAIN", "STK", "STK.US.MAJOR", num_stocks)
    
    async def get_top_losers(self, num_stocks: int = 20) -> List[Dict[str, Any]]:
        """Get top percentage losers."""
        return await self.scan_market("TOP_PERC_LOSE", "STK", "STK.US.MAJOR", num_stocks)
    
    async def get_most_active_stocks(self, num_stocks: int = 20) -> List[Dict[str, Any]]:
        """Get most active stocks by volume."""
        return await self.scan_market("MOST_ACTIVE", "STK", "STK.US.MAJOR", num_stocks)
    
    async def get_high_option_volume_stocks(self, num_stocks: int = 20) -> List[Dict[str, Any]]:
        """Get stocks with high option volume."""
        return await self.scan_market("HIGH_OPT_VOLUME_PUT_CALL_RATIO", "STK", "STK.US.MAJOR", num_stocks)
    
    def get_scanner_data(self, scanner_subscription, max_results: int = 20) -> List[Dict[str, Any]]:
        """Synchronous wrapper for scanner data retrieval using ScannerSubscription object."""
        try:
            if not self.is_connected():
                logger.error("Not connected to IB")
                return []
            
            req_id = self.get_next_request_id()
            self.scanner_results[req_id] = []
            self.data_ready_events[req_id] = threading.Event()
            
            # Set number of rows if not already set
            if not hasattr(scanner_subscription, 'numberOfRows') or scanner_subscription.numberOfRows is None:
                scanner_subscription.numberOfRows = max_results
            
            # Request scanner data
            self.client.reqScannerSubscription(req_id, scanner_subscription, [], [])
            
            # Wait for results
            if self.data_ready_events[req_id].wait(timeout=15):
                results = self.scanner_results.get(req_id, [])
                logger.info(f"Scanner returned {len(results)} results")
                
                # Cancel the subscription to avoid continuous data
                self.client.cancelScannerSubscription(req_id)
                
                return results
            else:
                logger.error("Scanner request timeout")
                # Cancel the subscription on timeout
                self.client.cancelScannerSubscription(req_id)
                return []
                
        except Exception as e:
            logger.error(f"Scanner data error: {e}")
            return []
    
    async def get_fundamental_data(self, symbol: str, asset_type: str = "stock") -> Dict[str, Any]:
        """Get fundamental financial data for a symbol using IB fundamental data."""
        try:
            if not self.is_connected():
                await self.connect()
            
            if not self.is_connected():
                return {"error": "Not connected to IB"}
            
            # Apply rate limiting
            await self.rate_limiter.wait_if_needed()
            
            # Create contract based on asset type
            if asset_type == "forex":
                # Parse forex symbol (e.g., EURUSD -> EUR, USD)
                if len(symbol) == 6:
                    base_currency = symbol[:3]
                    quote_currency = symbol[3:]
                    contract = self.create_forex_contract(base_currency, quote_currency)
                else:
                    return {"error": f"Invalid forex symbol format: {symbol}"}
            elif asset_type == "crypto":
                contract = self.create_crypto_contract(symbol)
            else:  # Default to stock
                contract = self.create_stock_contract(symbol)
            
            if not contract:
                return {"error": f"Could not create contract for {symbol}"}
            
            # Request fundamental data
            req_id = self.get_next_request_id()
            
            # IB fundamental data types
            fundamental_types = [
                "ReportSnapshot",  # Financial summary
                "ReportsFinSummary",  # Financial summary
                "ReportRatios",  # Financial ratios
                "RESC",  # Analyst estimates
                "CalendarReport"  # Calendar data
            ]
            
            fundamental_data = {}
            
            for data_type in fundamental_types:
                try:
                    # Request fundamental data
                    self.data_ready_events[req_id] = threading.Event()
                    self.client.reqFundamentalData(req_id, contract, data_type, [])
                    
                    # Wait for response with timeout
                    if self.data_ready_events[req_id].wait(timeout=10):
                        if req_id in self.fundamental_data:
                            data = self.fundamental_data.pop(req_id)
                            if data and not isinstance(data, dict) or not data.get('error'):
                                fundamental_data[data_type] = data
                    
                    # Clean up event
                    if req_id in self.data_ready_events:
                        del self.data_ready_events[req_id]
                    
                    req_id = self.get_next_request_id()
                    
                except Exception as e:
                    logger.warning(f"Failed to get {data_type} for {symbol}: {e}")
                    continue
            
            if fundamental_data:
                # Parse and extract key financial metrics
                parsed_data = self._parse_fundamental_data(fundamental_data, symbol)
                logger.info(f"Interactive Brokers successfully fetched fundamental data for {symbol}")
                return parsed_data
            else:
                logger.warning(f"No fundamental data available for {symbol} from IB")
                return {"error": f"No fundamental data available for {symbol}"}
                
        except Exception as e:
            logger.error(f"Fundamental data request failed for {symbol}: {e}")
            return {"error": str(e)}
    
    def _parse_fundamental_data(self, fundamental_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Parse IB fundamental data into standardized format."""
        try:
            # Initialize result with default values
            result = {
                'pe_ratio': None,
                'pb_ratio': None,
                'roa': None,
                'roe': None,
                'revenue_growth': None,
                'eps': None,
                'debt_to_equity': None,
                'current_ratio': None,
                'gross_margin': None,
                'operating_margin': None,
                'net_margin': None,
                'beta': None,
                'source': 'Interactive Brokers'
            }
            
            # Parse different data types
            for data_type, data in fundamental_data.items():
                if data_type == "ReportRatios" and isinstance(data, str):
                    # Parse XML or structured data for ratios
                    # This would require XML parsing for IB's fundamental data format
                    # For now, return basic structure
                    pass
                elif data_type == "ReportsFinSummary" and isinstance(data, str):
                    # Parse financial summary data
                    pass
            
            # Note: IB fundamental data comes in XML format and requires parsing
            # For production use, you would need to implement XML parsing
            # For now, return the structure with IB as source
            logger.info(f"Parsed fundamental data structure for {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing fundamental data for {symbol}: {e}")
            return {"error": f"Failed to parse fundamental data: {e}"}
    
    # Algorithmic Trading Order Creation
    def create_vwap_order(self, symbol: str, quantity: int, action: str = "BUY", 
                         max_pct_vol: float = 0.1, start_time: str = "", end_time: str = "") -> Order:
        """Create VWAP algorithmic order."""
        order = Order()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = "MKT"
        order.algoStrategy = "Vwap"
        order.algoParams = []
        order.algoParams.append(TagValue("maxPctVol", max_pct_vol))
        if start_time:
            order.algoParams.append(TagValue("startTime", start_time))
        if end_time:
            order.algoParams.append(TagValue("endTime", end_time))
        order.algoParams.append(TagValue("allowPastEndTime", 1))
        order.algoParams.append(TagValue("noTakeLiq", 0))
        return order
    
    def create_twap_order(self, symbol: str, quantity: int, action: str = "BUY",
                         strategy_type: str = "Marketable", start_time: str = "", end_time: str = "") -> Order:
        """Create TWAP algorithmic order."""
        order = Order()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = "MKT"
        order.algoStrategy = "Twap"
        order.algoParams = []
        order.algoParams.append(TagValue("strategyType", strategy_type))
        if start_time:
            order.algoParams.append(TagValue("startTime", start_time))
        if end_time:
            order.algoParams.append(TagValue("endTime", end_time))
        order.algoParams.append(TagValue("allowPastEndTime", 1))
        return order
    
    def create_arrival_price_order(self, symbol: str, quantity: int, action: str = "BUY",
                                  max_pct_vol: float = 0.1, risk_aversion: str = "Neutral") -> Order:
        """Create Arrival Price algorithmic order."""
        order = Order()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = "MKT"
        order.algoStrategy = "ArrivalPx"
        order.algoParams = []
        order.algoParams.append(TagValue("maxPctVol", max_pct_vol))
        order.algoParams.append(TagValue("riskAversion", risk_aversion))
        order.algoParams.append(TagValue("forceCompletion", 0))
        order.algoParams.append(TagValue("allowPastEndTime", 1))
        return order
    
    def create_adaptive_order(self, symbol: str, quantity: int, action: str = "BUY",
                             priority: str = "Normal") -> Order:
        """Create Adaptive algorithmic order."""
        order = Order()
        order.action = action
        order.totalQuantity = quantity
        order.orderType = "MKT"
        order.algoStrategy = "Adaptive"
        order.algoParams = []
        order.algoParams.append(TagValue("adaptivePriority", priority))
        return order
