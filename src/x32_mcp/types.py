"""
X32型定義・Enum・変換関数

X32で使用される各種データ型の変換とEnum定義を提供します。
"""

from enum import Enum
import math


# ========================================
# Color定義
# ========================================

class ChannelColor(Enum):
    """チャンネル色定義"""
    OFF = ("OFF", 0)
    BLACK = ("BK", 1)
    RED = ("RD", 2)
    GREEN = ("GN", 3)
    YELLOW = ("YE", 4)
    BLUE = ("BL", 5)
    MAGENTA = ("MG", 6)
    CYAN = ("CY", 7)
    WHITE = ("WH", 8)

    def __init__(self, code: str, index: int):
        self.code = code
        self.index = index


def color_to_code(color: str) -> str:
    """
    色名を2文字コードに変換

    Args:
        color: "RED", "GREEN", "YELLOW" など

    Returns:
        2文字コード ("RD", "GN", "YE" など)
    """
    color_upper = color.upper()
    for c in ChannelColor:
        if c.name == color_upper or c.code == color_upper:
            return c.code

    valid = ", ".join([c.name for c in ChannelColor])
    raise ValueError(f"無効な色 '{color}'。有効な値: {valid}")


def code_to_color(code: str) -> str:
    """
    2文字コードを色名に変換

    Args:
        code: "RD", "GN" など

    Returns:
        色名 ("RED", "GREEN" など)
    """
    code_upper = code.upper()
    for c in ChannelColor:
        if c.code == code_upper:
            return c.name

    raise ValueError(f"無効な色コード '{code}'")


# ========================================
# 周波数変換（20Hz - 20kHz）
# ========================================

FREQ_MIN = 20.0      # Hz
FREQ_MAX = 20000.0   # Hz
FREQ_STEPS = 201     # ステップ数

def freq_to_value(freq_hz: float) -> float:
    """
    周波数（Hz）をX32のvalue型（0.0-1.0）に変換

    Args:
        freq_hz: 周波数（20.0 - 20000.0 Hz）

    Returns:
        value型の値（0.0 - 1.0）

    Note:
        X32は対数スケール（201ステップ）を使用
    """
    freq_hz = max(FREQ_MIN, min(FREQ_MAX, freq_hz))

    # 対数スケール変換
    log_min = math.log(FREQ_MIN)
    log_max = math.log(FREQ_MAX)
    log_freq = math.log(freq_hz)

    normalized = (log_freq - log_min) / (log_max - log_min)
    return max(0.0, min(1.0, normalized))


def value_to_freq(value: float) -> float:
    """
    X32のvalue型（0.0-1.0）を周波数（Hz）に変換

    Args:
        value: value型の値（0.0 - 1.0）

    Returns:
        周波数（Hz）
    """
    value = max(0.0, min(1.0, value))

    # 対数スケール逆変換
    log_min = math.log(FREQ_MIN)
    log_max = math.log(FREQ_MAX)
    log_freq = log_min + value * (log_max - log_min)

    freq = math.exp(log_freq)
    return max(FREQ_MIN, min(FREQ_MAX, freq))


# ========================================
# Q値変換（バンド幅）
# ========================================

Q_MIN = 0.3
Q_MAX = 10.0

def q_to_value(q: float) -> float:
    """
    Q値をX32のvalue型（0.0-1.0）に変換

    Args:
        q: Q値（0.3 - 10.0）

    Returns:
        value型の値（0.0 - 1.0）

    Note:
        Q値は対数スケールで変換
    """
    q = max(Q_MIN, min(Q_MAX, q))

    # 対数スケール
    log_min = math.log(Q_MIN)
    log_max = math.log(Q_MAX)
    log_q = math.log(q)

    normalized = (log_q - log_min) / (log_max - log_min)
    return max(0.0, min(1.0, normalized))


