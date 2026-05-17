# Qiita Skills Blog Generator

Claude用Agent Skillsリポジトリ内のすべてのスキルを解析し、初学者向けにわかりやすく解説するQiita技術ブログ記事を自動生成するPythonツール。

## プロジェクト概要

`skills/` ディレクトリ配下の全スキルを走査し、各 `SKILL.md` から YAML フロントマターと Markdown 本文を解析します。スキルを5つのカテゴリ（クリエイティブ&デザイン、開発&技術、ドキュメント処理、エンタープライズ&コミュニケーション、メタスキル）に自動分類し、初学者向けの日本語技術記事として Qiita Markdown 形式で出力します。

記事には以下が含まれます。

- Agent Skills の基本概念と仕組み
- 公式 / ベンダー提供 / 野良 Agent Skills の安全性比較
- 必要な前提ソフトウェア（IDE、CLI、開発環境、外部ツール）
- 各スキルの目的・使用場面・ライセンス情報
- 企業内利用における考慮事項

## インストール方法

### 前提条件

- Python 3.8 以上
- PyYAML（YAMLパーサー）

### セットアップ

リポジトリをクローン後、依存関係をインストールします。

```bash
pip install pyyaml
```

PyYAMLのみが実行時の必須依存です。標準ライブラリ（pathlib、logging、json、argparse、re、dataclasses）以外の依存はありません。

## 使用方法

### コマンドラインからの実行

リポジトリのルートで以下のコマンドを実行します。

```bash
# デフォルト設定で実行（skills/ を解析し、output/ に記事を出力）
python -m qiita_skills_blog_generator.main

# カスタム設定ファイルを指定
python -m qiita_skills_blog_generator.main --config config.json

# 既存ファイルを確認なしで上書き（CI などの非対話実行向け）
python -m qiita_skills_blog_generator.main --force

# ヘルプを表示
python -m qiita_skills_blog_generator.main --help
```

終了コードは `0`（成功） / `1`（処理中にエラーが発生 or 予期しない例外）です。

### Python API からの実行

```python
from pathlib import Path
from qiita_skills_blog_generator.controller import MainController

# デフォルト設定で実行
controller = MainController()
result = controller.run()

# カスタム設定で実行
controller = MainController(config_path=Path("config.json"))
result = controller.run(force=True)

print(f"成功: {result.success_count} / スキップ: {result.skip_count} / エラー: {result.error_count}")
```

## 設定ファイルの説明

JSON 形式の設定ファイルで、出力先や記事の挙動をカスタマイズできます。リポジトリ同梱の `config.example.json` を雛形として利用してください。

### 設定項目

| キー | 型 | デフォルト値 | 説明 |
| --- | --- | --- | --- |
| `skills_directory` | string | `"skills"` | スキルを走査するディレクトリパス |
| `output_directory` | string | `"output"` | 記事の出力先ディレクトリパス |
| `article_title` | string | `"Claude Agent Skills完全ガイド：初学者のための実践的スキル解説"` | 記事のH1タイトル |
| `target_audience` | string | `"初学者"` | 対象読者（`"初学者"` / `"中級者"` / `"上級者"`） |
| `max_skill_description_length` | int | `400` | 各スキル説明の最大文字数 |
| `included_categories` | string[] | 全5カテゴリ | 記事に含めるカテゴリ |
| `log_level` | string | `"INFO"` | ログレベル（`DEBUG`/`INFO`/`WARNING`/`ERROR`） |
| `log_file` | string | `"logs/qiita_generator.log"` | ログ出力先 |

### 設定例

```json
{
  "skills_directory": "skills",
  "output_directory": "output",
  "article_title": "Claude Agent Skills完全ガイド：初学者のための実践的スキル解説",
  "target_audience": "初学者",
  "max_skill_description_length": 400,
  "included_categories": [
    "クリエイティブ&デザイン",
    "開発&技術",
    "ドキュメント処理",
    "エンタープライズ&コミュニケーション",
    "メタスキル"
  ],
  "log_level": "INFO",
  "log_file": "logs/qiita_generator.log"
}
```

設定ファイルが存在しない、または JSON 形式が不正な場合は警告を出してデフォルト設定で続行します。

## プロジェクト構造

```
qiita_skills_blog_generator/
├── __init__.py            # パッケージ初期化
├── main.py                # CLIエントリーポイント
├── controller.py          # MainController（全体制御、品質検証、ファイル保存）
├── skill_analyzer.py      # SkillAnalyzer（SKILL.md解析）
├── content_generator.py   # ContentGenerator（コンテンツ生成、カテゴリ分類）
├── markdown_formatter.py  # MarkdownFormatter（Qiita形式整形）
├── logger.py              # Logger（実行ログ）
├── config.py              # Config / SkillData / ProcessingResultデータクラス
├── constants.py           # カテゴリマッピング、品質基準などの定数
├── utils.py               # ユーティリティ関数
├── test_*.py              # 各コンポーネントのユニットテスト
└── README.md              # このファイル
```

## 出力例

### 出力ファイル

