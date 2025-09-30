"""
X32出力ルーティングソース・アイコンの文字列⇄整数マッピング

X32の /outputs/main/{01..16}/src は int型 0..76 を受け付ける。
アイコン、色などのマッピングも含む。
"""

# ========================================
# 出力ルーティングソース
# ========================================

# 文字列 → 整数コード
OUTPUT_SRC_TO_CODE: dict[str, int] = {
    "OFF": 0,
    "MainL": 1,
    "MainR": 2,
    "MC": 3,  # Mono/Center
    # MixBus 1..16
    "Bus1": 4, "Bus2": 5, "Bus3": 6, "Bus4": 7,
    "Bus5": 8, "Bus6": 9, "Bus7": 10, "Bus8": 11,
    "Bus9": 12, "Bus10": 13, "Bus11": 14, "Bus12": 15,
    "Bus13": 16, "Bus14": 17, "Bus15": 18, "Bus16": 19,
    # Matrix 1..6
    "Matrix1": 20, "Matrix2": 21, "Matrix3": 22,
    "Matrix4": 23, "Matrix5": 24, "Matrix6": 25,
    # DirectOut Ch01..32 (26..57)
    **{f"DirectOutCh{i:02d}": 26 + i - 1 for i in range(1, 33)},
    # AuxIn 1..8 (58..65)
    "AuxIn1": 58, "AuxIn2": 59, "AuxIn3": 60, "AuxIn4": 61,
    "AuxIn5": 62, "AuxIn6": 63, "AuxIn7": 64, "AuxIn8": 65,
    # FX 1L-4R (66..73)
    "FX1L": 66, "FX1R": 67, "FX2L": 68, "FX2R": 69,
    "FX3L": 70, "FX3R": 71, "FX4L": 72, "FX4R": 73,
    # Aux 1..6 (74..79) - 追加の補助出力
    "Aux1": 74, "Aux2": 75, "Aux3": 76, "Aux4": 77,
    "Aux5": 78, "Aux6": 79,
}

# 整数コード → 文字列（逆引き）
CODE_TO_OUTPUT_SRC: dict[int, str] = {v: k for k, v in OUTPUT_SRC_TO_CODE.items()}


# ========================================
# チャンネルアイコン（74種類）
# ========================================

ICON_NAMES = [
    "None", "Mic", "Line", "Headphone", "Speaker", "Guitar", "Bass", "Piano",
    "Keyboard", "Drums", "Percussion", "Trumpet", "Saxophone", "Violin", "Cello",
    "Acoustic", "Electric", "Vocal", "Choir", "Strings", "Brass", "Woodwind",
    "Orchestra", "DJ", "CD", "Tape", "USB", "Computer", "Phone", "Radio",
    "Video", "Camera", "Projector", "TV", "Screen", "Light", "Effect",
    "Monitor", "Aux", "Bus", "Matrix", "FX", "Compressor", "Gate", "EQ",
    "Filter", "Reverb", "Delay", "Chorus", "Flanger", "Phaser", "Distortion",
    "Gain", "Fader", "Pan", "Mute", "Solo", "Record", "Play", "Stop",
    "Pause", "Forward", "Rewind", "Eject", "Loop", "Metronome", "Tuner",
    "Clock", "User1", "User2", "User3", "User4", "User5", "User6"
]

def icon_name_to_index(icon: str) -> int:
    """
    アイコン名をインデックスに変換

    Args:
        icon: アイコン名（"Mic", "Guitar" など）

    Returns:
        アイコンインデックス（0-73）
    """
    icon_title = icon.title()  # 大文字小文字を正規化
    try:
        return ICON_NAMES.index(icon_title)
    except ValueError:
        valid = ", ".join(ICON_NAMES[:20]) + "..."
        raise ValueError(f"無効なアイコン名 '{icon}'。有効な値: {valid}")


def index_to_icon_name(index: int) -> str:
    """
    インデックスをアイコン名に変換

    Args:
        index: アイコンインデックス（0-73）

    Returns:
        アイコン名
    """
    if 0 <= index < len(ICON_NAMES):
        return ICON_NAMES[index]
    raise ValueError(f"無効なアイコンインデックス {index}（0-{len(ICON_NAMES)-1}の範囲）")


def source_to_code(source: str) -> int:
    """
    出力ソース文字列を整数コードに変換

    Args:
        source: "MainL", "Bus5", "Matrix2" など

    Returns:
        X32の /outputs/main/{nn}/src に送信する整数値

    Raises:
        ValueError: 未定義のソース文字列
    """
    if source not in OUTPUT_SRC_TO_CODE:
        valid = ", ".join(sorted(OUTPUT_SRC_TO_CODE.keys()))
        raise ValueError(
            f"無効な出力ソース '{source}'。有効な値: {valid}"
        )
    return OUTPUT_SRC_TO_CODE[source]


def code_to_source(code: int) -> str:
    """
    整数コードを出力ソース文字列に変換

    Args:
        code: X32から取得した整数値

    Returns:
        "MainL", "Bus5" などの文字列

    Raises:
        ValueError: 未定義のコード
    """
    if code not in CODE_TO_OUTPUT_SRC:
        raise ValueError(
            f"未定義の出力ソースコード {code}。マッピングテーブルを拡張してください。"
        )
    return CODE_TO_OUTPUT_SRC[code]