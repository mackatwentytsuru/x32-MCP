"""
X32 MCP Server - FastMCP実装

ツール（操作）とリソース（取得）を提供し、
STDIO/Streamable HTTPの両方で起動可能。
"""

import logging
import sys
from typing import Literal

import typer
from mcp.server.fastmcp import FastMCP

from .osc_client import X32Client, X32Error
from .conv import db_to_level, level_to_db
from .mapping import source_to_code, code_to_source, icon_name_to_index, index_to_icon_name
from .types import (
    color_to_code, code_to_color,
    pan_to_value, value_to_pan,
    gain_db_to_value, value_to_gain_db,
    freq_to_value, value_to_freq,
    q_to_value, value_to_q
)
from .config import X32_IP, X32_PORT

# STDIOモード時はstdoutへのログ出力を防ぐ
# すべてのログはstderrに出力
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr  # 重要: stdoutではなくstderrに出力
)
logger = logging.getLogger(__name__)

# FastMCPインスタンス
mcp = FastMCP("x32-mcp")

# グローバルX32クライアント
_client: X32Client | None = None


def get_client() -> X32Client:
    """
    X32クライアントのシングルトンインスタンスを取得
    初回呼び出し時にkeepaliveを開始
    """
    global _client
    if _client is None:
        _client = X32Client(host=X32_IP, port=X32_PORT)
        _client.start_xremote_keepalive()
        logger.info("X32Client initialized and keepalive started")
    return _client


# ========================================
# Tools（操作系）
# ========================================

@mcp.tool()
def set_fader(channel: int, volume_db: float) -> str:
    """
    チャンネルフェーダーレベルを設定

    Args:
        channel: チャンネル番号（1〜32）
        volume_db: フェーダーレベル（-90.0 〜 +10.0 dB）

    Returns:
        成功メッセージまたはエラー

    Note:
        X32のフェーダーは level型（0.0〜1.0）で管理されます。
        dB値は内部で自動変換されます。
    """
    if not (1 <= channel <= 32):
        return f"エラー: チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）"

    if not (-90.0 <= volume_db <= 10.0):
        return f"エラー: フェーダーレベルは-90.0〜+10.0 dBの範囲で指定してください（指定値: {volume_db}）"

    try:
        client = get_client()
        level = db_to_level(volume_db)
        address = f"/ch/{channel:02d}/mix/fader"
        client.send(address, level)
        return f"✓ チャンネル{channel}のフェーダーを{volume_db:.1f} dBに設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_fader内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_mute(channel: int, mute: bool) -> str:
    """
    チャンネルミュート状態を設定

    Args:
        channel: チャンネル番号（1〜32）
        mute: True=ミュート、False=アンミュート

    Returns:
        成功メッセージまたはエラー

    Note:
        **重要**: X32では /ch/{cc}/mix/on = 1 がアンミュート、0 がミュートです。
        この関数は引数を直感的な True=ミュート に統一しています。
    """
    if not (1 <= channel <= 32):
        return f"エラー: チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）"

    try:
        client = get_client()
        # X32: 1=ON(アンミュート)、0=OFF(ミュート)
        # 引数: True=ミュート、False=アンミュート
        value = 0 if mute else 1
        address = f"/ch/{channel:02d}/mix/on"
        client.send(address, value)
        state = "ミュート" if mute else "アンミュート"
        return f"✓ チャンネル{channel}を{state}に設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_mute内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_bus_send(channel: int, bus: int, level_db: float) -> str:
    """
    チャンネルからバスへの送りレベルを設定

    Args:
        channel: チャンネル番号（1〜32）
        bus: バス番号（1〜16）
        level_db: 送りレベル（-90.0 〜 +10.0 dB）

    Returns:
        成功メッセージまたはエラー

    Note:
        MixBus（Aux Send）への送りレベルを制御します。
    """
    if not (1 <= channel <= 32):
        return f"エラー: チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）"

    if not (1 <= bus <= 16):
        return f"エラー: バス番号は1〜16の範囲で指定してください（指定値: {bus}）"

    if not (-90.0 <= level_db <= 10.0):
        return f"エラー: 送りレベルは-90.0〜+10.0 dBの範囲で指定してください（指定値: {level_db}）"

    try:
        client = get_client()
        level = db_to_level(level_db)
        address = f"/ch/{channel:02d}/mix/{bus:02d}/level"
        client.send(address, level)
        return f"✓ チャンネル{channel}からバス{bus}への送りを{level_db:.1f} dBに設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_bus_send内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def route_output(output_idx: int, source: str) -> str:
    """
    メイン出力のルーティングソースを設定

    Args:
        output_idx: 出力番号（1〜16）
        source: ルーティングソース（例: "MainL", "MainR", "MC", "Bus5", "Matrix2", "OFF"）

    Returns:
        成功メッセージまたはエラー

    Note:
        X32の /outputs/main/{01..16}/src に整数コード（0..76）を送信します。
        有効なソース文字列については mapping.py を参照してください。
    """
    if not (1 <= output_idx <= 16):
        return f"エラー: 出力番号は1〜16の範囲で指定してください（指定値: {output_idx}）"

    try:
        code = source_to_code(source)
    except ValueError as e:
        return f"エラー: {e}"

    try:
        client = get_client()
        address = f"/outputs/main/{output_idx:02d}/src"
        client.send(address, code)
        return f"✓ 出力{output_idx}のソースを'{source}'に設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("route_output内部エラー")
        return f"予期しないエラー: {e}"


