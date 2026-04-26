"""
🔍 محرك تحليل ICT (Inner Circle Trader)
تعرف الأنماط: Order Blocks, Fair Value Gaps, Liquidity, Market Structure
"""

import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# ============ ENUMS ============
class PatternType(Enum):
    """أنواع الأنماط"""
    ORDER_BLOCK = "Order Block"
    FVG = "Fair Value Gap"
    LIQUIDITY = "Liquidity"
    MARKET_STRUCTURE = "Market Structure"


class Direction(Enum):
    """الاتجاهات"""
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"


# ============ DATA CLASSES ============
@dataclass
class OrderBlock:
    """Order Block - منطقة تجميع الطلبات"""
    start_index: int
    end_index: int
    high: float
    low: float
    direction: Direction
    strength: float = 0.5  # 0.0 - 1.0
    candles_count: int = 0
    volume_ratio: float = 0.0
    
    @property
    def mid_price(self) -> float:
        return (self.high + self.low) / 2
    
    @property
    def range(self) -> float:
        return self.high - self.low
    
    def contains(self, price: float) -> bool:
        """هل السعر موجود في الـ block"""
        return self.low <= price <= self.high


@dataclass
class FairValueGap:
    """FVG - الفجوة التي لم يتم ملأها بعد"""
    start_index: int
    candle_index: int  # شمعة FVG
    top: float
    bottom: float
    direction: Direction
    gap_size: float = 0.0
    mitigated: bool = False
    mitigation_index: int = -1
    
    @property
    def mid_price(self) -> float:
        return (self.top + self.bottom) / 2
    
    @property
    def range(self) -> float:
        return self.top - self.bottom
    
    def contains(self, price: float) -> bool:
        """هل السعر موجود في الـ gap"""
        return self.bottom <= price <= self.top


@dataclass
class LiquidityLevel:
    """مستوى السيولة (Highs/Lows السابقة)"""
    price: float
    type: str  # "High" or "Low"
    index: int  # رقم الشمعة
    strength: float = 0.5  # 0.0 - 1.0
    touched_count: int = 0
    last_touched_index: int = -1


@dataclass
class MarketStructure:
    """هيكل السوق (HH/LL, LH/HL)"""
    direction: Direction
    higher_highs: List[Tuple[int, float]]  # [(index, price), ...]
    lower_lows: List[Tuple[int, float]]
    higher_lows: List[Tuple[int, float]]
    lower_highs: List[Tuple[int, float]]
    last_mss_index: int = -1  # آخر Market Structure Shift
    last_bos_index: int = -1  # آخر Break Of Structure


@dataclass
class ICTAnalysis:
    """تحليل ICT كامل"""
    symbol: str
    timeframe: str
    candles_count: int
    
    order_blocks: List[OrderBlock] = field(default_factory=list)
    fair_value_gaps: List[FairValueGap] = field(default_factory=list)
    liquidity_levels: List[LiquidityLevel] = field(default_factory=list)
    market_structure: MarketStructure = None
    
    overall_bias: Direction = Direction.NEUTRAL
    strength: float = 0.5


