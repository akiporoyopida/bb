# Claude Code Usage Viewer

Claude Code の使用実績をターミナルで視覚的に表示するPythonツール。`ccusage blocks --json` の出力を解析し、日別のタイムラインをアスキーアートで表現します。

## 特徴

- 📊 **タイムライン表示**: 24時間のタイムラインを48文字のアスキーアートで表現
- 🎨 **カラー表示**: モデルバージョンごとに色分け表示（Sonnet-4.5=シアン、4.0=青、3.5=マゼンタなど）
- 📈 **統計情報**: 総使用時間、コスト、トークン数などの統計
- 🔍 **フィルタリング**: 高使用日、高コスト日のみ表示
- 📋 **ソート機能**: コスト順、使用時間順でのソート
- 🚀 **リアルタイム情報**: 現在のセッション状態を1行で表示
- 🤖 **新モデル自動対応**: 将来の新しいClaudeモデルを自動認識・表示
- 🔍 **未知のモデル検出**: 未知のモデルが使用された場合、凡例に自動表示

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/akiporoyopida/bb.git
cd bb

# 実行権限を付与
chmod +x b.py

# オプション: PATHに追加
cp b.py ~/bin/
# または
sudo cp b.py /usr/local/bin/
```

## 必要な環境

- Python 3.6以上
- [CC Usage](https://github.com/Aider-AI/aider) (Claude Code使用状況を取得するため)

## 使用方法

### 基本的な使用

```bash
# ccusageから直接パイプで入力
ccusage blocks --json | python3 b.py

# JSONファイルから読み込み
python3 b.py < blocks.json

# ファイルを指定
python3 b.py --file blocks.json
```

# 実行例
```bash
ccusage blocks --live --json | python3 claude_code_viewer.py --current
```

# アクティブな場合の出力例
```bash
● opus-4      $ 16.79       6,779,420/ 58,679,737    [ 11.6%] → 74.3% ($109.38) リセット: 15:00 (3h24m)
 [62エントリー] バーンレート: 183,414 tokens/分, $27.25/時間
```

# 非アクティブな場合の出力例  
```bash
○ opus-4      $  0.00               0/ 58,679,737    [  0.0%] リセット: 15:00 (3h24m) [0エントリー]
```

### 現在のセッション情報

```bash
# 現在の使用状況を1行で表示
ccusage blocks --json | python3 b.py --current

# 出力例:
# opus-4      $ 45.67      23,456,789/ 58,679,737    [ 40.0%] リセット: 15:00 (2h35m) [3セッション]
```

### フィルタリング

```bash
# 高使用日のみ表示（5時間以上）
ccusage blocks --json | python3 b.py --high-usage

# 高コスト日のみ表示（$50以上）
ccusage blocks --json | python3 b.py --high-cost
```

### ソートと表示制限

```bash
# コスト順で上位10日を表示
ccusage blocks --json | python3 b.py --sort-cost --limit 10

# 使用時間順で上位5日を表示
ccusage blocks --json | python3 b.py --sort-duration --limit 5
```

### 詳細情報

```bash
# 特定日の詳細を表示
ccusage blocks --json | python3 b.py --date 2025-09-13

# モデル別の統計を表示
ccusage blocks --json | python3 b.py --model-summary

# 統計情報のみ表示
ccusage blocks --json | python3 b.py --summary
```

### その他のオプション

```bash
# カラー表示を無効化（パイプやファイル出力用）
ccusage blocks --json | python3 b.py --no-color > report.txt

# 凡例を非表示
ccusage blocks --json | python3 b.py --no-legend

# ヘルプを表示
python3 b.py -h
```

## タイムラインの見方

```
日付        曜日  ブロック  時間     タイムライン (00:00 ━━━━━━━━━━━━━━━━━━━━━━━━ 24:00)
2025-09-13  (金)   6ブロック  10h48m  |░░··········|████████████|█████···|░░░░░······|
```

### 凡例

#### モデル別の文字と色
- `█` = **Opus** (赤系)
  - 🔴 Opus-4.x (赤)
  - 🟡 Opus-3.x (黄)
- `▓` = **Sonnet** (青/シアン系)
  - 🔵 Sonnet-4.5 (シアン)
  - 🔵 Sonnet-4.0 (青)
  - 🟣 Sonnet-3.5 (マゼンタ)
- `▪` = **Haiku** (緑)
  - 🟢 Haiku-4.x / 3.x (緑)
- `░` = **Synthetic** (グレー)
- `▒` = **複数モデル使用** (黄)
- `◆` = **未知のモデル** (白) - 新しいモデルが使用された場合に表示
- `·` = 使用なし
- `|` = 6時間マーカー（0, 6, 12, 18時）

#### コストの色分け
- 🟢 **緑**: コスト $20未満
- 🟡 **黄**: コスト $20-50
- 🔴 **赤**: コスト $50以上

## 実行例

### 日別タイムライン表示
```bash
$ ccusage blocks --json | python3 b.py

