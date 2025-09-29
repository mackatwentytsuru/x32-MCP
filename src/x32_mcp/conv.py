"""
X32のdB値とlevel型(0.0..1.0)の相互変換

注意: X32のlevel型は実際には4つの異なるレンジを持つ非線形マッピングだが、
ここでは簡易的に線形近似を使用。将来的に厳密な変換に置き換え可能。

参考範囲:
- dB: -90.0 (最小) 〜 +10.0 (最大)
- level: 0.0 (最小) 〜 1.0 (最大)
"""

DB_MIN = -90.0
DB_MAX = 10.0
LEVEL_MIN = 0.0
LEVEL_MAX = 1.0


def db_to_level(db: float) -> float:
    """
    dB値をX32のlevel型(0.0..1.0)に変換

    Args:
        db: デシベル値（-90.0 〜 +10.0）

    Returns:
        level型の値（0.0 〜 1.0）

    Note:
        現在は線形近似。X32の厳密な4レンジ変換は後日実装可能。
    """
    # 範囲チェック
    db = max(DB_MIN, min(DB_MAX, db))

    # 線形スケーリング
    db_range = DB_MAX - DB_MIN
    normalized = (db - DB_MIN) / db_range
    level = LEVEL_MIN + normalized * (LEVEL_MAX - LEVEL_MIN)

    return max(LEVEL_MIN, min(LEVEL_MAX, level))


def level_to_db(level: float) -> float:
    """
    X32のlevel型(0.0..1.0)をdB値に変換

    Args:
        level: level型の値（0.0 〜 1.0）

    Returns:
        デシベル値（-90.0 〜 +10.0）

    Note:
        現在は線形近似。X32の厳密な4レンジ変換は後日実装可能。
    """
    # 範囲チェック
    level = max(LEVEL_MIN, min(LEVEL_MAX, level))

    # 線形スケーリング
    level_range = LEVEL_MAX - LEVEL_MIN
    normalized = (level - LEVEL_MIN) / level_range
    db = DB_MIN + normalized * (DB_MAX - DB_MIN)

    return max(DB_MIN, min(DB_MAX, db))