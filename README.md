# X32 MCP Server

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

Behringer X32 デジタルミキサーを**自然言語エージェント（Claude Code/Claude Desktop/ChatGPT等）**から操作するための[Model Context Protocol (MCP)](https://modelcontextprotocol.io/)サーバー実装です。

AIアシスタントと会話するだけで、X32の設定変更やミキシング操作を自動化できます。

## ✨ 特徴

- 🎛️ **包括的なX32制御** - フェーダー、EQ、ルーティング、DCAなど27種類の操作ツールを提供
- 🤖 **自然言語操作** - 「チャンネル1のフェーダーを-3dBに」といった指示で操作可能
- 🔌 **FastMCP + python-osc** - OSC over UDP (port 10023) による高速通信
- 🌐 **複数トランスポート対応** - STDIO（Claude Desktop/Claude Code）とStreamable HTTP（Web統合）の両方をサポート
- ♻️ **自動keepalive** - X32との接続を維持（/xremoteを8秒間隔で自動送信）
- 🧪 **モックX32同梱** - 実機なしでの開発・テストが可能
- 🔒 **セキュリティ設計** - IP固定、入力バリデーション、レート制限を実装

## 📋 必要要件

- Python 3.11 以上
- Behringer X32/X32 Rack/M32 デジタルミキサー（または互換エミュレーター）
- ネットワーク接続（UDP 10023番ポート）

## 🚀 クイックスタート

### 1. インストール

```bash
# リポジトリをクローン
git clone https://github.com/mackatwentytsuru/x32-MCP.git
cd x32-MCP

# 仮想環境を作成してアクティベート
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係をインストール
pip install -e .
```

### 2. X32のIPアドレスを設定

`src/x32_mcp/config.py`を編集して、X32のIPアドレスを設定：

```python
X32_IP = "192.168.1.12"  # あなたのX32のIPアドレスに変更
X32_PORT = 10023
```

### 3. Claude CodeまたはClaude Desktopで使用

#### Claude Codeで使用する場合

```bash
# ユーザースコープで追加（すべてのプロジェクトで利用可能）
claude mcp add x32-mcp --scope user --env PATH="$(pwd)/.venv/bin:/usr/local/bin:/usr/bin:/bin" -- python -m x32_mcp.server stdio

# プロジェクトスコープで追加（このプロジェクトのみで利用可能）
claude mcp add x32-mcp --scope project --env PATH="$(pwd)/.venv/bin:/usr/local/bin:/usr/bin:/bin" -- python -m x32_mcp.server stdio
```

Claude Codeを再起動すると、X32操作ツールが利用可能になります。

#### Claude Desktopで使用する場合

`~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）または
`%APPDATA%\Claude\claude_desktop_config.json`（Windows）に以下を追加：

```json
{
  "mcpServers": {
    "x32-mcp": {
      "command": "python",
      "args": ["-m", "x32_mcp.server", "stdio"],
      "cwd": "/path/to/x32-MCP",
      "env": {
        "PATH": "/path/to/x32-MCP/.venv/bin:/usr/local/bin:/usr/bin:/bin"
      }
    }
  }
}
```

Claude Desktopを再起動してください。

### 4. 開発・テスト用（オプション）

実機がない場合は、モックX32サーバーを使用できます：

```bash
# 別ターミナルでモックX32を起動
python scripts/fake_x32.py

# テストを実行
pip install -e ".[dev]"
pytest -q
```

## 💬 使用例

MCPサーバーを設定後、Claude Code/Claude Desktopで自然言語でX32を操作できます：

### 基本操作

```
👤 「チャンネル1の名前をVocal 1にして、色を赤にして」
🤖 → set_channel_name(1, "Vocal 1"), set_channel_color(1, "RED")

👤 「チャンネル1のフェーダーを0dBにして、パンを中央にして」
🤖 → set_fader(1, 0.0), set_pan(1, 0)

👤 「チャンネル2をミュートして」
🤖 → set_mute(2, true)
```

### EQ調整

```
👤 「チャンネル2のEQで、3kHzを+5dBブーストして」
🤖 → set_eq_enabled(2, true), set_eq_band(2, 2, 3000, 5.0, 1.0)

👤 「チャンネル1のEQをリセットして」
🤖 → reset_eq(1)
```

### DCAグループ

```
👤 「DCA1にVocalsと名前をつけて、フェーダーを-3dBに」
🤖 → set_dca_name(1, "Vocals"), set_dca_fader(1, -3.0)

👤 「DCA1を黄色にして」
🤖 → set_dca_color(1, "YELLOW")
```

### マスター操作

```
👤 「メインLRフェーダーを-5dBに下げて」
🤖 → set_main_lr_fader(-5.0)

👤 「バス3のフェーダーを-10dBにして、ミュートして」
🤖 → set_bus_fader(3, -10.0), set_bus_mute(3, true)
```

## 🔧 高度な使用方法

### MCP Inspectorでの開発

```bash
mcp dev src/x32_mcp/server.py
# または
uv run mcp dev src/x32_mcp/server.py
```

> **重要**: STDIOモードでは `stdout` への出力は厳禁です（MCP JSON破損防止）。ログは自動的に `stderr` に出力されます。

### Streamable HTTPモード

Web統合やカスタムクライアント向け：

```bash
python -m x32_mcp.server http --host 127.0.0.1 --port 8000
```

### Pythonプログラムから直接使用

```python
from x32_mcp.osc_client import X32Client
from x32_mcp.conv import db_to_level

# X32に接続
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

## 🎛️ 提供ツール（27ツール）

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

## 🧪 テスト

```bash
# 依存関係をインストール
pip install -e ".[dev]"

# テストを実行
pytest -q
```

モックX32を起動した状態で実行すると、エンドツーエンドでの動作確認が可能です。

## 🔒 セキュリティと堅牢性

- **IP固定**: 送信先IP/ポートは設定ファイルで固定（任意アドレスへの送信不可）
- **入力バリデーション**: 範囲外の値や無効な入力は明示的にバリデーション
- **レート制限**: 簡易レート制限を実装（短時間のsleep）
- **エラーハンドリング**: 例外はユーザーフレンドリーなエラーメッセージに変換
- **ログ管理**: STDIOモードではstderrにログ出力（MCP JSON破損防止）

## 🛠️ トラブルシューティング

### MCPサーバーが接続されない

```bash
# サーバーの接続状態を確認
claude mcp list

# サーバーを再追加
claude mcp remove x32-mcp
claude mcp add x32-mcp --scope user --env PATH="$(pwd)/.venv/bin:/usr/local/bin:/usr/bin:/bin" -- python -m x32_mcp.server stdio
```

### X32に接続できない

1. X32とコンピュータが同じネットワークにいることを確認
2. X32のIPアドレスを確認（Setup → Network画面で確認）
3. `src/x32_mcp/config.py`のIPアドレスが正しいことを確認
4. ファイアウォールでUDP 10023ポートが開いていることを確認

### モックX32サーバーが起動しない

```bash
# ポート10023が既に使用されていないか確認
lsof -i :10023  # macOS/Linux
netstat -an | grep 10023  # Windows

# 既存のプロセスを終了してから再起動
python scripts/fake_x32.py
```

## 🚧 今後の拡張予定

- [ ] dB ⇄ level型の厳密な4レンジ変換（現在は線形近似）
- [ ] DirectOutCh01〜32等、追加の出力ソースマッピング
- [ ] Dynamics（コンプレッサー、ゲート）パラメータの制御
- [ ] Effectsパラメータの制御
- [ ] シーン/スナップショット管理
- [ ] チャンネルリンク/グループ管理
- [ ] メーター値の取得

## 🤝 コントリビューション

Pull Requestを歓迎します！以下の手順でコントリビュートできます：

1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. Pull Requestを作成

## 📚 参考リンク

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [FastMCP](https://github.com/jlowin/fastmcp)
- [python-osc](https://github.com/attwad/python-osc)
- [X32 OSC仕様（非公式）](https://sites.google.com/site/patrickmaillot/x32)
- [Behringer X32公式サイト](https://www.behringer.com/product.html?modelCode=P0ASF)

## 📝 ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 👤 作者

**mackatwentytsuru**

- GitHub: [@mackatwentytsuru](https://github.com/mackatwentytsuru)

---

⭐ このプロジェクトが役に立ったら、GitHubでスターをつけてください！