> Historical planning notes (written early in the project). Many items below are already implemented. See README.md for the current tool list.
> 初期の計画メモです。多くはすでに実装済みです。今のツールの一覧は README.md を見てください。

# X32 MCP 拡張可能な機能リスト

## 現在実装済みのツール

### Tools（操作）
1. `set_fader` - チャンネルフェーダーレベル設定
2. `set_mute` - チャンネルミュート設定
3. `set_bus_send` - バス送りレベル設定
4. `route_output` - メイン出力ルーティング設定

### Resources（取得）
1. `get_fader` - チャンネルフェーダーレベル取得
2. `get_routing` - メイン出力ルーティング取得

---

## 追加可能な機能（優先度順）

### 【高優先度】基本的なチャンネル操作

#### 1. チャンネル設定
- **`set_channel_name`** - チャンネル名設定
  - `/ch/{01-32}/config/name`
  - 例: "Vocal 1", "Guitar", "Drums"

- **`get_channel_name`** - チャンネル名取得
  - `/ch/{01-32}/config/name`

- **`set_pan`** - パン（左右バランス）設定
  - `/ch/{01-32}/mix/pan`
  - 値: 0.0（左） 〜 0.5（中央） 〜 1.0（右）

- **`get_pan`** - パン取得
  - `/ch/{01-32}/mix/pan`

#### 2. EQ制御
- **`set_eq`** - イコライザー設定
  - `/ch/{01-32}/eq/{1-4}/g` - ゲイン（-15.0 〜 +15.0 dB）
  - `/ch/{01-32}/eq/{1-4}/f` - 周波数
  - `/ch/{01-32}/eq/{1-4}/q` - Q値（バンド幅）
  - `/ch/{01-32}/eq/on` - EQ ON/OFF

- **`get_eq`** - EQ設定取得

#### 3. ダイナミクス（コンプレッサー/ゲート）
- **`set_compressor`** - コンプレッサー設定
  - `/ch/{01-32}/dyn/comp/thr` - スレッショルド
  - `/ch/{01-32}/dyn/comp/ratio` - レシオ
  - `/ch/{01-32}/dyn/comp/attack` - アタック
  - `/ch/{01-32}/dyn/comp/release` - リリース
  - `/ch/{01-32}/dyn/on` - Dynamics ON/OFF

- **`set_gate`** - ゲート設定
  - `/ch/{01-32}/dyn/gate/thr` - スレッショルド
  - `/ch/{01-32}/dyn/gate/attack` - アタック
  - `/ch/{01-32}/dyn/gate/release` - リリース

### 【中優先度】ミックスバス・AUX制御

#### 4. MixBus（Aux）操作
- **`set_bus_fader`** - バスフェーダー設定
  - `/bus/{01-16}/mix/fader`

- **`set_bus_mute`** - バスミュート設定
  - `/bus/{01-16}/mix/on`

- **`get_bus_fader`** - バスフェーダー取得

#### 5. AuxIn（外部入力）操作
- **`set_auxin_fader`** - AuxIn フェーダー設定
  - `/auxin/{01-08}/mix/fader`

- **`set_auxin_mute`** - AuxIn ミュート設定
  - `/auxin/{01-08}/mix/on`

#### 6. Matrix出力
- **`set_matrix_fader`** - Matrix フェーダー設定
  - `/mtx/{01-06}/mix/fader`

- **`set_matrix_mute`** - Matrix ミュート設定
  - `/mtx/{01-06}/mix/on`

### 【中優先度】グループ制御

#### 7. DCA（Digital Controlled Amplifier）グループ
- **`set_dca_fader`** - DCAグループフェーダー設定
  - `/dca/{1-8}/fader`

- **`set_dca_mute`** - DCAグループミュート設定
  - `/dca/{1-8}/on`

- **`set_dca_name`** - DCAグループ名設定
  - `/dca/{1-8}/config/name`

#### 8. Mute Group（ミュートグループ）
- **`set_mute_group`** - ミュートグループ制御
  - `/config/mute/{1-6}` - グループミュート ON/OFF

### 【中優先度】エフェクト制御

#### 9. Effects（FX）
- **`set_fx_param`** - エフェクトパラメータ設定
  - `/fx/{1-8}/par/{01-64}` - パラメータ値

- **`set_fx_type`** - エフェクトタイプ設定
  - `/fx/{1-8}/type` - エフェクトタイプ選択

- **`get_fx_param`** - エフェクトパラメータ取得

### 【低優先度】シーン管理

#### 10. Scene/Snapshot
- **`load_scene`** - シーン読み込み
  - `/scene/load` または `/-snap/load`

- **`save_scene`** - シーン保存
  - `/scene/save` または `/-snap/save`

- **`get_current_scene`** - 現在のシーン取得
  - `/-snap/index`

### 【低優先度】メーター・モニタリング

#### 11. Meters（メーター値取得）
- **`get_meters`** - 各チャンネルのレベルメーター取得
  - `/meters/1` 〜 `/meters/15` - メーターバンク

- **`get_channel_level`** - チャンネルの現在のオーディオレベル取得

### 【低優先度】グローバル設定

#### 12. Main LR（メインステレオ出力）
- **`set_main_fader`** - メインLRフェーダー設定
  - `/main/st/mix/fader`

- **`set_main_mute`** - メインLRミュート設定
  - `/main/st/mix/on`

#### 13. ヘッドフォン・モニター
- **`set_headphone_source`** - ヘッドフォンソース選択
  - `/config/solo/source`

---

## 推奨実装順序

### Phase 1: 基本チャンネル拡張（すぐに役立つ）
1. `set_channel_name` / `get_channel_name` - チャンネル識別に必須
2. `set_pan` / `get_pan` - ステレオバランス調整
3. `set_main_fader` / `set_main_mute` - メイン出力制御

### Phase 2: 音質調整（プロユース）
4. `set_eq` - 4バンドEQ制御
5. `set_compressor` - ダイナミクス処理
6. `set_gate` - ノイズゲート

### Phase 3: 複雑なミックス（高度な操作）
7. DCAグループ制御
8. MixBus/Matrix拡張
9. エフェクト制御

### Phase 4: ワークフロー効率化
10. シーン管理
11. メーター取得
12. ミュートグループ

---

## 実装時の注意点

1. **データ型変換**
   - `level`型（0.0-1.0）: フェーダー、センドレベル
   - `db`型: 既存の`db_to_level`/`level_to_db`関数を使用
   - `freq`型: 周波数（Hz）
   - `time`型: 時間（ms）
   - `enum`型: 整数コード（マッピング必要）

2. **バリデーション**
   - すべてのパラメータ範囲チェック
   - 無効な値の明示的なエラーメッセージ

3. **ドキュメント**
   - 各ツールに日本語の説明
   - 実用的な使用例

4. **テスト**
   - 実機での動作確認
   - モックX32への対応追加