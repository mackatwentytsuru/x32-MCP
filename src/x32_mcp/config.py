"""
X32 MCP Server 設定
"""

# X32の送信先IP（実機またはモックのアドレスに変更してください）
X32_IP = "127.0.0.1"  # モック用。実機の場合は "192.168.1.100" など
X32_PORT = 10023

# keepalive間隔（秒）
XREMOTE_INTERVAL = 8.0

# レート制限：各OSC送信後のsleep時間（秒）
RATE_LIMIT_SLEEP = 0.01

# タイムアウト：OSC応答待機時間（秒）
OSC_RECV_TIMEOUT = 0.8