# ========================================
# Phase 1: チャンネル拡張ツール
# ========================================

@mcp.tool()
def set_channel_name(channel: int, name: str) -> str:
    """
    チャンネル名を設定

    Args:
        channel: チャンネル番号（1〜32）
        name: チャンネル名（最大12文字）

    Returns:
        成功メッセージまたはエラー
    """
    if not (1 <= channel <= 32):
        return f"エラー: チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）"

    if len(name) > 12:
        name = name[:12]
        logger.warning(f"チャンネル名を12文字に切り詰めました: '{name}'")

    try:
        client = get_client()
        address = f"/ch/{channel:02d}/config/name"
        client.send(address, name)
        return f"✓ チャンネル{channel}の名前を'{name}'に設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_channel_name内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_channel_color(channel: int, color: str) -> str:
    """
    チャンネルの色を設定

    Args:
        channel: チャンネル番号（1〜32）
        color: 色名（"RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE", "BLACK", "OFF"）

    Returns:
        成功メッセージまたはエラー
    """
    if not (1 <= channel <= 32):
        return f"エラー: チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）"

    try:
        color_code = color_to_code(color)
    except ValueError as e:
        return f"エラー: {e}"

    try:
        client = get_client()
        address = f"/ch/{channel:02d}/config/color"
        client.send(address, color_code)
        return f"✓ チャンネル{channel}の色を{color.upper()}に設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_channel_color内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_channel_icon(channel: int, icon: str) -> str:
    """
    チャンネルアイコンを設定

    Args:
        channel: チャンネル番号（1〜32）
        icon: アイコン名（"Mic", "Guitar", "Piano", "Vocal" など）

    Returns:
        成功メッセージまたはエラー
    """
    if not (1 <= channel <= 32):
        return f"エラー: チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）"

    try:
        icon_index = icon_name_to_index(icon)
    except ValueError as e:
        return f"エラー: {e}"

    try:
        client = get_client()
        address = f"/ch/{channel:02d}/config/icon"
        client.send(address, icon_index)
        return f"✓ チャンネル{channel}のアイコンを{icon}に設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_channel_icon内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_pan(channel: int, pan: float) -> str:
    """
    チャンネルのパン（左右バランス）を設定

    Args:
        channel: チャンネル番号（1〜32）
        pan: パン位置（-100=左, 0=中央, +100=右）

    Returns:
        成功メッセージまたはエラー
    """
    if not (1 <= channel <= 32):
        return f"エラー: チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）"

    if not (-100.0 <= pan <= 100.0):
        return f"エラー: パン位置は-100〜+100の範囲で指定してください（指定値: {pan}）"

    try:
        client = get_client()
        pan_value = pan_to_value(pan)
        address = f"/ch/{channel:02d}/mix/pan"
        client.send(address, pan_value)

        # パン位置の説明
        if pan < -30:
            pos_desc = "左寄り"
        elif pan > 30:
            pos_desc = "右寄り"
        else:
            pos_desc = "中央"

        return f"✓ チャンネル{channel}のパンを{pan:+.0f}（{pos_desc}）に設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_pan内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_gain(channel: int, gain_db: float) -> str:
    """
    チャンネルのプリアンプゲインを設定

    Args:
        channel: チャンネル番号（1〜32）
        gain_db: ゲイン（0.0 〜 +60.0 dB、-12.0dBも可能）

    Returns:
        成功メッセージまたはエラー
    """
    if not (1 <= channel <= 32):
        return f"エラー: チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）"

    if not (-12.0 <= gain_db <= 60.0):
        return f"エラー: ゲインは-12.0〜+60.0 dBの範囲で指定してください（指定値: {gain_db}）"

    try:
        client = get_client()
        gain_value = gain_db_to_value(gain_db, gain_min=-12.0, gain_max=60.0)
        address = f"/ch/{channel:02d}/preamp/gain"
        client.send(address, gain_value)
        return f"✓ チャンネル{channel}のゲインを{gain_db:+.1f} dBに設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_gain内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_phantom_power(channel: int, enabled: bool) -> str:
    """
    チャンネルのファンタム電源（+48V）を設定

    Args:
        channel: チャンネル番号（1〜32）
        enabled: True=ON、False=OFF

    Returns:
        成功メッセージまたはエラー

    Warning:
        ファンタム電源をONにする前に、接続機器が対応していることを確認してください。
        非対応機器に供給すると故障の原因になります。
    """
    if not (1 <= channel <= 32):
        return f"エラー: チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）"

    try:
        client = get_client()
        value = 1 if enabled else 0
        address = f"/ch/{channel:02d}/preamp/phantom"
        client.send(address, value)

        state = "ON" if enabled else "OFF"
        warning = " ⚠️ 接続機器が対応していることを確認してください" if enabled else ""
        return f"✓ チャンネル{channel}のファンタム電源を{state}にしました{warning}"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_phantom_power内部エラー")
        return f"予期しないエラー: {e}"


