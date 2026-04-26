"""
📊 وحدة جلب البيانات (Data Fetcher)
جلب الشموع من Binance و TradingView
"""

import pandas as pd
import numpy as np
import ccxt
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from config import DEFAULT_CANDLES, MIN_CANDLES_REQUIRED, TRADINGVIEW_API

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ DATA CLASSES ============
@dataclass
class Candle:
    """تمثيل شمعة واحدة"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }
    
    @property
    def hl2(self) -> float:
        """High + Low / 2"""
        return (self.high + self.low) / 2
    
    @property
    def hlc3(self) -> float:
        """High + Low + Close / 3"""
        return (self.high + self.low + self.close) / 3
    
    @property
    def ohlc4(self) -> float:
        """Open + High + Low + Close / 4"""
        return (self.open + self.high + self.low + self.close) / 4
    
    @property
    def body_size(self) -> float:
        """حجم جسم الشمعة"""
        return abs(self.close - self.open)
    
    @property
    def wick_size(self) -> float:
        """حجم الفتيل الكامل"""
        return self.high - self.low
    
    @property
    def range(self) -> float:
        """النطاق من الأقل للأعلى"""
        return self.high - self.low
    
    @property
    def is_bullish(self) -> bool:
        """هل الشمعة صاعدة"""
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        """هل الشمعة هابطة"""
        return self.close < self.open


@dataclass
class CandleData:
    """مجموعة من الشموع"""
    symbol: str
    timeframe: str
    candles: List[Candle]
    last_update: datetime
    
    def to_dataframe(self) -> pd.DataFrame:
        """تحويل إلى DataFrame"""
        data = [c.to_dict() for c in self.candles]
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    
    def __len__(self):
        return len(self.candles)
    
    def latest(self) -> Candle:
        """آخر شمعة"""
        return self.candles[-1] if self.candles else None


# ============ DATA FETCHER CLASS ============
class DataFetcher:
    """جلب البيانات من Binance"""
    
    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        self._cache = {}
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = DEFAULT_CANDLES
    ) -> CandleData:
        """
        جلب الشموع من Binance
        
        Args:
            symbol: مثل "BTC/USDT"
            timeframe: مثل "1h", "4h", "1d"
            limit: عدد الشموع
        
        Returns:
            CandleData: مجموعة الشموع
        """
        try:
            logger.info(f"جلب البيانات: {symbol} {timeframe}")
            
            # جلب من API
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            if not ohlcv:
                raise ValueError(f"لا توجد بيانات لـ {symbol}")
            
            if len(ohlcv) < MIN_CANDLES_REQUIRED:
                raise ValueError(
                    f"عدد الشموع {len(ohlcv)} أقل من الحد الأدنى {MIN_CANDLES_REQUIRED}"
                )
            
            # تحويل إلى Candle objects
            candles = [
                Candle(
                    timestamp=int(row[0]),
                    open=float(row[1]),
                    high=float(row[2]),
                    low=float(row[3]),
                    close=float(row[4]),
                    volume=float(row[5])
                )
                for row in ohlcv
            ]
            
            # تخزين في الـ cache
            cache_key = f"{symbol}_{timeframe}"
            self._cache[cache_key] = {
                'data': candles,
                'timestamp': datetime.now()
            }
            
            return CandleData(
                symbol=symbol,
                timeframe=timeframe,
                candles=candles,
                last_update=datetime.now()
            )
        
        except Exception as e:
            logger.error(f"خطأ في جلب البيانات: {e}")
            raise
    
    def get_from_cache(self, symbol: str, timeframe: str, max_age_seconds: int = 300):
        """جلب من الـ cache إذا كان طازج"""
        cache_key = f"{symbol}_{timeframe}"
        
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            age = (datetime.now() - cached['timestamp']).total_seconds()
            
            if age < max_age_seconds:
                logger.info(f"استخدام البيانات المخزنة: {symbol} {timeframe}")
                return CandleData(
                    symbol=symbol,
                    timeframe=timeframe,
                    candles=cached['data'],
                    last_update=cached['timestamp']
                )
        
        return None
    
    def get_supported_symbols(self) -> List[str]:
        """الحصول على قائمة الرموز المدعومة"""
        try:
            symbols = self.exchange.symbols
            # فلترة لـ USDT فقط
            usdt_symbols = [s for s in symbols if s.endswith('/USDT')]
            return sorted(usdt_symbols)[:50]  # أول 50
        except Exception as e:
            logger.error(f"خطأ في جلب الرموز: {e}")
            return []
    
    def get_ticker(self, symbol: str) -> Dict:
        """جلب معلومات السعر الحالي"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'high_24h': ticker['high'],
                'low_24h': ticker['low'],
                'change_24h': ticker['percentage'],
                'volume_24h': ticker['quoteVolume']
            }
        except Exception as e:
            logger.error(f"خطأ في جلب الـ ticker: {e}")
            return None
    
    def resample_candles(
        self,
        candle_data: CandleData,
        target_timeframe: str
    ) -> CandleData:
        """
        تحويل الشموع إلى timeframe أكبر
        مثل: 1h -> 4h
        """
        try:
            df = candle_data.to_dataframe()
            
            # تحديد المدة بالدقائق
            timeframe_minutes = {
                '1m': 1, '5m': 5, '15m': 15, '30m': 30,
                '1h': 60, '4h': 240, '1d': 1440
            }
            
            if target_timeframe not in timeframe_minutes:
                raise ValueError(f"Timeframe غير مدعوم: {target_timeframe}")
            
            # تجميع البيانات
            df.set_index('datetime', inplace=True)
            period = f"{timeframe_minutes[target_timeframe]}min"
            
            resampled = df.resample(period).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            # تحويل للخلف إلى Candle objects
            candles = [
                Candle(
                    timestamp=int(row['datetime'].timestamp() * 1000),
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row['volume']
                )
                for _, row in resampled.iterrows()
            ]
            
            return CandleData(
                symbol=candle_data.symbol,
                timeframe=target_timeframe,
                candles=candles,
                last_update=datetime.now()
            )
        
        except Exception as e:
            logger.error(f"خطأ في تحويل الـ timeframe: {e}")
            raise
    
    def clear_cache(self):
        """مسح الـ cache"""
        self._cache.clear()
        logger.info("تم مسح الـ cache")


# ============ SINGLETON PATTERN ============
_data_fetcher_instance = None

def get_data_fetcher() -> DataFetcher:
    """الحصول على instance واحد من DataFetcher"""
    global _data_fetcher_instance
    if _data_fetcher_instance is None:
        _data_fetcher_instance = DataFetcher()
    return _data_fetcher_instance
