"""
X32 MCP Server settings / 設定

Set the mixer address with environment variables (no need to edit this file):
  X32_IP    IP address of the X32 (or of the mock server)   default: 192.168.1.100
  X32_PORT  OSC UDP port of the X32                         default: 10023
環境変数 X32_IP / X32_PORT で、ミキサーの宛先を指定できます(このファイルを書き換える必要はありません)。
"""

import os

# X32 destination (change to your mixer's or the mock's address)
# X32の送信先IP(実機またはモックのアドレスに変更してください)
X32_IP = os.environ.get("X32_IP", "192.168.1.100")
X32_PORT = int(os.environ.get("X32_PORT", "10023"))

# keepalive interval in seconds / keepalive間隔(秒)
XREMOTE_INTERVAL = 8.0

# Rate limit: sleep after each OSC send, in seconds / レート制限:各OSC送信後のsleep時間(秒)
RATE_LIMIT_SLEEP = 0.01

# Timeout waiting for an OSC reply, in seconds / タイムアウト:OSC応答待機時間(秒)
OSC_RECV_TIMEOUT = 0.8