# ========================================
# Phase 2: EQ制御ツール
# ========================================

@mcp.tool()
def set_eq_enabled(channel: int, enabled: bool) -> str:
    """
    チャンネルEQのON/OFFを設定

    Args:
        channel: チャンネル番号（1〜32）
        enabled: True=ON、False=OFF

    Returns:
        成功メッセージまたはエラー
    """
    if not (1 <= channel <= 32):
        return f"エラー: チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）"

    try:
        client = get_client()
        value = 1 if enabled else 0
        address = f"/ch/{channel:02d}/eq/on"
        client.send(address, value)

        state = "ON" if enabled else "OFF"
        return f"✓ チャンネル{channel}のEQを{state}にしました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_eq_enabled内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_eq_band(channel: int, band: int, freq_hz: float, gain_db: float, q: float) -> str:
    """
    チャンネルEQのバンド設定

    Args:
        channel: チャンネル番号（1〜32）
        band: バンド番号（1〜4）
        freq_hz: 中心周波数（20〜20000 Hz）
        gain_db: ゲイン（-15.0〜+15.0 dB）
        q: Q値/バンド幅（0.3〜10.0）

    Returns:
        成功メッセージまたはエラー

    Note:
        X32は4バンドパラメトリックEQを搭載しています。
    """
    if not (1 <= channel <= 32):
        return f"エラー: チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）"

    if not (1 <= band <= 4):
        return f"エラー: バンド番号は1〜4の範囲で指定してください（指定値: {band}）"

    if not (20.0 <= freq_hz <= 20000.0):
        return f"エラー: 周波数は20〜20000 Hzの範囲で指定してください（指定値: {freq_hz}）"

    if not (-15.0 <= gain_db <= 15.0):
        return f"エラー: ゲインは-15.0〜+15.0 dBの範囲で指定してください（指定値: {gain_db}）"

    if not (0.3 <= q <= 10.0):
        return f"エラー: Q値は0.3〜10.0の範囲で指定してください（指定値: {q}）"

    try:
        client = get_client()

        # 周波数設定
        freq_value = freq_to_value(freq_hz)
        client.send(f"/ch/{channel:02d}/eq/{band}/f", freq_value)

        # ゲイン設定
        gain_value = gain_db_to_value(gain_db, gain_min=-15.0, gain_max=15.0)
        client.send(f"/ch/{channel:02d}/eq/{band}/g", gain_value)

        # Q値設定
        q_value = q_to_value(q)
        client.send(f"/ch/{channel:02d}/eq/{band}/q", q_value)

        return f"✓ チャンネル{channel} EQバンド{band}を設定しました（{freq_hz:.0f}Hz, {gain_db:+.1f}dB, Q={q:.1f}）"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_eq_band内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def reset_eq(channel: int) -> str:
    """
    チャンネルEQをフラット（全ゲイン0dB）にリセット

    Args:
        channel: チャンネル番号（1〜32）

    Returns:
        成功メッセージまたはエラー
    """
    if not (1 <= channel <= 32):
        return f"エラー: チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）"

    try:
        client = get_client()
        # 全バンドのゲインを0dBに設定
        zero_gain = gain_db_to_value(0.0, gain_min=-15.0, gain_max=15.0)

        for band in range(1, 5):
            address = f"/ch/{channel:02d}/eq/{band}/g"
            client.send(address, zero_gain)

        return f"✓ チャンネル{channel}のEQをリセットしました（全バンドゲイン0dB）"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("reset_eq内部エラー")
        return f"予期しないエラー: {e}"


# ========================================
# Phase 4: Bus・Matrix・Main LRツール
# ========================================