`output/<YYYY-MM-DD>_<slug>.md` の形式で、UTF-8 エンコーディングで保存されます。

```
output/2026-05-17_Claude-Agent-Skills完全ガイド-初学者のための実践的スキル解説.md
```

同名ファイルが既に存在する場合の挙動：

- `--force` 指定時 : 確認なしで上書き
- 対話モード（TTY） : `[y/N]` で確認
- 非対話モード : 連番付き別名で保存（例：`..._1.md`）

### 記事構造

生成される記事は次の構造を持ちます。

```markdown
# <article_title>

## 目次

## はじめに
## Agent Skillsとは
## Agent Skillsの安全性とリスク
### 公式Agent Skills
### ベンダー提供Agent Skills
### 野良Agent Skills
### 企業内での安全性判断基準
### 本記事で扱うAnthropicの公式Agent Skillsについて
## Agent Skillsを利用・開発するための前提ソフトウェア
### Agent Skillsを利用できるIDE（統合開発環境）
### Agent Skillsを利用できるCLI（コマンドラインインターフェース）
### Agent Skillsを構築するための開発環境
### パッケージリポジトリとライブラリ管理
### ドキュメント処理系スキルに必要な外部ツール
### スキルカテゴリごとの依存関係
### 企業内利用における考慮事項
## スキル一覧
### ライセンスについて
### クリエイティブ&デザイン
#### algorithmic-art
#### canvas-design
...
## まとめ
```

### 品質基準

`MainController.validate_output()` が以下を自動検証します。基準を満たさない場合は警告がログに記録されますが、ファイルは保存されます。

- 記事の文字数が 5000 文字以上（要件8.1）
- すべてのカテゴリが含まれている（要件8.2）
- 各スキル（H4見出し）の説明が空でない（要件8.3）
- Markdown 記法が正しい（H1の数、コードフェンスのペア、見出しの空白など、要件8.4）
- 安全性セクションと前提ソフトウェアセクションが存在（要件8.6, 8.7）
- 見出しの階層構造が適切（要件8.9）

## ログ

実行ログは `log_file` で指定された場所と標準エラーに出力されます。デフォルトは `logs/qiita_generator.log`。

ログには次の情報が含まれます。

- 処理開始 / 終了時刻
- 使用された設定内容
- 各スキルの処理状況（成功 / スキップ / エラー）
- エラー詳細（事象、場所、原因、対処方法）
- 出力ファイルパス
- 集計（成功数 / スキップ数 / エラー数）

## テスト

ユニットテストはプロジェクトルートから次のコマンドで実行します。

```bash
python -m unittest discover -t . -s qiita_skills_blog_generator -p "test_*.py"
```

`-t .` でトップレベルディレクトリを指定すると、パッケージ相対 import が解決されます。

## トラブルシューティング

### 「スキルディレクトリが存在しません」と出て処理が中止される

`skills_directory`（デフォルト `skills`）の指す場所が存在しません。設定の `skills_directory` を確認するか、リポジトリのルートで実行してください。

### 「SKILL.mdファイルが見つかりませんでした」と警告が出る

`skills_directory` 配下のサブディレクトリに `SKILL.md` がありません。各スキルディレクトリ直下に `SKILL.md` を配置してください。

### 「YAMLフロントマターの解析に失敗しました」エラー

`SKILL.md` 冒頭の `---` で囲まれた YAML ブロックの構文に問題があります。インデント、リスト記法（`[ ]`）、コロンの位置などを見直してください。問題のあるスキルはスキップされ、残りのスキルで記事生成は続行されます。

### 「必須フィールド'name'/'description'が欠けているか空です」警告

YAML フロントマターに `name` または `description` がありません。両方とも必須なので追加してください。問題のあるスキルはスキップされます。

### コマンドが応答しなくなる（既存の出力ファイル上書き確認待ち）

対話モードで実行中、既存の出力ファイルがあると `[y/N]` の応答を待ち続けます。次のいずれかで回避してください。

- `--force` を付けて実行する
- 既存ファイルを削除または別の場所に移動する
- 標準入力から `n` を入力して別名保存させる

### 「PyYAMLがインストールされていません」エラー

`pip install pyyaml` で PyYAML をインストールしてください。

### 出力記事の文字数が足りないと警告される

`MIN_ARTICLE_LENGTH`（5000文字）を下回ると警告が出ます。スキル数が極端に少ないか、`included_categories` で大半のカテゴリを除外している可能性があります。

### 設定ファイルが反映されない

JSON のキー名のタイポに注意してください。不正なキーや型の不一致があるとデフォルト設定にフォールバックし、警告が `stderr` に出力されます。

## 要件との対応

実装は `.kiro/specs/qiita-skills-blog-generator/` の要件・設計ドキュメントに準拠しています。詳細は同ディレクトリの `requirements.md` と `design.md` を参照してください。

## ライセンス

このツール自体は本リポジトリのライセンスに従います。生成される記事に含まれる各スキルのライセンス情報は、対象スキルの `LICENSE.txt` に基づきます。
