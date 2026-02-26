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