@mcp.tool()
def set_bus_fader(bus: int, level_db: float) -> str:
    """
    バスフェーダーレベルを設定

    Args:
        bus: バス番号（1〜16）
        level_db: フェーダーレベル（-90.0 〜 +10.0 dB）

    Returns:
        成功メッセージまたはエラー
    """
    if not (1 <= bus <= 16):
        return f"エラー: バス番号は1〜16の範囲で指定してください（指定値: {bus}）"

    if not (-90.0 <= level_db <= 10.0):
        return f"エラー: フェーダーレベルは-90.0〜+10.0 dBの範囲で指定してください（指定値: {level_db}）"

    try:
        client = get_client()
        level = db_to_level(level_db)
        address = f"/bus/{bus:02d}/mix/fader"
        client.send(address, level)
        return f"✓ バス{bus}のフェーダーを{level_db:.1f} dBに設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_bus_fader内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_bus_mute(bus: int, mute: bool) -> str:
    """
    バスミュート状態を設定

    Args:
        bus: バス番号（1〜16）
        mute: True=ミュート、False=アンミュート

    Returns:
        成功メッセージまたはエラー
    """
    if not (1 <= bus <= 16):
        return f"エラー: バス番号は1〜16の範囲で指定してください（指定値: {bus}）"

    try:
        client = get_client()
        value = 0 if mute else 1
        address = f"/bus/{bus:02d}/mix/on"
        client.send(address, value)
        state = "ミュート" if mute else "アンミュート"
        return f"✓ バス{bus}を{state}に設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_bus_mute内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_matrix_fader(matrix: int, level_db: float) -> str:
    """
    Matrixフェーダーレベルを設定

    Args:
        matrix: Matrix番号（1〜6）
        level_db: フェーダーレベル（-90.0 〜 +10.0 dB）

    Returns:
        成功メッセージまたはエラー
    """
    if not (1 <= matrix <= 6):
        return f"エラー: Matrix番号は1〜6の範囲で指定してください（指定値: {matrix}）"

    if not (-90.0 <= level_db <= 10.0):
        return f"エラー: フェーダーレベルは-90.0〜+10.0 dBの範囲で指定してください（指定値: {level_db}）"

    try:
        client = get_client()
        level = db_to_level(level_db)
        address = f"/mtx/{matrix:02d}/mix/fader"
        client.send(address, level)
        return f"✓ Matrix{matrix}のフェーダーを{level_db:.1f} dBに設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_matrix_fader内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_matrix_mute(matrix: int, mute: bool) -> str:
    """
    Matrixミュート状態を設定

    Args:
        matrix: Matrix番号（1〜6）
        mute: True=ミュート、False=アンミュート

    Returns:
        成功メッセージまたはエラー
    """
    if not (1 <= matrix <= 6):
        return f"エラー: Matrix番号は1〜6の範囲で指定してください（指定値: {matrix}）"

    try:
        client = get_client()
        value = 0 if mute else 1
        address = f"/mtx/{matrix:02d}/mix/on"
        client.send(address, value)
        state = "ミュート" if mute else "アンミュート"
        return f"✓ Matrix{matrix}を{state}に設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_matrix_mute内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_auxin_fader(auxin: int, level_db: float) -> str:
    """
    AuxIn（外部入力）フェーダーレベルを設定

    Args:
        auxin: AuxIn番号（1〜8）
        level_db: フェーダーレベル（-90.0 〜 +10.0 dB）

    Returns:
        成功メッセージまたはエラー
    """
    if not (1 <= auxin <= 8):
        return f"エラー: AuxIn番号は1〜8の範囲で指定してください（指定値: {auxin}）"

    if not (-90.0 <= level_db <= 10.0):
        return f"エラー: フェーダーレベルは-90.0〜+10.0 dBの範囲で指定してください（指定値: {level_db}）"

    try:
        client = get_client()
        level = db_to_level(level_db)
        address = f"/auxin/{auxin:02d}/mix/fader"
        client.send(address, level)
        return f"✓ AuxIn{auxin}のフェーダーを{level_db:.1f} dBに設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_auxin_fader内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_auxin_mute(auxin: int, mute: bool) -> str:
    """
    AuxInミュート状態を設定

    Args:
        auxin: AuxIn番号（1〜8）
        mute: True=ミュート、False=アンミュート

    Returns:
        成功メッセージまたはエラー
    """
    if not (1 <= auxin <= 8):
        return f"エラー: AuxIn番号は1〜8の範囲で指定してください（指定値: {auxin}）"

    try:
        client = get_client()
        value = 0 if mute else 1
        address = f"/auxin/{auxin:02d}/mix/on"
        client.send(address, value)
        state = "ミュート" if mute else "アンミュート"
        return f"✓ AuxIn{auxin}を{state}に設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_auxin_mute内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_main_lr_fader(level_db: float) -> str:
    """
    メインLR（ステレオ出力）フェーダーレベルを設定

    Args:
        level_db: フェーダーレベル（-90.0 〜 +10.0 dB）

    Returns:
        成功メッセージまたはエラー
    """
    if not (-90.0 <= level_db <= 10.0):
        return f"エラー: フェーダーレベルは-90.0〜+10.0 dBの範囲で指定してください（指定値: {level_db}）"

    try:
        client = get_client()
        level = db_to_level(level_db)
        address = "/main/st/mix/fader"
        client.send(address, level)
        return f"✓ メインLRフェーダーを{level_db:.1f} dBに設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_main_lr_fader内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_main_lr_mute(mute: bool) -> str:
    """
    メインLR（ステレオ出力）ミュート状態を設定

    Args:
        mute: True=ミュート、False=アンミュート

    Returns:
        成功メッセージまたはエラー
    """
    try:
        client = get_client()
        value = 0 if mute else 1
        address = "/main/st/mix/on"
        client.send(address, value)
        state = "ミュート" if mute else "アンミュート"
        return f"✓ メインLRを{state}に設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_main_lr_mute内部エラー")
        return f"予期しないエラー: {e}"


# ========================================
# Phase 5: DCA・グループツール
# ========================================

