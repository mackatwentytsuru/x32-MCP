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

## 提供ツール（27ツール）

### 基本チャンネル操作（10ツール）

- `set_fader(channel, volume_db)` - フェーダーレベル設定（-90〜+10 dB）
- `set_mute(channel, mute)` - ミュート設定
- `set_pan(channel, pan)` - パン設定（-100=左, 0=中央, +100=右）
- `set_channel_name(channel, name)` - チャンネル名設定
- `set_channel_color(channel, color)` - 色設定（RED/GREEN/YELLOW/BLUE等）
- `set_channel_icon(channel, icon)` - アイコン設定（Mic/Guitar/Piano等）
- `set_gain(channel, gain_db)` - プリアンプゲイン設定（-12〜+60 dB）
- `set_phantom_power(channel, enabled)` - ファンタム電源ON/OFF
- `set_bus_send(channel, bus, level_db)` - バス送りレベル設定
- `route_output(output_idx, source)` - 出力ルーティング設定

### EQ制御（3ツール）

- `set_eq_enabled(channel, enabled)` - EQ ON/OFF
- `set_eq_band(channel, band, freq_hz, gain_db, q)` - 4バンドパラメトリックEQ設定
  - band: 1〜4
  - freq_hz: 20〜20000 Hz
  - gain_db: -15〜+15 dB
  - q: 0.3〜10.0
- `reset_eq(channel)` - EQリセット（全バンド0dB）

### Bus・Matrix・Main LR（8ツール）

- `set_bus_fader(bus, level_db)` - バスフェーダー設定（1〜16）
- `set_bus_mute(bus, mute)` - バスミュート設定
- `set_matrix_fader(matrix, level_db)` - Matrixフェーダー設定（1〜6）
- `set_matrix_mute(matrix, mute)` - Matrixミュート設定
- `set_auxin_fader(auxin, level_db)` - AuxInフェーダー設定（1〜8）
- `set_auxin_mute(auxin, mute)` - AuxInミュート設定
- `set_main_lr_fader(level_db)` - メインLRフェーダー設定
- `set_main_lr_mute(mute)` - メインLRミュート設定

### DCAグループ（4ツール）

- `set_dca_fader(dca, level_db)` - DCAフェーダー設定（1〜8）
- `set_dca_mute(dca, mute)` - DCAミュート設定
- `set_dca_name(dca, name)` - DCA名設定
- `set_dca_color(dca, color)` - DCA色設定

### Resources（取得系・8ツール）

- `get_fader(channel)` - フェーダーレベル取得
- `get_pan(channel)` - パン取得
- `get_gain(channel)` - ゲイン取得
- `get_mute_status(channel)` - ミュート状態取得
- `get_phantom_power(channel)` - ファンタム電源状態取得
- `get_routing(output_idx)` - 出力ルーティング取得
- `get_channel_name(channel)` - チャンネル名取得※
- `get_channel_color(channel)` - チャンネル色取得※

※一部のResourcesはX32のOSC制限により未実装

## テスト

```bash
pytest -q
```

モックX32を起動した状態で実行すると、エンドツーエンドでの動作確認が可能です。

## 設定

デフォルトでは `192.168.1.100:10023` に接続します。
`src/x32_mcp/config.py` で `X32_IP` を実機/モックのIPアドレスに変更してください。

## 使用例

### Claude Desktopでの利用

MCPサーバーを設定後、自然言語でX32を操作できます：

```
「チャンネル1の名前をVocal 1にして、色を赤にして」
→ set_channel_name(1, "Vocal 1"), set_channel_color(1, "RED")

「チャンネル1のフェーダーを0dBにして、パンを中央にして」
→ set_fader(1, 0.0), set_pan(1, 0)

「チャンネル2のEQで、3kHzを+5dBブーストして」
→ set_eq_enabled(2, true), set_eq_band(2, 2, 3000, 5.0, 1.0)

「DCA1にVocalsと名前をつけて、フェーダーを-3dBに」
→ set_dca_name(1, "Vocals"), set_dca_fader(1, -3.0)

「メインLRフェーダーを-5dBに下げて」
→ set_main_lr_fader(-5.0)
```

### プログラムからの利用

```python
from x32_mcp.osc_client import X32Client
from x32_mcp.conv import db_to_level

client = X32Client(host="192.168.1.12", port=10023)
client.start_xremote_keepalive()

# チャンネル1を設定
client.send("/ch/01/config/name", "Vocal 1")
client.send("/ch/01/mix/fader", db_to_level(0.0))
client.send("/ch/01/mix/pan", 0.5)  # 中央

# EQ設定
client.send("/ch/01/eq/on", 1)
client.send("/ch/01/eq/2/f", freq_to_value(3000))
client.send("/ch/01/eq/2/g", gain_db_to_value(5.0, -15, 15))
```

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