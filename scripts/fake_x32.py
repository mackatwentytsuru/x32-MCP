"""
モックX32 - UDP :10023で最小限のOSCアドレスに応答

開発・テスト用の簡易X32エミュレーター。
実機が無い環境でもMCPサーバーの動作確認が可能。
"""

import socket
import logging
from pythonosc.osc_message_builder import OscMessageBuilder
from pythonosc.osc_message import OscMessage

logging.basicConfig(
    level=logging.INFO,
    format="[MOCK X32] %(message)s"
)
logger = logging.getLogger(__name__)

# 内部状態
state = {
    "/ch/01/mix/fader": 0.50,  # level型（0.0〜1.0）
    "/ch/01/mix/on": 1,  # 1=ON(アンミュート)、0=OFF(ミュート)
    "/ch/01/mix/01/level": 0.30,
    "/outputs/main/01/src": 1,  # 1=MainL
}


def handle_message(msg: OscMessage, addr: tuple) -> bytes | None:
    """
    OSCメッセージを処理し、必要に応じて応答を返す

    Args:
        msg: 受信したOSCメッセージ
        addr: 送信元アドレス

    Returns:
        応答OSCメッセージのバイト列（応答不要ならNone）
    """
    address = msg.address
    params = msg.params

    # /xremote keepalive → 無視（ログのみ）
    if address == "/xremote":
        logger.debug("Received /xremote keepalive")
        return None

    # GET（値なし）→ 応答を返す
    if not params:
        if address in state:
            value = state[address]
            builder = OscMessageBuilder(address=address)
            if isinstance(value, float):
                builder.add_arg(value, "f")
            elif isinstance(value, int):
                builder.add_arg(value, "i")
            response = builder.build()
            logger.info(f"GET {address} -> {value}")
            return response.dgram
        else:
            logger.warning(f"GET {address} -> (未実装)")
            return None

    # SET（値あり）→ 内部状態を更新
    else:
        state[address] = params[0]
        logger.info(f"SET {address} = {params[0]}")
        return None


def main():
    """
    モックX32のメインループ
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 10023))
    logger.info("Mock X32 listening on UDP :10023")
    logger.info("Press Ctrl+C to stop")

    try:
        while True:
            data, addr = sock.recvfrom(4096)
            try:
                msg = OscMessage(data)
                response = handle_message(msg, addr)
                if response:
                    sock.sendto(response, addr)
            except Exception as e:
                logger.error(f"メッセージ処理エラー: {e}")
    except KeyboardInterrupt:
        logger.info("Shutting down mock X32")
    finally:
        sock.close()


if __name__ == "__main__":
    main()