def value_to_q(value: float) -> float:
    """
    X32のvalue型（0.0-1.0）をQ値に変換

    Args:
        value: value型の値（0.0 - 1.0）

    Returns:
        Q値（0.3 - 10.0）
    """
    value = max(0.0, min(1.0, value))

    # 対数スケール逆変換
    log_min = math.log(Q_MIN)
    log_max = math.log(Q_MAX)
    log_q = log_min + value * (log_max - log_min)

    q = math.exp(log_q)
    return max(Q_MIN, min(Q_MAX, q))


# ========================================
# 時間変換（ms）
# ========================================

TIME_MIN = 0.0    # ms
TIME_MAX = 4000.0  # ms

def time_to_value(time_ms: float, time_max: float = TIME_MAX) -> float:
    """
    時間（ms）をX32のvalue型（0.0-1.0）に変換

    Args:
        time_ms: 時間（ミリ秒）
        time_max: 最大時間（デフォルト4000ms）

    Returns:
        value型の値（0.0 - 1.0）

    Note:
        パラメータによって最大値が異なる場合があります
    """
    time_ms = max(TIME_MIN, min(time_max, time_ms))
    return time_ms / time_max


def value_to_time(value: float, time_max: float = TIME_MAX) -> float:
    """
    X32のvalue型（0.0-1.0）を時間（ms）に変換

    Args:
        value: value型の値（0.0 - 1.0）
        time_max: 最大時間（デフォルト4000ms）

    Returns:
        時間（ミリ秒）
    """
    value = max(0.0, min(1.0, value))
    return value * time_max


# ========================================
# パーセンテージ変換
# ========================================

def percent_to_value(percent: float) -> float:
    """
    パーセント（0-100）をvalue型（0.0-1.0）に変換

    Args:
        percent: パーセント（0 - 100）

    Returns:
        value型の値（0.0 - 1.0）
    """
    percent = max(0.0, min(100.0, percent))
    return percent / 100.0


def value_to_percent(value: float) -> float:
    """
    value型（0.0-1.0）をパーセント（0-100）に変換

    Args:
        value: value型の値（0.0 - 1.0）

    Returns:
        パーセント（0 - 100）
    """
    value = max(0.0, min(1.0, value))
    return value * 100.0


# ========================================
# ゲイン変換（dB）
# ========================================

def gain_db_to_value(gain_db: float, gain_min: float = -18.0, gain_max: float = 18.0) -> float:
    """
    ゲイン（dB）をvalue型（0.0-1.0）に変換

    Args:
        gain_db: ゲイン（dB）
        gain_min: 最小ゲイン（デフォルト-18dB）
        gain_max: 最大ゲイン（デフォルト+18dB）

    Returns:
        value型の値（0.0 - 1.0）
    """
    gain_db = max(gain_min, min(gain_max, gain_db))
    normalized = (gain_db - gain_min) / (gain_max - gain_min)
    return max(0.0, min(1.0, normalized))


def value_to_gain_db(value: float, gain_min: float = -18.0, gain_max: float = 18.0) -> float:
    """
    value型（0.0-1.0）をゲイン（dB）に変換

    Args:
        value: value型の値（0.0 - 1.0）
        gain_min: 最小ゲイン（デフォルト-18dB）
        gain_max: 最大ゲイン（デフォルト+18dB）

    Returns:
        ゲイン（dB）
    """
    value = max(0.0, min(1.0, value))
    gain_db = gain_min + value * (gain_max - gain_min)
    return max(gain_min, min(gain_max, gain_db))


# ========================================
# Pan（パン）変換
# ========================================

def pan_to_value(pan: float) -> float:
    """
    パン位置をX32のvalue型（0.0-1.0）に変換

    Args:
        pan: パン位置（-100=左, 0=中央, +100=右）

    Returns:
        value型の値（0.0=左, 0.5=中央, 1.0=右）
    """
    pan = max(-100.0, min(100.0, pan))
    return (pan + 100.0) / 200.0


def value_to_pan(value: float) -> float:
    """
    X32のvalue型（0.0-1.0）をパン位置に変換

    Args:
        value: value型の値（0.0=左, 0.5=中央, 1.0=右）

    Returns:
        パン位置（-100=左, 0=中央, +100=右）
    """
    value = max(0.0, min(1.0, value))
    return value * 200.0 - 100.0