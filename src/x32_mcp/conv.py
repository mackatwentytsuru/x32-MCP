"""
X32のdB値とlevel型(0.0..1.0)の相互変換

X32の実測データに基づく区分線形補間を使用。

実測データポイント:
- -90dB = 0.000000
- -40dB = 0.187683
- -30dB = 0.250244
- -20dB = 0.375367
- -10dB = 0.499511
- 0dB = 0.748778
- +5dB = 0.874878
- +10dB = 0.999022
"""

# 実測データテーブル (dB, level)
_FADER_TABLE = [
    (-90.0, 0.000000),
    (-40.0, 0.187683),
    (-30.0, 0.250244),
    (-20.0, 0.375367),
    (-10.0, 0.499511),
    (0.0, 0.748778),
    (5.0, 0.874878),
    (10.0, 0.999022),
]

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
        実測データに基づく区分線形補間を使用。
    """
    # 範囲チェック
    db = max(DB_MIN, min(DB_MAX, db))

    # 区分線形補間
    for i in range(len(_FADER_TABLE) - 1):
        db1, level1 = _FADER_TABLE[i]
        db2, level2 = _FADER_TABLE[i + 1]

        if db1 <= db <= db2:
            # 線形補間
            t = (db - db1) / (db2 - db1)
            level = level1 + t * (level2 - level1)
            return level

    # 範囲外（通常は到達しない）
    return LEVEL_MIN if db < DB_MIN else LEVEL_MAX


def level_to_db(level: float) -> float:
    """
    X32のlevel型(0.0..1.0)をdB値に変換

    Args:
        level: level型の値（0.0 〜 1.0）

    Returns:
        デシベル値（-90.0 〜 +10.0）

    Note:
        実測データに基づく区分線形補間を使用。
    """
    # 範囲チェック
    level = max(LEVEL_MIN, min(LEVEL_MAX, level))

    # 区分線形補間
    for i in range(len(_FADER_TABLE) - 1):
        db1, level1 = _FADER_TABLE[i]
        db2, level2 = _FADER_TABLE[i + 1]

        if level1 <= level <= level2:
            # 線形補間
            t = (level - level1) / (level2 - level1)
            db = db1 + t * (db2 - db1)
            return db

    # 範囲外（通常は到達しない）
    return DB_MIN if level < LEVEL_MIN else DB_MAX