@mcp.tool()
def set_dca_fader(dca: int, level_db: float) -> str:
    """
    DCAグループフェーダーレベルを設定

    Args:
        dca: DCA番号（1〜8）
        level_db: フェーダーレベル（-90.0 〜 +10.0 dB）

    Returns:
        成功メッセージまたはエラー

    Note:
        DCAは複数のチャンネルをまとめて制御するためのグループです。
    """
    if not (1 <= dca <= 8):
        return f"エラー: DCA番号は1〜8の範囲で指定してください（指定値: {dca}）"

    if not (-90.0 <= level_db <= 10.0):
        return f"エラー: フェーダーレベルは-90.0〜+10.0 dBの範囲で指定してください（指定値: {level_db}）"

    try:
        client = get_client()
        level = db_to_level(level_db)
        address = f"/dca/{dca}/fader"
        client.send(address, level)
        return f"✓ DCA{dca}のフェーダーを{level_db:.1f} dBに設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_dca_fader内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_dca_mute(dca: int, mute: bool) -> str:
    """
    DCAグループミュート状態を設定

    Args:
        dca: DCA番号（1〜8）
        mute: True=ミュート、False=アンミュート

    Returns:
        成功メッセージまたはエラー
    """
    if not (1 <= dca <= 8):
        return f"エラー: DCA番号は1〜8の範囲で指定してください（指定値: {dca}）"

    try:
        client = get_client()
        value = 0 if mute else 1
        address = f"/dca/{dca}/on"
        client.send(address, value)
        state = "ミュート" if mute else "アンミュート"
        return f"✓ DCA{dca}を{state}に設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_dca_mute内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_dca_name(dca: int, name: str) -> str:
    """
    DCAグループ名を設定

    Args:
        dca: DCA番号（1〜8）
        name: DCA名（最大12文字）

    Returns:
        成功メッセージまたはエラー
    """
    if not (1 <= dca <= 8):
        return f"エラー: DCA番号は1〜8の範囲で指定してください（指定値: {dca}）"

    if len(name) > 12:
        name = name[:12]
        logger.warning(f"DCA名を12文字に切り詰めました: '{name}'")

    try:
        client = get_client()
        address = f"/dca/{dca}/config/name"
        client.send(address, name)
        return f"✓ DCA{dca}の名前を'{name}'に設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_dca_name内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_dca_color(dca: int, color: str) -> str:
    """
    DCAグループの色を設定

    Args:
        dca: DCA番号（1〜8）
        color: 色名（"RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE", "BLACK", "OFF"）

    Returns:
        成功メッセージまたはエラー
    """
    if not (1 <= dca <= 8):
        return f"エラー: DCA番号は1〜8の範囲で指定してください（指定値: {dca}）"

    try:
        color_code = color_to_code(color)
    except ValueError as e:
        return f"エラー: {e}"

    try:
        client = get_client()
        address = f"/dca/{dca}/config/color"
        client.send(address, color_code)
        return f"✓ DCA{dca}の色を{color.upper()}に設定しました"
    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_dca_color内部エラー")
        return f"予期しないエラー: {e}"


# ========================================
# Resources（取得系）
# ========================================

@mcp.resource("x32://channel/{channel}/name")
def get_channel_name(channel: int) -> str:
    """
    チャンネル名を取得

    Args:
        channel: チャンネル番号（1〜32）

    Returns:
        チャンネル名

    Raises:
        X32Error: 通信エラー
    """
    if not (1 <= channel <= 32):
        raise ValueError(f"チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）")

    client = get_client()
    address = f"/ch/{channel:02d}/config/name"
    # X32はstringを返すため、専用の query_string メソッドが必要
    # 現状はqueryではなく、設定値の取得は実装しない
    # （X32のOSCでは設定の取得が全てサポートされているわけではない）
    raise NotImplementedError("X32はチャンネル名の取得をサポートしていません")


@mcp.resource("x32://channel/{channel}/color")
def get_channel_color(channel: int) -> str:
    """
    チャンネルの色を取得

    Args:
        channel: チャンネル番号（1〜32）

    Returns:
        色名

    Raises:
        X32Error: 通信エラー
    """
    if not (1 <= channel <= 32):
        raise ValueError(f"チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）")

    raise NotImplementedError("X32は色設定の取得をサポートしていません")


@mcp.resource("x32://channel/{channel}/pan")
def get_pan(channel: int) -> float:
    """
    チャンネルのパンを取得

    Args:
        channel: チャンネル番号（1〜32）

    Returns:
        パン位置（-100=左, 0=中央, +100=右）

    Raises:
        X32Error: 通信エラー
    """
    if not (1 <= channel <= 32):
        raise ValueError(f"チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）")

    client = get_client()
    address = f"/ch/{channel:02d}/mix/pan"
    value = client.query_float(address)
    pan = value_to_pan(value)
    logger.info(f"get_pan({channel}) -> {pan:+.0f}")
    return pan


@mcp.resource("x32://channel/{channel}/gain")
def get_gain(channel: int) -> float:
    """
    チャンネルのプリアンプゲインを取得

    Args:
        channel: チャンネル番号（1〜32）

    Returns:
        ゲイン（dB）

    Raises:
        X32Error: 通信エラー
    """
    if not (1 <= channel <= 32):
        raise ValueError(f"チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）")

    client = get_client()
    address = f"/ch/{channel:02d}/preamp/gain"
    value = client.query_float(address)
    gain = value_to_gain_db(value, gain_min=-12.0, gain_max=60.0)
    logger.info(f"get_gain({channel}) -> {gain:+.1f} dB")
    return gain


