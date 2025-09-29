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
from .mapping import source_to_code, code_to_source
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
# Resources（取得系）
# ========================================

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