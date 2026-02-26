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