@mcp.resource("x32://channel/{channel}/mute")
def get_mute_status(channel: int) -> bool:
    """
    チャンネルのミュート状態を取得

    Args:
        channel: チャンネル番号（1〜32）

    Returns:
        True=ミュート、False=アンミュート

    Raises:
        X32Error: 通信エラー
    """
    if not (1 <= channel <= 32):
        raise ValueError(f"チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）")

    client = get_client()
    address = f"/ch/{channel:02d}/mix/on"
    value = client.query_int(address)
    # X32: 1=ON(アンミュート)、0=OFF(ミュート)
    # 戻り値: True=ミュート、False=アンミュート
    is_muted = (value == 0)
    logger.info(f"get_mute_status({channel}) -> {'ミュート' if is_muted else 'アンミュート'}")
    return is_muted


@mcp.resource("x32://channel/{channel}/phantom")
def get_phantom_power(channel: int) -> bool:
    """
    チャンネルのファンタム電源状態を取得

    Args:
        channel: チャンネル番号（1〜32）

    Returns:
        True=ON、False=OFF

    Raises:
        X32Error: 通信エラー
    """
    if not (1 <= channel <= 32):
        raise ValueError(f"チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）")

    client = get_client()
    address = f"/ch/{channel:02d}/preamp/phantom"
    value = client.query_int(address)
    is_on = (value == 1)
    logger.info(f"get_phantom_power({channel}) -> {'ON' if is_on else 'OFF'}")
    return is_on


@mcp.resource("x32://fader/{channel}")
def get_fader(channel: int) -> float:
    """
    チャンネルフェーダーレベルを取得

    Args:
        channel: チャンネル番号（1〜32）

    Returns:
        フェーダーレベル（dB）

    Raises:
        X32Error: 通信エラー
    """
    if not (1 <= channel <= 32):
        raise ValueError(f"チャンネル番号は1〜32の範囲で指定してください（指定値: {channel}）")

    client = get_client()
    address = f"/ch/{channel:02d}/mix/fader"
    level = client.query_float(address)
    db = level_to_db(level)
    logger.info(f"get_fader({channel}) -> {db:.1f} dB")
    return db


@mcp.resource("x32://routing/{output_idx}")
def get_routing(output_idx: int) -> str:
    """
    メイン出力のルーティングソースを取得

    Args:
        output_idx: 出力番号（1〜16）

    Returns:
        ルーティングソース（例: "MainL", "Bus5"）

    Raises:
        X32Error: 通信エラー
    """
    if not (1 <= output_idx <= 16):
        raise ValueError(f"出力番号は1〜16の範囲で指定してください（指定値: {output_idx}）")

    client = get_client()
    address = f"/outputs/main/{output_idx:02d}/src"
    code = client.query_int(address)
    source = code_to_source(code)
    logger.info(f"get_routing({output_idx}) -> '{source}'")
    return source


# ========================================
# USB出力設定ツール
# ========================================

