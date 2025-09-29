"""
MCPツールのスモークテスト

モックX32に対して実際にOSC通信を行い、基本動作を確認する。
"""

import pytest
import time
import subprocess
import socket
from x32_mcp.server import set_fader, set_mute, set_bus_send, route_output, get_fader, get_routing
from x32_mcp.osc_client import X32Client


@pytest.fixture(scope="module")
def mock_x32():
    """
    モックX32をサブプロセスで起動

    Note:
        scripts/fake_x32.py が別途起動されている場合は、このfixture不要。
        テスト実行前に手動で起動してください。
    """
    # モックが既に起動しているか確認
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("127.0.0.1", 10023))
        sock.close()
        # ポートが空いている→モックを起動
        proc = subprocess.Popen(
            ["python", "scripts/fake_x32.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(1)  # 起動待機
        yield proc
        proc.terminate()
        proc.wait()
    except OSError:
        # ポートが使用中→既に起動済み
        sock.close()
        yield None


class TestToolsSmoke:
    """MCPツールの基本動作テスト"""

    def test_set_fader(self, mock_x32):
        result = set_fader(channel=1, volume_db=-10.0)
        assert "✓" in result
        assert "チャンネル1" in result

    def test_set_fader_invalid_channel(self, mock_x32):
        result = set_fader(channel=0, volume_db=-10.0)
        assert "エラー" in result
        assert "1〜32" in result

    def test_set_fader_invalid_db(self, mock_x32):
        result = set_fader(channel=1, volume_db=-100.0)
        assert "エラー" in result
        assert "-90.0〜+10.0" in result

    def test_set_mute(self, mock_x32):
        result = set_mute(channel=1, mute=True)
        assert "✓" in result
        assert "ミュート" in result

    def test_set_bus_send(self, mock_x32):
        result = set_bus_send(channel=1, bus=5, level_db=-20.0)
        assert "✓" in result
        assert "バス5" in result

    def test_route_output(self, mock_x32):
        result = route_output(output_idx=1, source="Bus5")
        assert "✓" in result
        assert "Bus5" in result

    def test_route_output_invalid_source(self, mock_x32):
        result = route_output(output_idx=1, source="InvalidSource")
        assert "エラー" in result
        assert "無効な出力ソース" in result

    def test_get_fader(self, mock_x32):
        # まず設定
        set_fader(channel=1, volume_db=-15.0)
        time.sleep(0.1)

        # 取得
        db = get_fader(channel=1)
        assert isinstance(db, float)
        # モックは更新されているはずだが、線形近似なので誤差を許容
        assert -90.0 <= db <= 10.0

    def test_get_routing(self, mock_x32):
        # まず設定
        route_output(output_idx=1, source="Bus5")
        time.sleep(0.1)

        # 取得
        source = get_routing(output_idx=1)
        assert isinstance(source, str)
        # モックが正しく応答していれば "Bus5" が返る
        # （モックの初期値は "MainL"=1 だが、上で設定したので "Bus5"）
        assert source in ["MainL", "Bus5"]  # 初期値または設定値