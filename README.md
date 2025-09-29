# X32 MCP Server

Behringer X32 デジタルミキサーを**自然言語エージェント（Claude/ChatGPT等）**から操作するためのMCPサーバー実装です。

## 特徴

- **FastMCP + python-osc** による OSC over UDP (port 10023) 制御
- **STDIO/Streamable HTTP** 両対応のトランスポート
- **自動keepalive**（/xremote を8秒間隔で送信）
- **モックX32** を同梱し、実機なしでの開発・テストが可能
- フェーダー、ミュート、バス送り、出力ルーティング等の基本操作をツールとして提供

## セットアップ

### 1. 仮想環境の作成とインストール

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

### 2. 開発用依存関係（テスト実行時）

```bash
pip install -e ".[dev]"
```

## 使い方

### モックX32の起動（開発・テスト用）

別ターミナルで以下を実行：

```bash
python scripts/fake_x32.py
```

モックは UDP :10023 で待ち受け、最小限のOSCアドレスに応答します。

> **注意**: 本番環境では実機またはエミュレーター（[pmaillot/X32-Behringer](https://github.com/pmaillot/X32-Behringer)）の使用を推奨します。

### MCPサーバーの起動

#### STDIOモード（MCP Inspector / Claude Desktop等）

```bash
mcp dev src/x32_mcp/server.py
# または
uv run mcp dev src/x32_mcp/server.py
```

> **重要**: STDIOモードでは `stdout` への出力は厳禁です（MCP JSON破損防止）。ログは自動的に `stderr` に出力されます。

#### Streamable HTTPモード（任意）

```bash
python -m x32_mcp.server http --host 127.0.0.1 --port 8000
```

## 提供ツール

### Tools（操作）

- `set_fader(channel: int, volume_db: float) -> str`
  チャンネルフェーダーレベルを設定（-90.0 〜 +10.0 dB）

- `set_mute(channel: int, mute: bool) -> str`
  チャンネルミュート状態を設定
  **注意**: X32では `/ch/{cc}/mix/on` = 1 がアンミュート、0 がミュート

- `set_bus_send(channel: int, bus: int, level_db: float) -> str`
  チャンネルからバス(1〜16)への送りレベルを設定

- `route_output(output_idx: int, source: str) -> str`
  メイン出力(1〜16)のルーティングソースを設定
  source例: "OFF", "MainL", "MainR", "MC", "Bus1"〜"Bus16", "Matrix1"〜"Matrix6"

### Resources（取得）

- `get_fader(channel: int) -> float`
  チャンネルフェーダーレベルを取得（dB）

- `get_routing(output_idx: int) -> str`
  メイン出力のルーティングソースを取得（文字列）

## テスト

```bash
pytest -q
```

モックX32を起動した状態で実行すると、エンドツーエンドでの動作確認が可能です。

## 設定

デフォルトでは `192.168.1.100:10023` に接続します。
`src/x32_mcp/config.py` で `X32_IP` を実機/モックのIPアドレスに変更してください。

## セキュリティと堅牢性

- 送信先IP/ポートは設定ファイルで固定（任意アドレスへの送信不可）
- 範囲外の値や無効な入力は明示的にバリデーション
- 簡易レート制限を実装（短時間のsleep）
- 例外はユーザーフレンドリーなエラーメッセージに変換

## 今後の拡張

- dB ⇄ level型の厳密な4レンジ変換（現在は線形近似）
- DirectOutCh01〜32等、追加の出力ソースマッピング
- EQ、Dynamics、Effectsパラメータの制御
- シーン/スナップショット管理

## ライセンス

MIT