"""
⚖️ وكيل إدارة المخاطر (Risk Manager Agent)
حساب حجم العقد، Entry، Stop Loss، Take Profit
"""

from dataclasses import dataclass
from typing import List, Dict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


@dataclass
class RiskParameters:
    """معاملات المخاطر"""
    account_size: float  # حجم الحساب بالدولار
    risk_percentage: float  # النسبة المئوية للمخاطرة (مثل 2%)
    reward_ratio: float  # نسبة الفائدة للخطر (مثل 1.5)
    max_position_size: float  # أقصى حجم عقد (مثل 5%)
    slippage_tolerance: float  # تحمل الانزلاق (0.1%)


@dataclass
class TradeSetup:
    """إعداد التجارة الكامل"""
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float  # بالعملات (مثل 0.5 BTC)
    position_size_usd: float  # بالدولار
    risk_amount: float  # المبلغ المعرض للخطر (بالدولار)
    profit_amount: float  # المبلغ المتوقع ربحه
    risk_reward_ratio: float
    signal_type: str  # "BUY" or "SELL"
    confidence: float
    candle_price: float  # السعر الحالي


class RiskManagerAgent:
    """
    وكيل إدارة المخاطر
    يحسب حجم العقد والـ SL و TP بناءً على المخاطر
    """
    
    def __init__(self, risk_params: RiskParameters):
        self.risk_params = risk_params
    
    def calculate_trade_setup(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        current_price: float,
        signal_type: str = "BUY",
        confluence_factor: float = 1.0,
        confidence: float = 0.5
    ) -> TradeSetup:
        """
        حساب إعداد التجارة الكامل
        
        Args:
            entry_price: سعر الدخول
            stop_loss: سعر إيقاف الخسارة
            take_profit: سعر الهدف
            current_price: السعر الحالي
            signal_type: "BUY" أو "SELL"
            confluence_factor: عامل التقارب (1.0 - 3.0)
            confidence: ثقة الإشارة (0.0 - 1.0)
        
        Returns:
            TradeSetup: إعداد التجارة
        """
        
        # 1. حساب المسافة
        if signal_type == "BUY":
            risk_distance = entry_price - stop_loss
            profit_distance = take_profit - entry_price
        else:  # SELL
            risk_distance = stop_loss - entry_price
            profit_distance = entry_price - take_profit
        
        # 2. حساب حجم العقد بناءً على المخاطر
        risk_amount = (self.risk_params.account_size * self.risk_params.risk_percentage) / 100
        
        # عدل المخاطر بناءً على الثقة والـ confluence
        adjusted_risk = risk_amount * (confidence * confluence_factor)
        
        # حجم العقد = المبلغ المعرض / المسافة
        position_size_usd = adjusted_risk / (risk_distance / entry_price) if risk_distance > 0 else 0
        
        # تحقق من حد أقصى
        max_size = (self.risk_params.account_size * self.risk_params.max_position_size) / 100
        position_size_usd = min(position_size_usd, max_size)
        
        # حويل إلى عملات
        position_size = position_size_usd / entry_price if entry_price > 0 else 0
        
        # 3. حساب الفائدة المتوقعة
        profit_amount = position_size_usd * (profit_distance / entry_price)
        actual_risk_reward = profit_distance / risk_distance if risk_distance > 0 else 0
        
        # 4. مع تحمل الانزلاق
        slippage = entry_price * self.risk_params.slippage_tolerance / 100
        
        if signal_type == "BUY":
            adjusted_entry = entry_price + slippage
            adjusted_sl = stop_loss - slippage
        else:
            adjusted_entry = entry_price - slippage
            adjusted_sl = stop_loss + slippage
        
        return TradeSetup(
            entry_price=adjusted_entry,
            stop_loss=adjusted_sl,
            take_profit=take_profit,
            position_size=position_size,
            position_size_usd=position_size_usd,
            risk_amount=adjusted_risk,
            profit_amount=profit_amount,
            risk_reward_ratio=actual_risk_reward,
            signal_type=signal_type,
            confidence=confidence,
            candle_price=current_price
        )
    
    def validate_setup(self, setup: TradeSetup) -> tuple[bool, str]:
        """
        التحقق من صحة الإعداد
        """
        errors = []
        
        # 1. تحقق من الأسعار
        if setup.signal_type == "BUY":
            if setup.entry_price <= setup.stop_loss:
                errors.append("❌ Entry يجب أن يكون أعلى من SL في الشراء")
            if setup.entry_price >= setup.take_profit:
                errors.append("❌ Entry يجب أن يكون أقل من TP في الشراء")
        
        else:  # SELL
            if setup.entry_price >= setup.stop_loss:
                errors.append("❌ Entry يجب أن يكون أقل من SL في البيع")
            if setup.entry_price <= setup.take_profit:
                errors.append("❌ Entry يجب أن يكون أعلى من TP في البيع")
        
        # 2. تحقق من R:R
        if setup.risk_reward_ratio < 1.0:
            errors.append(f"⚠️ نسبة R:R ضعيفة: {setup.risk_reward_ratio:.2f}")
        
        # 3. تحقق من حجم العقد
        if setup.position_size_usd <= 0:
            errors.append("❌ حجم العقد يجب أن يكون موجب")
        
        if setup.position_size_usd > (self.risk_params.account_size * self.risk_params.max_position_size / 100):
            errors.append("❌ حجم العقد يتجاوز الحد الأقصى")
        
        # 4. تحقق من المخاطر
        if setup.risk_amount > (self.risk_params.account_size * self.risk_params.risk_percentage / 100):
            errors.append("❌ المخاطرة تتجاوز النسبة المسموحة")
        
        is_valid = len(errors) == 0
        message = "✅ الإعداد صحيح" if is_valid else "\\n".join(errors)\n        \n        return is_valid, message\n    \n    def get_setup_summary(self, setup: TradeSetup) -> str:\n        \"\"\"\n        ملخص الإعداد بصيغة نصية\n        \"\"\"\n        summary = f\"\"\"\n        💰 إعداد التجارة:\n        ══════════════════════════════════\n        النوع: {setup.signal_type} 🔷\n        \n        الأسعار:\n        • Entry:     {setup.entry_price:.2f} 📍\n        • Stop Loss: {setup.stop_loss:.2f} 🛑\n        • Take Prof: {setup.take_profit:.2f} 🎯\n        \n        حجم العقد:\n        • العملات: {setup.position_size:.4f}\n        • الدولار: ${setup.position_size_usd:.2f}\n        \n        المخاطر والفوائد:\n        • المخاطر: ${setup.risk_amount:.2f}\n        • الفائدة المتوقعة: ${setup.profit_amount:.2f}\n        • نسبة R:R: 1:{setup.risk_reward_ratio:.2f}\n        \n        الثقة: {setup.confidence * 100:.0f}%\n        \"\"\"\n        \n        return summary\n    \n    def adjust_position_size(\n        self,\n        setup: TradeSetup,\n        new_risk_percentage: float = None,\n        new_account_size: float = None\n    ) -> TradeSetup:\n        \"\"\"\n        تعديل حجم العقد بناءً على معاملات جديدة\n        \"\"\"\n        if new_account_size:\n            self.risk_params.account_size = new_account_size\n        \n        if new_risk_percentage:\n            self.risk_params.risk_percentage = new_risk_percentage\n        \n        # أعد الحساب\n        return self.calculate_trade_setup(\n            entry_price=setup.entry_price,\n            stop_loss=setup.stop_loss,\n            take_profit=setup.take_profit,\n            current_price=setup.candle_price,\n            signal_type=setup.signal_type,\n            confidence=setup.confidence\n        )\n    \n    def get_position_metrics(self, setup: TradeSetup) -> Dict:\n        \"\"\"\n        مقاييس الموضع (Position)\n        \"\"\"\n        return {\n            'entry_price': setup.entry_price,\n            'stop_loss': setup.stop_loss,\n            'take_profit': setup.take_profit,\n            'position_size': setup.position_size,\n            'position_size_usd': setup.position_size_usd,\n            'risk': setup.risk_amount,\n            'potential_reward': setup.profit_amount,\n            'rr_ratio': setup.risk_reward_ratio,\n            'account_risk_pct': (setup.risk_amount / self.risk_params.account_size) * 100,\n            'signal_type': setup.signal_type,\n            'confidence': setup.confidence\n        }\n"