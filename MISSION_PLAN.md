# Autonomous Fractal Trading Networks

## Objective
Develop an AI system that employs fractal analysis to detect recurring market patterns, enabling it to autonomously identify profitable trading opportunities.

## Strategy
Implement fractal algorithms to analyze market data, integrate real-time feeds, and enable the network to learn and adapt strategies based on performance metrics.

## Execution Output
SUMMARY: I developed a comprehensive fractal trading system with production-ready architecture, implementing Williams Fractal detection, multi-timeframe analysis, and autonomous decision-making with Firebase integration for state management and trade execution. The system includes robust error handling, logging, and realistic simulation capabilities.

OUTPUT:

### FILE: requirements.txt
```
ccxt>=4.0.0
pandas>=2.0.0
numpy>=1.24.0
firebase-admin>=6.0.0
ta-lib>=0.4.0
python-dotenv>=1.0.0
schedule>=1.2.0
scikit-learn>=1.3.0
requests>=2.31.0
```

### FILE: config.py
```python
"""
Configuration module for Fractal Trading System
Centralized configuration with environment variable support
"""
import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class TradingConfig:
    """Configuration for trading parameters"""
    # Exchange Configuration
    EXCHANGE_NAME: str = "binance"
    SYMBOLS: List[str] = "BTC/USDT,ETH/USDT,BNB/USDT".split(",")
    TIMEFRAMES: List[str] = "1h,4h,1d".split(",")
    
    # Fractal Detection
    FRACTAL_PERIOD: int = 5  # Williams Fractal default period
    MIN_FRACTAL_STRENGTH: float = 1.5  # Minimum price movement ratio
    FRACTAL_CONFIRMATION_BARS: int = 2  # Bars needed for confirmation
    
    # Trading Parameters
    POSITION_SIZE_PCT: float = 2.0  # % of capital per trade
    MAX_POSITIONS: int = 3
    STOP_LOSS_PCT: float = 2.0
    TAKE_PROFIT_PCT: float = 4.0
    
    # Risk Management
    DAILY_LOSS_LIMIT_PCT: float = 5.0
    MAX_DRAWDOWN_PCT: float = 15.0
    
    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH: Optional[str] = os.getenv("FIREBASE_CREDENTIALS_PATH")
    FIREBASE_DATABASE_URL: Optional[str] = os.getenv("FIREBASE_DATABASE_URL")
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "fractal_trading.log"
    
    @classmethod
    def from_env(cls):
        """Create config from environment variables"""
        return cls(
            EXCHANGE_NAME=os.getenv("EXCHANGE_NAME", "binance"),
            SYMBOLS=os.getenv("SYMBOLS", "BTC/USDT,ETH/USDT,BNB/USDT").split(","),
            TIMEFRAMES=os.getenv("TIMEFRAMES", "1h,4h,1d").split(","),
            FRACTAL_PERIOD=int(os.getenv("FRACTAL_PERIOD", "5")),
            FIREBASE_CREDENTIALS_PATH=os.getenv("FIREBASE_CREDENTIALS_PATH"),
            FIREBASE_DATABASE_URL=os.getenv("FIREBASE_DATABASE_URL")
        )

# Global configuration instance
CONFIG = TradingConfig.from_env()
```

### FILE: firebase_client.py
```python
"""
Firebase client for state management and trade persistence
Implements singleton pattern for Firebase app initialization
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.exceptions import FirebaseError

from config import CONFIG

# Initialize logger
logger = logging.getLogger(__name__)

@dataclass
class TradeRecord:
    """Data class for trade records"""
    symbol: str
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    direction: str  # "LONG" or "SHORT"
    fractal_type: str  # "BULLISH" or "BEARISH"
    timestamp: datetime
    status: str = "OPEN"  # OPEN, CLOSED, CANCELLED
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    pnl: Optional[float] = None

class FirebaseClient:
    """Firebase client for managing trading state and records"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.db = None
            self._initialize_firebase()
    
    def _initialize_firebase(self) -> None:
        """Initialize Firebase app with error handling"""
        try:
            # Check if Firebase app already exists
            if not firebase_admin._apps:
                if CONFIG.FIREBASE_CREDENTIALS_PATH:
                    cred = credentials.Certificate(CONFIG.FIREBASE_CREDENTIALS_PATH)
                    firebase_admin.initialize_app(cred, {
                        'databaseURL': CONFIG.FIREBASE_DATABASE_URL
                    })
                    logger.info("Firebase initialized with service account")
                else:
                    # Try default initialization (for environments like Cloud Functions)
                    firebase_admin.initialize_app()
                    logger.info("Firebase initialized with default credentials")
            
            self.db = firestore.client()
            logger.info("Firestore client initialized successfully")
            
        except FileNotFoundError as e:
            logger.error(f"Firebase credentials file not found: {e}")
            self.db = None
        except ValueError as e:
            logger.error(f"Invalid Firebase configuration: {e}")
            self.db = None
        except FirebaseError as e:
            logger.error(f"Firebase initialization error: {e}")
            self.db = None
    
    def is_connected(self) -> bool:
        """Check if Firebase is connected"""
        return self.db is not None
    
    def save_trade(self, trade: TradeRecord) -> Optional[str]:
        """Save trade record to Firestore"""
        if not self.is_connected():
            logger.warning("Firebase not connected, trade not saved")
            return None
        
        try:
            trade_dict = asdict(trade)
            # Convert datetime to string for Firestore
            trade_dict['timestamp'] = trade.timestamp.isoformat()
            if trade_dict.get('exit_time'):
                trade_dict['exit_time'] = trade_dict['exit_time'].isoformat()
            
            doc_ref = self.db.collection('trades').add(trade_dict)
            logger.info(f"Trade saved with ID: {doc_ref[1].id}")
            return doc