# ============ ICT LOGIC ENGINE ============
class ICTLogic:
    """محرك تحليل ICT"""
    
    def __init__(self, config=None):
        self.config = config or self._default_config()
    
    @staticmethod
    def _default_config():
        """الإعدادات الافتراضية"""
        return {
            'ob_min_height': 0.002,
            'ob_lookback': 20,
            'fvg_min_size': 0.001,
            'fvg_lookback': 5,
            'liquidity_lookback': 50,
            'mss_candles_back': 30,
        }
    
    def analyze(self, candles) -> ICTAnalysis:
        """
        تحليل شامل للشموع
        """
        if len(candles) < 50:
            raise ValueError("يحتاج 50 شمعة على الأقل")
        
        # استخراج الأنماط
        order_blocks = self._detect_order_blocks(candles)
        fair_value_gaps = self._detect_fvg(candles)
        liquidity_levels = self._detect_liquidity(candles)
        market_structure = self._analyze_market_structure(candles)
        
        # تحديد الـ bias العام
        overall_bias = self._determine_bias(market_structure)
        
        # حساب قوة التحليل
        strength = self._calculate_strength(
            order_blocks, fair_value_gaps, liquidity_levels
        )
        
        return ICTAnalysis(
            symbol="",
            timeframe="",
            candles_count=len(candles),
            order_blocks=order_blocks,
            fair_value_gaps=fair_value_gaps,
            liquidity_levels=liquidity_levels,
            market_structure=market_structure,
            overall_bias=overall_bias,
            strength=strength
        )
    
    def _detect_order_blocks(self, candles) -> List[OrderBlock]:
        """
        تعرف Order Blocks
        OB = منطقة تجميع طلبات الـ Institutions قبل حركة كبيرة
        """
        obs = []
        lookback = self.config['ob_lookback']
        min_height = self.config['ob_min_height']
        
        for i in range(lookback, len(candles) - 1):
            current = candles[i]
            next_candle = candles[i + 1]
            
            # تحقق من الانفصال (Break)
            if current.is_bullish and next_candle.low > current.high:
                # Bullish Break = Bearish OB
                obs.append(OrderBlock(
                    start_index=max(0, i - 3),
                    end_index=i,
                    high=current.high,
                    low=min(c.low for c in candles[max(0, i-3):i+1]),
                    direction=Direction.BEARISH,
                    strength=self._calculate_ob_strength(candles, i, 3),
                    candles_count=4
                ))
            
            elif current.is_bearish and next_candle.high < current.low:
                # Bearish Break = Bullish OB
                obs.append(OrderBlock(
                    start_index=max(0, i - 3),
                    end_index=i,
                    high=max(c.high for c in candles[max(0, i-3):i+1]),
                    low=current.low,
                    direction=Direction.BULLISH,
                    strength=self._calculate_ob_strength(candles, i, 3),
                    candles_count=4
                ))
        
        # فلترة الضعيفة
        obs = [ob for ob in obs if ob.range >= min_height * candles[-1].close]
        return sorted(obs, key=lambda x: x.strength, reverse=True)[:10]
    
    def _detect_fvg(self, candles) -> List[FairValueGap]:
        """
        تعرف Fair Value Gaps (FVG)
        FVG = فجوة بين شمعتين لم يتم ملأها بعد
        """
        fvgs = []
        
        for i in range(2, len(candles) - 1):
            prev = candles[i - 2]
            current = candles[i - 1]
            next_candle = candles[i]
            
            # Bullish FVG: السعر صعد بسرعة وترك فجوة تحته
            if prev.high < current.low and current.low < next_candle.close:
                gap_size = current.low - prev.high
                if gap_size >= self.config['fvg_min_size'] * candles[-1].close:
                    fvgs.append(FairValueGap(
                        start_index=i - 2,
                        candle_index=i - 1,
                        top=current.low,
                        bottom=prev.high,
                        direction=Direction.BULLISH,
                        gap_size=gap_size
                    ))
            
            # Bearish FVG: السعر هبط بسرعة وترك فجوة فوقه
            elif prev.low > current.high and current.high > next_candle.close:
                gap_size = prev.low - current.high
                if gap_size >= self.config['fvg_min_size'] * candles[-1].close:
                    fvgs.append(FairValueGap(
                        start_index=i - 2,
                        candle_index=i - 1,
                        top=prev.low,
                        bottom=current.high,
                        direction=Direction.BEARISH,
                        gap_size=gap_size
                    ))
        
        # تحديد FVGs المغطاة
        for fvg in fvgs:
            for j in range(fvg.candle_index + 1, len(candles)):
                if candles[j].contains_price(fvg.top, fvg.bottom):
                    fvg.mitigated = True
                    fvg.mitigation_index = j
                    break
        
        return sorted(fvgs, key=lambda x: x.gap_size, reverse=True)[:15]
    
    def _detect_liquidity(self, candles) -> List[LiquidityLevel]:
        """
        تعرف مستويات السيولة
        = الـ Highs والـ Lows السابقة اللي المتداولون يستهدفونها
        """
        liquidity_levels = []
        lookback = self.config['liquidity_lookback']
        
        # جمع جميع الـ Highs و Lows
        for i in range(lookback, len(candles)):
            window = candles[i - lookback:i]
            highest = max(c.high for c in window)
            lowest = min(c.low for c in window)
            
            # High
            for j, c in enumerate(window):
                if abs(c.high - highest) < 0.0001:
                    liquidity_levels.append(LiquidityLevel(
                        price=highest,
                        type="High",
                        index=i - lookback + j,
                        strength=0.7
                    ))
                    break
            
            # Low
            for j, c in enumerate(window):
                if abs(c.low - lowest) < 0.0001:
                    liquidity_levels.append(LiquidityLevel(
                        price=lowest,
                        type="Low",
                        index=i - lookback + j,
                        strength=0.7
                    ))
                    break
        
        # إزالة التكرارات
        unique_levels = []
        for level in liquidity_levels:
            if not any(abs(ul.price - level.price) < 0.0001 for ul in unique_levels):
                unique_levels.append(level)
        
        return sorted(unique_levels, key=lambda x: x.index, reverse=True)[:20]
    
    def _analyze_market_structure(self, candles) -> MarketStructure:
        """
        تحليل هيكل السوق
        """
        lookback = self.config['mss_candles_back']
        window = candles[-lookback:]
        
        # البحث عن HH, LL, HL, LH
        higher_highs = []
        lower_lows = []
        higher_lows = []
        lower_highs = []
        
        for i in range(1, len(window)):
            # HH/LL
            if i > 0:
                if window[i].high > window[i-1].high:
                    higher_highs.append((len(candles) - lookback + i, window[i].high))
                elif window[i].high < window[i-1].high:
                    lower_highs.append((len(candles) - lookback + i, window[i].high))
                
                if window[i].low < window[i-1].low:
                    lower_lows.append((len(candles) - lookback + i, window[i].low))
                elif window[i].low > window[i-1].low:
                    higher_lows.append((len(candles) - lookback + i, window[i].low))
        
        # تحديد الـ bias
        if len(higher_highs) > len(lower_highs):
            direction = Direction.BULLISH
        elif len(lower_lows) > len(higher_lows):
            direction = Direction.BEARISH
        else:
            direction = Direction.NEUTRAL
        
        return MarketStructure(
            direction=direction,
            higher_highs=higher_highs,
            lower_lows=lower_lows,
            higher_lows=higher_lows,
            lower_highs=lower_highs
        )
    
    def _determine_bias(self, market_structure: MarketStructure) -> Direction:
        """تحديد الاتجاه العام"""
        return market_structure.direction
    
    def _calculate_ob_strength(self, candles, index, lookback) -> float:
        """حساب قوة Order Block"""
        obs_candles = candles[max(0, index-lookback):index+1]
        volume = sum(c.volume for c in obs_candles)
        avg_volume = volume / len(obs_candles) if obs_candles else 1
        
        # قوة بناءً على الحجم
        strength = min(1.0, avg_volume / (max(c.volume for c in candles) + 1))
        return strength
    
    def _calculate_strength(self, obs, fvgs, liquidity) -> float:
        """حساب قوة التحليل الكلي"""
        factors = []
        
        if obs:
            factors.append(min(1.0, len(obs) / 5))
        if fvgs:
            factors.append(min(1.0, len(fvgs) / 10))
        if liquidity:
            factors.append(min(1.0, len(liquidity) / 10))
        
        return np.mean(factors) if factors else 0.3


# ============ UTILITY FUNCTIONS ============
def add_price_methods(candle_class):
    """إضافة دوال السعر للـ Candle class"""
    def contains_price(self, top, bottom):
        return self.low <= bottom and self.high >= top
    
    candle_class.contains_price = contains_price
    return candle_class
