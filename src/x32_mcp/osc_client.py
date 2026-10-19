"""
X32 OSCクライアント

python-oscを使用してX32と通信：
- 送信：SimpleUDPClientで各種パラメータを設定
- GET問合せ：値なしメッセージを送信し、応答を受け取る
- keepalive：/xremoteを定期的に送信（スレッド）
"""

import logging
import socket
import time
import threading
from typing import Optional

from pythonosc.udp_client import SimpleUDPClient
from pythonosc.osc_message_builder import OscMessageBuilder
from pythonosc.osc_message import OscMessage

from .config import X32_IP, X32_PORT, XREMOTE_INTERVAL, RATE_LIMIT_SLEEP, OSC_RECV_TIMEOUT

logger = logging.getLogger(__name__)


class X32Error(Exception):
    """X32通信エラー"""
    pass


class X32Client:
    """
    X32 OSCクライアント

    送信、GET問合せ、/xremote keepaliveを管理
    """

    def __init__(
        self,
        host: str = X32_IP,
        port: int = X32_PORT,
        recv_timeout: float = OSC_RECV_TIMEOUT
    ):
        self.host = host
        self.port = port
        self.recv_timeout = recv_timeout

        # 送信用クライアント
        self._client = SimpleUDPClient(host, port)

        # GET問合せ用ソケット（受信も行う）
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.settimeout(recv_timeout)

        # keepaliveスレッド
        self._keepalive_thread: Optional[threading.Thread] = None
        self._keepalive_stop = threading.Event()

        logger.info(f"X32Client initialized for {host}:{port}")

    def send(self, address: str, *values) -> None:
        """
        OSCメッセージを送信

        Args:
            address: OSCアドレス (例: "/ch/01/mix/fader")
            values: 送信する値（float, int, str等）

        Raises:
            X32Error: 送信エラー
        """
        try:
            self._client.send_message(address, values if values else [])
            time.sleep(RATE_LIMIT_SLEEP)  # レート制限
            logger.debug(f"Sent: {address} {values}")
        except Exception as e:
            raise X32Error(f"OSC送信エラー ({address}): {e}")

    def _roundtrip(self, address: str) -> OscMessage:
        """
        値なしメッセージを送信し、応答メッセージを返す(内部用)

        Windows では、直前に送った UDP が「宛先なし」で戻されると、次の recvfrom が
        ConnectionResetError (WinError 10054) になる。古いエラーなので、1回だけ送り直す。
        On Windows a stale ICMP "port unreachable" from an earlier send makes the next
        recvfrom raise ConnectionResetError; the request is simply sent once more.
        """
        for attempt in (1, 2):
            builder = OscMessageBuilder(address=address)
            msg = builder.build()
            self._sock.sendto(msg.dgram, (self.host, self.port))
            time.sleep(RATE_LIMIT_SLEEP)
            try:
                data, _ = self._sock.recvfrom(4096)
            except ConnectionResetError:
                if attempt == 2:
                    raise
                logger.debug(f"Stale connection reset on {address}; retrying once")
                continue
            return OscMessage(data)
        raise X32Error(f"応答を取得できませんでした: {address}")  # pragma: no cover

    def query_float(self, address: str) -> float:
        """
        値なしメッセージを送信し、float応答を取得

        Args:
            address: OSCアドレス (例: "/ch/01/mix/fader")

        Returns:
            X32から返されたfloat値

        Raises:
            X32Error: 通信エラー、応答なし、パースエラー
        """
        try:
            # 値なしメッセージを送信し、応答を受信
            response = self._roundtrip(address)

            # 最初の引数をfloatとして取得
            if not response.params:
                raise X32Error(f"応答に値が含まれていません: {address}")

            value = float(response.params[0])
            logger.debug(f"Queried: {address} -> {value}")
            return value

        except socket.timeout:
            raise X32Error(f"X32からの応答がタイムアウトしました: {address}")
        except Exception as e:
            raise X32Error(f"OSC問合せエラー ({address}): {e}")

    def query_int(self, address: str) -> int:
        """
        値なしメッセージを送信し、int応答を取得

        Args:
            address: OSCアドレス

        Returns:
            X32から返されたint値

        Raises:
            X32Error: 通信エラー、応答なし、パースエラー
        """
        try:
            response = self._roundtrip(address)

            if not response.params:
                raise X32Error(f"応答に値が含まれていません: {address}")

            value = int(response.params[0])
            logger.debug(f"Queried: {address} -> {value}")
            return value

        except socket.timeout:
            raise X32Error(f"X32からの応答がタイムアウトしました: {address}")
        except Exception as e:
            raise X32Error(f"OSC問合せエラー ({address}): {e}")

    def start_xremote_keepalive(self, interval: float = XREMOTE_INTERVAL) -> None:
        """
        /xremote keepaliveを開始（バックグラウンドスレッド）

        Args:
            interval: 送信間隔（秒、推奨8〜10秒）
        """
        if self._keepalive_thread and self._keepalive_thread.is_alive():
            logger.warning("keepaliveスレッドは既に実行中です")
            return

        self._keepalive_stop.clear()
        self._keepalive_thread = threading.Thread(
            target=self._keepalive_loop,
            args=(interval,),
            daemon=True
        )
        self._keepalive_thread.start()
        logger.info(f"keepalive started (interval={interval}s)")

    def stop_xremote_keepalive(self) -> None:
        """
        /xremote keepaliveを停止
        """
        if not self._keepalive_thread or not self._keepalive_thread.is_alive():
            return

        self._keepalive_stop.set()
        self._keepalive_thread.join(timeout=2.0)
        logger.info("keepalive stopped")

    def _keepalive_loop(self, interval: float) -> None:
        """
        keepaliveループ（スレッド内部）
        """
        while not self._keepalive_stop.wait(timeout=interval):
            try:
                self._client.send_message("/xremote", [])
                logger.debug("Sent /xremote keepalive")
            except Exception as e:
                logger.error(f"keepalive送信エラー: {e}")

    def close(self) -> None:
        """
        リソースをクリーンアップ
        """
        self.stop_xremote_keepalive()
        self._sock.close()
        logger.info("X32Client closed")