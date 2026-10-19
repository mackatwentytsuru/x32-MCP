"""osc_client: a stale Windows "connection reset" on recvfrom is retried once."""

import pytest
from pythonosc.osc_message_builder import OscMessageBuilder

from x32_mcp.osc_client import X32Client, X32Error


def _reply(address: str, value: float) -> bytes:
    builder = OscMessageBuilder(address=address)
    builder.add_arg(value)
    return builder.build().dgram


class FlakySocket:
    """Fake UDP socket: recvfrom raises ConnectionResetError `fail_times` times, then answers."""

    def __init__(self, fail_times: int, data: bytes):
        self.fail_times = fail_times
        self.data = data
        self.sent = 0

    def sendto(self, dgram, addr):
        self.sent += 1

    def recvfrom(self, size):
        if self.fail_times > 0:
            self.fail_times -= 1
            raise ConnectionResetError("stale ICMP port unreachable")
        return self.data, ("127.0.0.1", 10023)

    def close(self):
        pass


def _client(sock) -> X32Client:
    client = X32Client(host="127.0.0.1", port=10023)
    client._sock.close()
    client._sock = sock
    return client


def test_one_stale_reset_is_retried():
    sock = FlakySocket(1, _reply("/ch/01/mix/fader", 0.5))
    assert _client(sock).query_float("/ch/01/mix/fader") == pytest.approx(0.5)
    assert sock.sent == 2


def test_persistent_reset_becomes_an_x32_error():
    sock = FlakySocket(5, _reply("/ch/01/mix/fader", 0.5))
    with pytest.raises(X32Error):
        _client(sock).query_float("/ch/01/mix/fader")
    assert sock.sent == 2
