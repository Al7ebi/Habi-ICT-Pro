import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import logging
import sys
from pathlib import Path

# إضافة المجلدات للـ path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    APP_NAME, VERSION, POPULAR_SYMBOLS, SUPPORTED_TIMEFRAMES,
    UIColors, RiskConfig
)
from core.data_fetcher import get_data_fetcher, Candle
from core.ict_logic import ICTLogic, Direction
from agents.director import DirectorAgent
from agents.quant_ict import QuantICTAgent
from agents.risk_manager import RiskManagerAgent, RiskParameters

# بقية الكود الذي معك... (تأكد من لصقه كاملاً بدون علامات الاقتباس الخارجية)
