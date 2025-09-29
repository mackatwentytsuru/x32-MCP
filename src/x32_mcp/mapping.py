"""
X32出力ルーティングソースの文字列⇄整数マッピング

X32の /outputs/main/{01..16}/src は int型 0..76 を受け付ける。
最低限のマッピングを実装し、将来拡張可能な構造とする。
"""

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
    # TODO: DirectOutCh01..32 (26..57), AuxIn1..8 (58..65), etc.
}

# 整数コード → 文字列（逆引き）
CODE_TO_OUTPUT_SRC: dict[int, str] = {v: k for k, v in OUTPUT_SRC_TO_CODE.items()}


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