==================================================================================================
Claude Code 使用実績タイムライン
2025-08-21 - 2025-09-24
==================================================================================================

統計情報:
  総使用時間: 163時間48分
  総コスト: $1787.28
  総トークン数: 586,797,370
  総エントリー数: 7,416
  総ブロック数: 65
  使用日数: 31日
  平均ブロック時間: 151.9分
  1日平均コスト: $57.65

凡例:
  █ = Opus (赤系)
    █ Opus-4.x
    █ Opus-3.x
  ▓ = Sonnet (青/シアン系)
    ▓ Sonnet-4.5
    ▓ Sonnet-4.0
    ▓ Sonnet-3.5
  ▪ = Haiku (緑)
  ░ = Synthetic
  ▒ = 複数モデル使用
  · = 使用なし
  | = 6時間マーカー (0, 6, 12, 18時)

日付        曜日  ブロック  時間     タイムライン (00:00 ━━━━━━━━━━━━━━━━━━━━━━━━ 24:00)  トークン数        コスト
────────────────────────────────────────────────────────────────────────────────────────────────────
2025-08-21  (水)   2ブロック   3h10m  |····························█████··········|···      28,920,804  $ 66.79
2025-08-23  (金)   4ブロック   9h35m  |██········|·····▒▒▒▒▒▒▒▒▒▒▒▒|▒▒▒▒▒▒▒·····|···      77,141,523  $169.22
...
```

### 現在の使用状況
```bash
$ ccusage blocks --json | python3 b.py --current
opus-4      $127.27      58,679,737/ 58,679,737    [100.0%] リセット: 05:00 (1h15m) [1セッション]
```

## エイリアスの設定

よく使うコマンドは、シェルのエイリアスに設定すると便利です：

```bash
# ~/.zshrc または ~/.bashrc に追加
alias ccv='ccusage blocks --json | python3 ~/path/to/b.py'
alias ccv-current='ccv --current'
alias ccv-cost='ccv --sort-cost --limit 10'
alias ccv-today='ccv --date $(date +%Y-%m-%d)'
```

## トラブルシューティング

### `ccusage: command not found`
CC Usageがインストールされていません。[インストール手順](https://github.com/Aider-AI/aider)を参照してください。

### 文字化けする場合
```bash
# ロケールを設定
export LANG=ja_JP.UTF-8
export LC_ALL=ja_JP.UTF-8
```

### カラー表示されない場合
```bash
# ターミナルが256色対応か確認
tput colors

# 強制的にカラー表示を有効化
export TERM=xterm-256color
```

## 更新履歴

### v2.0.0 (2025-10-01)
- 🎨 **モデルバージョン別の色分け対応**
  - Sonnet-4.5 (シアン)、Sonnet-4.0 (青)、Sonnet-3.5 (マゼンタ) を自動識別
  - Opus、Haikuも同様にバージョン別に色分け
- 🤖 **新モデル自動認識機能**
  - 正規表現ベースのモデル名解析により、将来の新しいモデルを自動認識
  - 例: `claude-sonnet-4-5-20250929` → `sonnet-4.5` として自動解析
- 🔍 **未知のモデル検出機能**
  - 未知のモデルが使用された場合、凡例に具体的なモデル名を自動表示
  - 既知のモデルのみの場合は、凡例に表示されない
- 📝 **凡例の動的表示**
  - 実際に使用されたモデルに応じて凡例を動的に生成

### v1.0.0 (初回リリース)
- 基本的なタイムライン表示機能
- 統計情報、フィルタリング、ソート機能
- 現在のセッション情報表示

## ライセンス

MIT License

## 関連プロジェクト

- [CC Usage](https://github.com/Aider-AI/aider) - Claude Code使用状況トラッキングツール
- [Claude](https://www.anthropic.com/claude) - Anthropic社のAIアシスタント
