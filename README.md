# X32 MCP Server

[English](#english) | [日本語](#日本語)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-server-green.svg)](https://modelcontextprotocol.io/)

---

## English

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that lets an AI assistant (Claude Code, Claude Desktop, or any MCP client) control a **Behringer X32** digital mixer over OSC. It was built with Claude Code.

You talk to the assistant ("set channel 1 to -3 dB and name it Vocal 1"), and the assistant calls these tools, which send OSC messages to the mixer.

> **Maintenance note:** The author no longer owns the hardware (Behringer X32), so updates will be slow and hardware testing is not possible. Issues and pull requests are still welcome.

> **メンテナンスについて:** 作者は現在この機材(Behringer X32)を持っていないため、更新はゆっくりになり、実機での確認はできません。Issue や Pull Request は歓迎します。

### Features

- 31 tools: faders, mutes, pan, preamp gain, phantom power, 4-band EQ, bus sends, buses, matrices, Aux In, Main LR, DCA groups, output routing, USB (card) output setup, and read-only status queries
- 8 read-only MCP resources (fader, pan, gain, mute, phantom power, channel name and color, output routing)
- OSC over UDP (default port 10023) with python-osc and FastMCP
- Automatic `/xremote` keepalive (every 8 seconds) to stay subscribed to the mixer
- STDIO transport (Claude Code, Claude Desktop). An HTTP command also exists (see [Limitations](#limitations))
- A mock X32 (`scripts/fake_x32.py`) so you can develop and test without a mixer
- The destination IP/port is fixed by configuration, and values are range-checked before they are sent

### Requirements

- Python 3.11 or newer
- The MCP Python SDK 1.x (`pip install -e .` pulls `mcp<2`; the code uses its `FastMCP`, which was renamed in 2.x)
- A Behringer X32 / X32 Rack / M32, or the bundled mock server
- Network access to the mixer on UDP port 10023

### Install

```bash
git clone https://github.com/mackatwentytsuru/x32-MCP.git
cd x32-MCP
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
```

### Configure the mixer address

Set the IP address of your X32 with an environment variable (the default `192.168.1.100` is only a placeholder):

```bash
export X32_IP=192.168.1.50       # your X32's address (X32 Setup > Network)
export X32_PORT=10023            # optional
```

The values are read in `src/x32_mcp/config.py`.

### Use it with Claude Code

```bash
# macOS / Linux (user scope: available in every project)
claude mcp add x32-mcp --scope user \
  --env X32_IP=192.168.1.50 \
  -- "$(pwd)/.venv/bin/python" -m x32_mcp.server stdio
```

On Windows, point the command at `.venv\Scripts\python.exe` instead. Restart Claude Code and the X32 tools appear.

### Use it with Claude Desktop

Add this to `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/`, Windows: `%APPDATA%\Claude\`):

```json
{
  "mcpServers": {
    "x32-mcp": {
      "command": "/path/to/x32-MCP/.venv/bin/python",
      "args": ["-m", "x32_mcp.server", "stdio"],
      "env": { "X32_IP": "192.168.1.50" }
    }
  }
}
```

### Try it without a mixer

```bash
# terminal 1: start the mock X32 (listens on UDP 10023)
python scripts/fake_x32.py

# terminal 2: point the server at the mock and run the tests
pip install -e ".[dev]"
X32_IP=127.0.0.1 pytest -q       # PowerShell: $env:X32_IP="127.0.0.1"; pytest -q
```

### Example requests

| You say | Tool calls |
|---|---|
| "Name channel 1 Vocal 1 and make it red" | `set_channel_name(1, "Vocal 1")`, `set_channel_color(1, "RED")` |
| "Fader of channel 1 to 0 dB, pan center" | `set_fader(1, 0.0)`, `set_pan(1, 0)` |
| "Boost 3 kHz on channel 2 by 5 dB" | `set_eq_enabled(2, true)`, `set_eq_band(2, 2, 3000, 5.0, 1.0)` |
| "Name DCA 1 Vocals and set it to -3 dB" | `set_dca_name(1, "Vocals")`, `set_dca_fader(1, -3.0)` |
| "Send the main mix to the computer over USB" | `setup_usb_output_for_streaming()` |

`setup_usb_output_for_streaming()` routes Main L/R to OUT 5/6 and then to USB card outputs 1/2, so that streaming software can pick the mixer up as a USB audio device.

### Tools

**Channel** (10): `set_fader` (-90 to +10 dB), `set_mute`, `set_pan` (-100 to +100), `set_channel_name`, `set_channel_color`, `set_channel_icon`, `set_gain` (-12 to +60 dB), `set_phantom_power`, `set_bus_send`, `route_output`

**EQ** (3): `set_eq_enabled`, `set_eq_band` (band 1-4, 20-20000 Hz, -15 to +15 dB, Q 0.3-10), `reset_eq`

**Bus, matrix, Aux In, Main LR** (8): `set_bus_fader`, `set_bus_mute`, `set_matrix_fader`, `set_matrix_mute`, `set_auxin_fader`, `set_auxin_mute`, `set_main_lr_fader`, `set_main_lr_mute`

**DCA** (4): `set_dca_fader`, `set_dca_mute`, `set_dca_name`, `set_dca_color`

**USB output** (3): `setup_usb_output_for_streaming`, `set_card_output_routing`, `set_card_output_level`

**Status queries** (3): `get_channel_status`, `get_all_channels_status`, `get_mixer_snapshot`

**Resources** (8, `x32://...`): `get_fader`, `get_pan`, `get_gain`, `get_mute_status`, `get_phantom_power`, `get_routing`, `get_channel_name`, `get_channel_color`

See `src/x32_mcp/server.py` for the exact arguments.

### Safety: this changes a real mixer

- These tools change the live state of the mixer immediately and do not ask for confirmation. A wrong request can raise a fader on a live PA or send phantom power (+48 V) to a microphone that does not want it. Do not use it with a live audience unless you are watching the mixer yourself.
- Try new requests with the mock server first.
- There is no authentication. Keep the mixer on a trusted network and do not expose the MCP server to the internet.

### Limitations

- The dB-to-level conversion is a piecewise-linear table measured on one X32 (see `src/x32_mcp/conv.py`). Values between the measured points are interpolated, so a fader can be slightly off from the console's own curve.
- Not implemented yet: dynamics (compressor, gate), effects parameters, scenes and snapshots, channel linking, meters, more output sources.
- Some channel reads (name, color) depend on what the X32's OSC interface returns and may not work on every firmware.
- The `http` command (`python -m x32_mcp.server http --host 127.0.0.1 --port 8000`) serves MCP over Streamable HTTP at `/mcp`. It has no authentication, and it was only checked with a single `initialize` request, not with a real client. Keep it on localhost, or use STDIO.
- Tested against the bundled mock server. It has not been through a systematic test on every X32 firmware.
- Unofficial. Not affiliated with or endorsed by Behringer / Music Tribe. "Behringer" and "X32" are trademarks of their owners.

### Troubleshooting

- **The server does not connect:** run `claude mcp list`. Remove and add it again with `claude mcp remove x32-mcp`.
- **The mixer does not answer:** check that the computer and the X32 are on the same network, that `X32_IP` is correct, and that UDP 10023 is not blocked by a firewall.
- **The mock does not start:** another program may already use port 10023 (`netstat -an | findstr 10023` on Windows, `lsof -i :10023` on macOS/Linux).
- **STDIO mode:** never print to stdout in the server code. It would corrupt the MCP stream. Logs go to stderr.

### Development

```bash
mcp dev src/x32_mcp/server.py     # MCP Inspector
```

`EXPANSION_PLAN.md` holds old planning notes in Japanese. They are historical, so rely on this README for the current tool list.

### License

MIT. See [LICENSE](LICENSE). Author: Yuki Tsuruoka ([@mackatwentytsuru](https://github.com/mackatwentytsuru)).

### References

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP](https://github.com/jlowin/fastmcp)
- [python-osc](https://github.com/attwad/python-osc)
- [Unofficial X32 OSC documentation](https://sites.google.com/site/patrickmaillot/x32)

---

## 日本語

Behringer X32 デジタルミキサーを、AI アシスタント(Claude Code・Claude Desktop など MCP に対応したもの)から OSC で動かすための [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) サーバーです。Claude Code で作りました。

アシスタントに「チャンネル1のフェーダーを -3dB にして、名前を Vocal 1 に」と話しかけると、アシスタントがこのサーバーの道具(ツール)を呼び、ミキサーに OSC のメッセージが届きます。

### できること

- 31 個のツール: フェーダー、ミュート、パン、プリアンプのゲイン、ファンタム電源、4バンド EQ、バス送り、バス、マトリクス、Aux In、メイン LR、DCA グループ、出力のルーティング、USB(カード)出力の設定、読み取り専用の状態の問い合わせ
- 読み取り専用の MCP リソース 8 個(フェーダー、パン、ゲイン、ミュート、ファンタム電源、チャンネル名と色、出力ルーティング)
- OSC over UDP(標準のポートは 10023)。python-osc と FastMCP を使用
- `/xremote` を 8 秒ごとに自動で送り、ミキサーとの接続を保つ
- STDIO で動きます(Claude Code・Claude Desktop)。HTTP のコマンドもありますが、[できないこと・気をつけること](#できないこと気をつけること)を見てください
- 実機なしで開発・テストできるモック X32(`scripts/fake_x32.py`)つき
- 送信先の IP とポートは設定で固定。送る前に値の範囲を確かめます

### 必要な物

- Python 3.11 以上
- MCP の Python SDK 1.x(`pip install -e .` で `mcp<2` が入ります。コードが使う `FastMCP` は 2.x で名前が変わったためです)
- Behringer X32 / X32 Rack / M32(または同梱のモック)
- ミキサーへ UDP 10023 番ポートで届くネットワーク

### 入れ方

```bash
git clone https://github.com/mackatwentytsuru/x32-MCP.git
cd x32-MCP
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
```

### ミキサーの宛先を決める

X32 の IP アドレスを環境変数で指定します(初期値の `192.168.1.100` は見本です)。

```bash
export X32_IP=192.168.1.50       # あなたの X32 のアドレス(X32 の Setup > Network で確認)
export X32_PORT=10023            # 省略できます
```

読み込む場所は `src/x32_mcp/config.py` です。

### Claude Code で使う

```bash
# macOS / Linux(ユーザー範囲: すべてのプロジェクトで使える)
claude mcp add x32-mcp --scope user \
  --env X32_IP=192.168.1.50 \
  -- "$(pwd)/.venv/bin/python" -m x32_mcp.server stdio
```

Windows では、コマンドを `.venv\Scripts\python.exe` にしてください。Claude Code を再起動すると、X32 のツールが使えます。

### Claude Desktop で使う

`claude_desktop_config.json`(macOS は `~/Library/Application Support/Claude/`、Windows は `%APPDATA%\Claude\`)に次を足します。

```json
{
  "mcpServers": {
    "x32-mcp": {
      "command": "/path/to/x32-MCP/.venv/bin/python",
      "args": ["-m", "x32_mcp.server", "stdio"],
      "env": { "X32_IP": "192.168.1.50" }
    }
  }
}
```

### ミキサーなしで試す

```bash
# 端末1: モック X32 を起動(UDP 10023 で待ち受けます)
python scripts/fake_x32.py

# 端末2: モックに向けて、テストを動かす
pip install -e ".[dev]"
X32_IP=127.0.0.1 pytest -q       # PowerShell: $env:X32_IP="127.0.0.1"; pytest -q
```

### 話しかけ方の例

| 話しかけ | 呼ばれるツール |
|---|---|
| 「チャンネル1の名前を Vocal 1 にして、色を赤に」 | `set_channel_name(1, "Vocal 1")`, `set_channel_color(1, "RED")` |
| 「チャンネル1のフェーダーを 0dB、パンを中央に」 | `set_fader(1, 0.0)`, `set_pan(1, 0)` |
| 「チャンネル2の EQ で 3kHz を +5dB 持ち上げて」 | `set_eq_enabled(2, true)`, `set_eq_band(2, 2, 3000, 5.0, 1.0)` |
| 「DCA1 に Vocals と名前をつけて -3dB に」 | `set_dca_name(1, "Vocals")`, `set_dca_fader(1, -3.0)` |
| 「メインを USB でパソコンへ送って」 | `setup_usb_output_for_streaming()` |

`setup_usb_output_for_streaming()` は、Main L/R を OUT 5/6 に、そこから USB カード出力 1/2 に回します。配信ソフトが、ミキサーを USB のオーディオ機器として選べるようになります。

### ツール

- チャンネル(10): `set_fader`(-90〜+10 dB)、`set_mute`、`set_pan`(-100〜+100)、`set_channel_name`、`set_channel_color`、`set_channel_icon`、`set_gain`(-12〜+60 dB)、`set_phantom_power`、`set_bus_send`、`route_output`
- EQ(3): `set_eq_enabled`、`set_eq_band`(バンド 1〜4、20〜20000 Hz、-15〜+15 dB、Q 0.3〜10)、`reset_eq`
- バス・マトリクス・Aux In・メイン LR(8): `set_bus_fader`、`set_bus_mute`、`set_matrix_fader`、`set_matrix_mute`、`set_auxin_fader`、`set_auxin_mute`、`set_main_lr_fader`、`set_main_lr_mute`
- DCA(4): `set_dca_fader`、`set_dca_mute`、`set_dca_name`、`set_dca_color`
- USB 出力(3): `setup_usb_output_for_streaming`、`set_card_output_routing`、`set_card_output_level`
- 状態の問い合わせ(3): `get_channel_status`、`get_all_channels_status`、`get_mixer_snapshot`
- リソース(8、`x32://...`): `get_fader`、`get_pan`、`get_gain`、`get_mute_status`、`get_phantom_power`、`get_routing`、`get_channel_name`、`get_channel_color`

引数の細かい決まりは `src/x32_mcp/server.py` を見てください。

### 安全について: 本物のミキサーが動きます

- このツールは、ミキサーの今の状態を、確認なしですぐに変えます。言い方を間違えると、本番の PA でフェーダーが上がったり、ファンタム電源(+48V)を、それを嫌うマイクに送ったりします。お客さんの前では、自分でミキサーを見ていない限り使わないでください。
- 新しい頼み方は、先にモックで試してください。
- 認証はありません。ミキサーは信頼できるネットワークに置き、この MCP サーバーをインターネットに出さないでください。

### できないこと・気をつけること

- dB と値の変換は、X32 1台で測った値の表(区分直線、`src/x32_mcp/conv.py`)です。測った点のあいだは補間なので、卓本来の曲線と少しずれることがあります。
- まだ無いもの: ダイナミクス(コンプレッサー・ゲート)、エフェクトのパラメータ、シーンとスナップショット、チャンネルのリンク、メーター、出力ソースの追加。
- チャンネル名・色の読み取りは、X32 の OSC の返事しだいで、ファームウェアによっては動かないことがあります。
- `http` コマンド(`python -m x32_mcp.server http --host 127.0.0.1 --port 8000`)は、Streamable HTTP で `/mcp` に MCP を出します。認証はなく、確かめたのは `initialize` の1回の要求だけで、実際のクライアントでは試していません。localhost だけで使うか、STDIO を使ってください。
- 動作を確かめたのは同梱のモックです。すべての X32 のファームウェアで、きちんと試したわけではありません。
- 非公式です。Behringer / Music Tribe とは関係なく、承認も受けていません。「Behringer」「X32」は、それぞれの権利者の商標です。

### 困ったとき

- **サーバーにつながらない:** `claude mcp list` で確かめ、`claude mcp remove x32-mcp` で消して、もう一度足します。
- **ミキサーが答えない:** パソコンと X32 が同じネットワークにあるか、`X32_IP` が合っているか、UDP 10023 がファイアウォールで止められていないかを確かめます。
- **モックが起動しない:** 別のプログラムが 10023 番を使っているかもしれません(Windows は `netstat -an | findstr 10023`、macOS/Linux は `lsof -i :10023`)。
- **STDIO のとき:** サーバーのコードから標準出力に書かないでください。MCP の通信が壊れます。ログは標準エラーに出ます。

### 開発

```bash
mcp dev src/x32_mcp/server.py     # MCP Inspector
```

`EXPANSION_PLAN.md` は古い計画のメモです。今のツールの一覧は、この README を見てください。

### ライセンス

MIT です。[LICENSE](LICENSE) を見てください。作者: Yuki Tsuruoka([@mackatwentytsuru](https://github.com/mackatwentytsuru))。

### 参考

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP](https://github.com/jlowin/fastmcp)
- [python-osc](https://github.com/attwad/python-osc)
- [X32 OSC の非公式ドキュメント](https://sites.google.com/site/patrickmaillot/x32)

---

### Author / 作者

Made by Yuki Tsuruoka — stage visuals and live show production, building tools with Claude Code. Web: [otolume.com](https://otolume.com) (OTOLUME, a stage LED visual service) / Instagram: [@tsuru614](https://www.instagram.com/tsuru614/) / YouTube: [channel](https://www.youtube.com/channel/UCYngpwyo7vGBIXBtKhh7z1g)

作者: Yuki Tsuruoka(ステージ映像・ライブ演出。道具は Claude Code で作っています)Web: [otolume.com](https://otolume.com)(OTOLUME、ステージ LED 映像のサービス) / Instagram: [@tsuru614](https://www.instagram.com/tsuru614/) / YouTube: [channel](https://www.youtube.com/channel/UCYngpwyo7vGBIXBtKhh7z1g)