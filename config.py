"""
⚙️ إعدادات تطبيق HABIICT_PRO
"""

import os
from dotenv import load_dotenv

# تحميل المتغيرات من .env
load_dotenv()

# ============ API KEYS ============
# استخدم Streamlit Secrets في الإنتاج
try:
    import streamlit as st
    BINANCE_API_KEY = st.secrets.get("BINANCE_API_KEY", os.getenv("BINANCE_API_KEY", ""))
    BINANCE_API_SECRET = st.secrets.get("BINANCE_API_SECRET", os.getenv("BINANCE_API_SECRET", ""))
    TRADINGVIEW_API = st.secrets.get("TRADINGVIEW_API", os.getenv("TRADINGVIEW_API", ""))
except:
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
    TRADINGVIEW_API = os.getenv("TRADINGVIEW_API", "")

# ============ SOLANA CONFIG ============
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
SOLANA_NETWORK = "mainnet-beta"

# ============ TRADING CONFIG ============
DEFAULT_SYMBOL = "BTC/USDT"
DEFAULT_TIMEFRAME = "1h"
DEFAULT_CANDLES = 1000
MIN_CANDLES_REQUIRED = 50

# TIMEFRAMES المدعومة
SUPPORTED_TIMEFRAMES = {
    "15m": "15 دقيقة",
    "30m": "30 دقيقة",
    "1h": "ساعة",
    "4h": "4 ساعات",
    "1d": "يوم"
}

# SYMBOLS الشهيرة
POPULAR_SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "ADA/USDT",
    "DOGE/USDT",
    "LINK/USDT",
]

# ============ ICT PARAMETERS ============
class ICTConfig:
    # Order Block
    OB_MIN_HEIGHT = 0.002  # 0.2% minimum
    OB_LOOKBACK = 20  # شموع للخلف
    
    # Fair Value Gap
    FVG_MIN_SIZE = 0.001  # 0.1% minimum
    FVG_LOOKBACK = 5
    
    # Liquidity Levels
    LIQUIDITY_LOOKBACK = 50
    LIQUIDITY_THRESHOLD = 0.98  # 98% من الحجم
    
    # Market Structure
    MSS_CANDLES_BACK = 30
    
    # Signal Strength
    MIN_CONFLUENCE_POINTS = 2  # عدد نقاط التقاء الحد الأدنى

# ============ RISK MANAGEMENT ============
class RiskConfig:
    DEFAULT_ACCOUNT_SIZE = 1000  # $1000
    DEFAULT_RISK_PERCENTAGE = 2.0  # 2% من الحساب
    DEFAULT_REWARD_RATIO = 1.5  # 1:1.5 Risk:Reward
    
    MAX_POSITION_SIZE = 5  # 5% من الحساب الواحد
    MAX_OPEN_TRADES = 5
    
    SLIPPAGE_TOLERANCE = 0.1  # 0.1%

# ============ UI COLORS ============
class UIColors:
    BULLISH = "#00CC99"  # أخضر
    BEARISH = "#FF3333"  # أحمر
    NEUTRAL = "#CCCCCC"  # رمادي
    OB_COLOR = "#4A90E2"  # أزرق
    FVG_COLOR = "#F5A623"  # برتقالي
    LIQUIDITY_COLOR = "#7ED321"  # أخضر فاتح

# ============ CACHE CONFIG ============
CACHE_DURATION = 300  # 5 دقائق بالثواني
CACHE_MAX_SIZE = 100  # عدد الـ entries القصوى

# ============ LOGGING ============
LOG_LEVEL = "INFO"
LOG_FILE = "habiict_pro.log"

# ============ VERSION ============
VERSION = "1.0.0"
APP_NAME = "HABIICT PRO - Smart Money Concepts Analyzer"