@mcp.tool()
def setup_usb_output_for_streaming() -> str:
    """
    USB出力をストリーミング/録音用に自動設定

    この設定により、Main L/R → OUT 5/6 → USB Card 1/2 の経路が構築されます。
    OBS StudioなどでUSBオーディオデバイスとして認識され、メイン出力がそのまま配信・録音できます。

    設定内容:
    - OUT 5 → Main Left に設定
    - OUT 6 → Main Right に設定
    - USB Card Out 1 → OUT 5 にルーティング
    - USB Card Out 2 → OUT 6 にルーティング
    - Card Out 1/2 のレベルを 0dB に設定

    Returns:
        設定完了メッセージまたはエラー

    Note:
        この設定後、パソコン側でUSBオーディオデバイス「X-USB」または「USB Audio CODEC」を
        入力デバイスとして選択してください。
    """
    try:
        client = get_client()

        # ガイドに基づく設定手順：
        # 1. CARD 1/2 → USER OUT に設定
        # 2. USER OUT 1/2 → AUX OUT 5/6 に設定
        # 3. AUX OUT 5/6（物理OUT 5/6）→ Main L/R に設定（通常デフォルト）

        # Step 1: 物理OUT 5/6 をMain L/R に設定（MIX → MAIN で確認する設定）
        # /outputs/main/05 と /outputs/main/06 が Main L/R のソース
        client.send("/outputs/main/05/src", source_to_code("MainL"))
        client.send("/outputs/main/06/src", source_to_code("MainR"))
        logger.info("物理OUT 5/6 → Main Left/Right に設定")

        # Step 2: USER OUT 1/2 を AUX OUT 5/6 に設定（USER → USER OUT メニュー）
        # /config/userout/01-04/src でUSER OUT 1-4のソースを指定
        # AUX OUT 5 = コード値 36 (OUT 5), AUX OUT 6 = コード値 37 (OUT 6)
        # OUT 1-16 のコード値は 32-47 (OUT1=32, OUT2=33, ..., OUT16=47)
        client.send("/config/userout/01/src", 36)  # USER OUT 1 → OUT 5
        client.send("/config/userout/02/src", 37)  # USER OUT 2 → OUT 6
        logger.info("USER OUT 1/2 → AUX OUT 5/6（物理OUT 5/6）に設定")

        # Step 3: CARD 1/2 のソースを USER OUT に設定（CARD メニュー）
        # /config/routing/CARD/01-32 でカード出力のソースを指定
        # USER OUT のコード値: USER OUT 1 = 60, USER OUT 2 = 61
        client.send("/config/routing/CARD/01", 60)  # CARD 1 → USER OUT 1
        client.send("/config/routing/CARD/02", 61)  # CARD 2 → USER OUT 2
        logger.info("CARD 1/2 → USER OUT 1/2 に設定")

        # Step 4: CARD出力レベルを 0dB に設定
        client.send("/config/routing/CARD/01/level", db_to_level(0.0))
        client.send("/config/routing/CARD/02/level", db_to_level(0.0))
        logger.info("CARD 1/2 のレベルを 0dB に設定")

        return """✓ USB出力をストリーミング用に設定しました

📋 信号の流れ:
  マイク入力 → Main L/R → 物理OUT 5/6 → USER OUT 1/2 → CARD 1/2 → USB → パソコン

📋 設定内容:
  - 物理OUT 5 → Main Left
  - 物理OUT 6 → Main Right
  - USER OUT 1 → 物理OUT 5
  - USER OUT 2 → 物理OUT 6
  - CARD 1 → USER OUT 1
  - CARD 2 → USER OUT 2
  - CARD レベル: 0dB

💻 次のステップ:
  1. パソコンで「オーディオ設定」を開く
  2. 入力デバイスで「X-USB」または「USB Audio CODEC」を選択
  3. OBS Studioなどで音声入力デバイスを「USB」に設定
  4. X32のメインフェーダーを動かして音声レベルが連動することを確認

✅ これで X32 のメイン出力がUSB経由でパソコンにステレオで送られます"""

    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("setup_usb_output_for_streaming内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_card_output_routing(card_out: int, source: Literal["OFF", "MainL", "MainR", "MC", "Bus1", "Bus2", "Bus3", "Bus4", "Bus5", "Bus6", "Bus7", "Bus8", "Bus9", "Bus10", "Bus11", "Bus12", "Bus13", "Bus14", "Bus15", "Bus16", "Matrix1", "Matrix2", "Matrix3", "Matrix4", "Matrix5", "Matrix6", "OUT1", "OUT2", "OUT3", "OUT4", "OUT5", "OUT6", "OUT7", "OUT8", "OUT9", "OUT10", "OUT11", "OUT12", "OUT13", "OUT14", "OUT15", "OUT16"]) -> str:
    """
    USB Card出力のルーティングソースを個別設定

    Args:
        card_out: USBカード出力番号（1〜32）
        source: ルーティングソース（"MainL", "MainR", "Bus1", "OUT5" など）

    Returns:
        成功メッセージまたはエラー

    Note:
        - Card Out 1-8 は User Out 1-8 に対応
        - Card Out 9-16 は Aux Out 1-8 に対応
        - Card Out 17-32 は P16 Out 1-16 に対応
        通常のUSBストリーミングでは Card Out 1/2 のみ使用します。
    """
    if not (1 <= card_out <= 32):
        return f"エラー: Card出力番号は1〜32の範囲で指定してください（指定値: {card_out}）"

    try:
        client = get_client()

        # OUTx形式の場合、OUT番号を抽出（OUT5 → 4）
        if source.startswith("OUT"):
            out_num = int(source[3:])
            if not (1 <= out_num <= 16):
                return f"エラー: OUT番号は1〜16の範囲で指定してください（指定値: {source}）"
            # OUT番号から内部コード値へ変換（OUT1=0, OUT2=1, ..., OUT16=15）
            route_code = out_num - 1
        else:
            # MainL, Bus1 などの場合は source_to_code を使用
            route_code = source_to_code(source)

        # Card Out 1-8 の場合
        if 1 <= card_out <= 8:
            address = f"/config/routing/OUT/{card_out:02d}"
            client.send(address, route_code)
            logger.info(f"Card Out {card_out} → {source} に設定")
            return f"✓ USB Card Out {card_out} を {source} にルーティングしました"

        # Card Out 9-16 (Aux Out) の場合
        elif 9 <= card_out <= 16:
            aux_num = card_out - 8
            address = f"/config/routing/AUX/{aux_num:02d}"
            client.send(address, route_code)
            logger.info(f"Card Out {card_out} (Aux {aux_num}) → {source} に設定")
            return f"✓ USB Card Out {card_out} (Aux Out {aux_num}) を {source} にルーティングしました"

        # Card Out 17-32 (P16) の場合
        else:
            p16_num = card_out - 16
            address = f"/config/routing/P16/{p16_num:02d}"
            client.send(address, route_code)
            logger.info(f"Card Out {card_out} (P16 {p16_num}) → {source} に設定")
            return f"✓ USB Card Out {card_out} (P16 Out {p16_num}) を {source} にルーティングしました"

    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_card_output_routing内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def set_card_output_level(card_out: int, level_db: float) -> str:
    """
    USB Card出力のレベルを設定

    Args:
        card_out: USBカード出力番号（1〜8）
        level_db: レベル（-90.0 〜 +10.0 dB）

    Returns:
        成功メッセージまたはエラー

    Note:
        通常は 0dB（ユニティゲイン）に設定します。
        Card Out 9以降のレベル設定は現在未対応です。
    """
    if not (1 <= card_out <= 8):
        return f"エラー: Card出力番号は1〜8の範囲で指定してください（指定値: {card_out}）"

    if not (-90.0 <= level_db <= 10.0):
        return f"エラー: レベルは-90.0〜+10.0 dBの範囲で指定してください（指定値: {level_db}）"

    try:
        client = get_client()
        level = db_to_level(level_db)
        address = f"/config/routing/OUT/{card_out:02d}/level"
        client.send(address, level)
        logger.info(f"Card Out {card_out} のレベルを {level_db:.1f} dB に設定")
        return f"✓ USB Card Out {card_out} のレベルを {level_db:.1f} dB に設定しました"

    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("set_card_output_level内部エラー")
        return f"予期しないエラー: {e}"


@mcp.tool()
def get_usb_routing_status() -> str:
    """
    USB出力のルーティング状態を診断

    現在のUSBルーティング設定を確認し、ストリーミング用の推奨設定と比較します。

    Returns:
        現在の設定状態と期待値の比較レポート
    """
    try:
        client = get_client()

        # 現在の設定を取得
        card1_src = client.query_int("/config/routing/CARD/01")
        card2_src = client.query_int("/config/routing/CARD/02")

        user_out1_src = client.query_int("/config/userout/01/src")
        user_out2_src = client.query_int("/config/userout/02/src")

        out5_src = client.query_int("/outputs/main/05/src")
        out6_src = client.query_int("/outputs/main/06/src")

        # 期待値
        expected_card1 = 60  # USER OUT 1
        expected_card2 = 61  # USER OUT 2
        expected_user1 = 36  # OUT 5
        expected_user2 = 37  # OUT 6
        expected_out5 = source_to_code("MainL")  # Main Left
        expected_out6 = source_to_code("MainR")  # Main Right

        # 結果をフォーマット
        report = "📊 USB出力ルーティング診断\n\n"

        # CARD設定
        report += "【CARD → USER OUT】\n"
        card1_ok = "✓" if card1_src == expected_card1 else "✗"
        card2_ok = "✓" if card2_src == expected_card2 else "✗"
        report += f"  {card1_ok} CARD 1: {card1_src} (期待値: {expected_card1} = USER OUT 1)\n"
        report += f"  {card2_ok} CARD 2: {card2_src} (期待値: {expected_card2} = USER OUT 2)\n\n"

        # USER OUT設定
        report += "【USER OUT → 物理OUT】\n"
        user1_ok = "✓" if user_out1_src == expected_user1 else "✗"
        user2_ok = "✓" if user_out2_src == expected_user2 else "✗"
        report += f"  {user1_ok} USER OUT 1: {user_out1_src} (期待値: {expected_user1} = OUT 5)\n"
        report += f"  {user2_ok} USER OUT 2: {user_out2_src} (期待値: {expected_user2} = OUT 6)\n\n"

        # 物理OUT設定
        report += "【物理OUT → メイン信号】\n"
        out5_ok = "✓" if out5_src == expected_out5 else "✗"
        out6_ok = "✓" if out6_src == expected_out6 else "✗"
        out5_name = code_to_source(out5_src) if out5_src >= 0 else "OFF"
        out6_name = code_to_source(out6_src) if out6_src >= 0 else "OFF"
        report += f"  {out5_ok} OUT 5: {out5_name} (期待値: Main Left)\n"
        report += f"  {out6_ok} OUT 6: {out6_name} (期待値: Main Right)\n\n"

        # 総合判定
        all_ok = (card1_src == expected_card1 and card2_src == expected_card2 and
                  user_out1_src == expected_user1 and user_out2_src == expected_user2 and
                  out5_src == expected_out5 and out6_src == expected_out6)

        if all_ok:
            report += "✅ 総合判定: すべて正しく設定されています\n"
            report += "   USB出力は Main L/R → OUT 5/6 → USER OUT 1/2 → CARD 1/2 → USB の経路で動作します"
        else:
            report += "⚠️ 総合判定: 一部の設定が推奨値と異なります\n"
            report += "   setup_usb_output_for_streaming() を実行して正しく設定してください"

        return report

    except X32Error as e:
        return f"エラー: {e}"
    except Exception as e:
        logger.exception("get_usb_routing_status内部エラー")
        return f"予期しないエラー: {e}"


# ========================================
# CLI起動
# ========================================

app = typer.Typer()


@app.command()
def stdio():
    """
    STDIOモードでMCPサーバーを起動

    **重要**: STDIOモードではstdoutへの出力は厳禁です。
    すべてのログはstderrに出力されます。
    """
    logger.info("Starting X32 MCP Server in STDIO mode")
    mcp.run(transport="stdio")


@app.command()
def http(host: str = "127.0.0.1", port: int = 8000):
    """
    Streamable HTTPモードでMCPサーバーを起動

    Args:
        host: バインドするホスト
        port: バインドするポート
    """
    logger.info(f"Starting X32 MCP Server in HTTP mode on {host}:{port}")
    import uvicorn

    # FastMCPのASGIアプリを取得
    app = mcp.get_asgi_app()
    uvicorn.run(app, host=host, port=port)


def cli():
    """
    エントリポイント（pyproject.tomlから呼ばれる）
    """
    app()


if __name__ == "__main__":
    cli()