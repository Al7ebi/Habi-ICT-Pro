"""
📍 وكيل تحديد الاتجاه (Director Agent)
تحديد Bias (Bullish/Bearish) والاتجاه الرئيسي
"""

from dataclasses import dataclass
from enum import Enum
from typing import List
from core.ict_logic import ICTAnalysis, Direction, MarketStructure
import logging

logger = logging.getLogger(__name__)


@dataclass
class DirectorSignal:
    """إشارة من وكيل Director"""
    bias: Direction
    confidence: float  # 0.0 - 1.0
    reasons: List[str]
    trend_confirmation: bool
    higher_timeframe_bias: Direction = None
    

class DirectorAgent:
    """
    وكيل تحديد الاتجاه
    يحلل المؤشرات ويحدد اتجاه السوق
    """
    
    def __init__(self):
        self.previous_signal = None
    
    def analyze(
        self,
        ict_analysis: ICTAnalysis,
        htf_analysis: ICTAnalysis = None  # Higher TimeFrame
    ) -> DirectorSignal:
        """
        تحليل الاتجاه بناءً على تحليل ICT
        """
        reasons = []
        confidence_factors = []
        
        # 1. Market Structure
        ms_confidence, ms_reason = self._analyze_market_structure(ict_analysis)
        confidence_factors.append(ms_confidence)
        if ms_reason:
            reasons.append(ms_reason)
        
        # 2. Order Blocks
        ob_confidence, ob_reason = self._analyze_order_blocks(ict_analysis)
        confidence_factors.append(ob_confidence)
        if ob_reason:
            reasons.append(ob_reason)
        
        # 3. FVG Levels
        fvg_confidence, fvg_reason = self._analyze_fvgs(ict_analysis)
        confidence_factors.append(fvg_confidence)
        if fvg_reason:
            reasons.append(fvg_reason)
        
        # 4. Higher TimeFrame Confirmation
        htf_confidence, htf_reason = self._analyze_htf(htf_analysis)
        confidence_factors.append(htf_confidence)
        if htf_reason:
            reasons.append(htf_reason)
        
        # حساب الـ bias والـ confidence
        bias = ict_analysis.overall_bias
        confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
        
        # التحقق من تأكيد الاتجاه
        trend_confirmation = self._confirm_trend(ict_analysis)
        
        # الـ HTF bias (إذا توفر)
        htf_bias = htf_analysis.overall_bias if htf_analysis else None
        
        signal = DirectorSignal(
            bias=bias,
            confidence=confidence,
            reasons=reasons,
            trend_confirmation=trend_confirmation,
            higher_timeframe_bias=htf_bias
        )
        
        self.previous_signal = signal
        return signal
    
    def _analyze_market_structure(self, ict: ICTAnalysis) -> tuple:
        """تحليل هيكل السوق"""
        ms = ict.market_structure
        
        if ms.direction == Direction.BULLISH:
            # تحقق من HH/HL
            if len(ms.higher_highs) > len(ms.lower_highs) and \
               len(ms.higher_lows) > len(ms.lower_lows):
                confidence = 0.9
                reason = "✅ هيكل صعودي قوي (HH/HL)"
            else:
                confidence = 0.5
                reason = "⚠️ هيكل صعودي ضعيف"
        
        elif ms.direction == Direction.BEARISH:
            # تحقق من LL/LH
            if len(ms.lower_lows) > len(ms.higher_lows) and \
               len(ms.lower_highs) > len(ms.higher_highs):
                confidence = 0.9
                reason = "✅ هيكل هابط قوي (LL/LH)"
            else:
                confidence = 0.5
                reason = "⚠️ هيكل هابط ضعيف"
        
        else:
            confidence = 0.3
            reason = "➡️ السوق محايد - بدون هيكل واضح"
        
        return confidence, reason
    
    def _analyze_order_blocks(self, ict: ICTAnalysis) -> tuple:
        """تحليل Order Blocks"""
        if not ict.order_blocks:
            return 0.3, "⚠️ لا توجد Order Blocks واضحة"
        
        # أقوى OB
        strongest_ob = ict.order_blocks[0]
        
        if strongest_ob.direction == Direction.BULLISH:
            confidence = min(0.9, 0.5 + strongest_ob.strength)
            reason = f"✅ OB صعودي قوي (القوة: {strongest_ob.strength:.2f})"
        else:
            confidence = min(0.9, 0.5 + strongest_ob.strength)
            reason = f"✅ OB هابط قوي (القوة: {strongest_ob.strength:.2f})"
        
        return confidence, reason
    
    def _analyze_fvgs(self, ict: ICTAnalysis) -> tuple:
        """تحليل Fair Value Gaps"""
        if not ict.fair_value_gaps:
            return 0.3, "⚠️ لا توجد FVGs"
        
        # احسب عدد FVGs الصاعدة والهابطة
        bullish_fvgs = sum(1 for f in ict.fair_value_gaps if f.direction == Direction.BULLISH)
        bearish_fvgs = sum(1 for f in ict.fair_value_gaps if f.direction == Direction.BEARISH)
        
        if bullish_fvgs > bearish_fvgs:
            confidence = 0.6
            reason = f"📊 المزيد من FVGs الصاعدة ({bullish_fvgs} vs {bearish_fvgs})"
        elif bearish_fvgs > bullish_fvgs:
            confidence = 0.6
            reason = f"📊 المزيد من FVGs الهابطة ({bearish_fvgs} vs {bullish_fvgs})"
        else:
            confidence = 0.4
            reason = "📊 FVGs متوازنة"
        
        return confidence, reason
    
    def _analyze_htf(self, htf_analysis: ICTAnalysis = None) -> tuple:
        """تحليل Higher TimeFrame"""
        if not htf_analysis:
            return 0.5, None
        
        confidence = 0.8
        
        if htf_analysis.overall_bias == Direction.BULLISH:
            reason = "📈 HTF صعودي = دعم قوي"
        elif htf_analysis.overall_bias == Direction.BEARISH:
            reason = "📉 HTF هابط = ضغط قوي"
        else:
            confidence = 0.4
            reason = "➡️ HTF محايد"
        
        return confidence, reason
    
    def _confirm_trend(self, ict: ICTAnalysis) -> bool:
        """التحقق من تأكيد الاتجاه"""
        # تأكيد = حداقل 3 OBs أو FVGs من نفس الاتجاه
        same_direction_count = 0
        
        for ob in ict.order_blocks[:3]:
            if ob.direction == ict.overall_bias:
                same_direction_count += 1
        
        for fvg in ict.fair_value_gaps[:3]:
            if fvg.direction == ict.overall_bias:
                same_direction_count += 1
        
        return same_direction_count >= 3
    
    def get_signal_summary(self, signal: DirectorSignal) -> str:
        """ملخص الإشارة بصيغة نصية"""
        bias_text = {
            Direction.BULLISH: "🟢 BULLISH",
            Direction.BEARISH: "🔴 BEARISH",
            Direction.NEUTRAL: "⚪ NEUTRAL"
        }
        
        confidence_text = f"{signal.confidence * 100:.0f}%"
        
        if signal.higher_timeframe_bias:
            htf_text = bias_text[signal.higher_timeframe_bias]
        else:
            htf_text = "بدون بيانات"
        
        summary = f"""
        📍 تحليل الاتجاه (Director):
        ══════════════════════════════
        الإشارة: {bias_text[signal.bias]}
        الثقة: {confidence_text}
        تأكيد الاتجاه: {'✅' if signal.trend_confirmation else '❌'}
        HTF Bias: {htf_text}
        
        الأسباب:
        {chr(10).join(['• ' + r for r in signal.reasons])}
        """
        
        return summary
