---
inclusion: always
---

# 技術スタック

## コア技術

これは主にドキュメントとリソースのリポジトリです。スキルは言語に依存しないMarkdownファイルで、オプションでバンドルされたリソースを含みます。

### スキルフォーマット

- **SKILL.md**: YAMLフロントマターを含むMarkdownファイル
- **フロントマターフィールド**: `name`（必須）、`description`（必須）、`license`（オプション）、`compatibility`（オプション）
- **コンテンツ**: Markdown形式の指示、例、ガイドライン

### バンドルリソース（オプション）

スキルには以下を含めることができます：
- **scripts/**: 決定論的タスク用のPython、JavaScript、またはシェルスクリプト
- **references/**: 必要に応じてコンテキストに読み込まれるドキュメント
- **assets/**: 出力で使用されるテンプレート、フォント、画像
- **templates/**: 再利用可能なファイルテンプレート

## 言語固有の依存関係

### Pythonスキル

一般的な依存関係：
- **python-docx**: Word文書の操作
- **pandoc**: ドキュメント変換とテキスト抽出
- **LibreOffice**: PDF変換（`soffice`コマンド経由）
- **Poppler**: PDFユーティリティ（`pdftoppm`）

### JavaScript/Nodeスキル

一般的な依存関係：
- **docx**: Word文書生成（`npm install -g docx`）
- **p5.js**: クリエイティブコーディング（HTMLアーティファクトでCDN経由で読み込み）

### MCP開発

- **TypeScript**（推奨）: MCP SDK、スキーマ用Zod
- **Python**: FastMCP、スキーマ用Pydantic

## 一般的なコマンド

### スキルテスト

```bash
# Claude Codeでスキルをテスト
/plugin install <skill-name>@anthropic-agent-skills

# MCP Inspector でテスト（MCPサーバー用）
npx @modelcontextprotocol/inspector
```

### ドキュメント処理

```bash
# .docから.docxに変換
python scripts/office/soffice.py --headless --convert-to docx document.doc

# Word文書からテキストを抽出
pandoc --track-changes=all document.docx -o output.md

# Word文書を検証
python scripts/office/validate.py doc.docx

# 編集用にWord文書を展開
python scripts/office/unpack.py document.docx unpacked/

# 編集後にWord文書を再パック
python scripts/office/pack.py unpacked/ output.docx --original document.docx
```

### スキル開発

```bash
# 配布用にスキルをパッケージ化
python -m scripts.package_skill <path/to/skill-folder>
```

## ファイル形式

- **スキル**: `.skill`（パッケージ化）または`SKILL.md`を含むフォルダ
- **ドキュメント**: `.docx`、`.pdf`、`.pptx`、`.xlsx`
- **アーティファクト**: 埋め込みリソースを含む自己完結型HTMLファイル
- **評価**: JSONまたはXML形式

## ビルドシステムなし

このリポジトリにはビルドシステム、package.json、コンパイルステップはありません。スキルはClaudeによってMarkdownファイルとして直接消費されます。
