# 要件ドキュメント

## はじめに

このドキュメントは、Claude用Agent Skillsリポジトリ内のすべてのスキルを解析し、初学者向けにわかりやすく解説するQiita技術ブログ記事を自動生成する機能の要件を定義します。

本機能は、skills/ディレクトリ配下の全スキル（クリエイティブ&デザイン、開発&技術、ドキュメント処理、エンタープライズ&コミュニケーション、メタスキル）を対象とし、各スキルの目的、使用方法、技術的特徴を体系的に整理した日本語の技術記事を生成します。

## 用語集

- **System**: Qiita技術ブログ生成システム全体
- **Skill_Analyzer**: スキルのSKILL.mdファイルを解析するコンポーネント
- **Content_Generator**: 解析結果から記事コンテンツを生成するコンポーネント
- **Markdown_Formatter**: Qiita形式のMarkdownを整形するコンポーネント
- **SKILL.md**: 各スキルの定義ファイル（YAMLフロントマター + Markdown本文）
- **YAMLフロントマター**: SKILL.mdの先頭にあるメタデータ（name、description、license等）
- **バンドルリソース**: スキルに含まれるscripts/、references/、assets/、templates/等のディレクトリ
- **初学者**: Agent Skillsの概念や使い方を初めて学ぶ読者
- **公式Agent Skills**: Anthropic、OpenAI、Googleなどのビッグテック企業が公開・メンテナンスするAgent Skills
- **ベンダー提供Agent Skills**: Microsoft、MySQL、AWSなどのプロダクトベンダーが自社製品向けに開発・公開するAgent Skills
- **野良Agent Skills**: インターネット上で個人や非公式な組織が公開しているAgent Skills（出所や品質が不明確）
- **IDE（統合開発環境）**: Agent Skillsを利用できる開発環境（VSCode、Kiro等）
- **CLI（コマンドラインインターフェース）**: コマンドラインからAgent Skillsを利用できるツール（Claude Code、Codex、Gemini CLI、Kiro CLI等）
- **開発環境**: Agent Skillsを構築するために必要なランタイム環境（Node.js、Python等）
- **パッケージリポジトリ**: 開発に必要なライブラリを提供するリポジトリ（npm、PyPI、uv等）
- **ドキュメント処理ツール**: 特定のAgent Skillsが依存する外部ソフトウェア（LibreOffice、Pandoc、Poppler等）

## 要件

### 要件1: スキル情報の収集

**ユーザーストーリー:** 開発者として、リポジトリ内のすべてのスキルを自動的に発見し、その基本情報を収集したい。これにより、手動でスキルを探す手間を省き、網羅的な記事を作成できる。

#### 受入基準

1. THE Skill_Analyzer SHALL skills/ディレクトリ配下のすべてのサブディレクトリを走査する
2. WHEN SKILL.mdファイルが見つかったとき、THE Skill_Analyzer SHALL そのファイルを読み込む
3. THE Skill_Analyzer SHALL YAMLフロントマターからname、description、licenseフィールドを抽出する
4. THE Skill_Analyzer SHALL Markdown本文の構造（見出し、セクション）を解析する
5. WHERE バンドルリソースディレクトリ（scripts/、references/、assets/、templates/）が存在する場合、THE Skill_Analyzer SHALL それらの存在を記録する
6. THE Skill_Analyzer SHALL 各スキルの情報を構造化データとして保存する

### 要件2: スキルのカテゴリ分類

**ユーザーストーリー:** 読者として、スキルがカテゴリごとに整理されていることで、自分の興味のある分野のスキルを素早く見つけたい。

#### 受入基準

1. THE System SHALL スキルを以下のカテゴリに分類する：
   - クリエイティブ&デザイン（algorithmic-art、canvas-design、frontend-design、theme-factory）
   - 開発&技術（claude-api、mcp-builder、webapp-testing、web-artifacts-builder）
   - ドキュメント処理（docx、pdf、pptx、xlsx）
   - エンタープライズ&コミュニケーション（brand-guidelines、doc-coauthoring、internal-comms、slack-gif-creator）
   - メタスキル（skill-creator）
2. WHEN スキルが複数のカテゴリに該当する可能性があるとき、THE System SHALL 主要な用途に基づいて1つのカテゴリに分類する
3. THE System SHALL 各カテゴリ内でスキルをアルファベット順にソートする

### 要件3: 初学者向けコンテンツの生成

**ユーザーストーリー:** 初学者として、技術的な詳細だけでなく、「なぜこのスキルが必要なのか」「どんな場面で使うのか」を理解したい。また、企業内でAgent Skillsを利用する際の安全性とリスク、必要な前提ソフトウェアとエコシステムについても理解し、適切な判断ができるようになりたい。

#### 受入基準

1. THE Content_Generator SHALL 各スキルについて以下の情報を含む説明を生成する：
   - スキルの目的（何ができるか）
   - 使用場面（どんなときに使うか）
   - 主要な機能
   - 技術的な特徴
2. THE Content_Generator SHALL 専門用語を使用する際は、初学者向けの補足説明を追加する
3. THE Content_Generator SHALL 具体的な使用例やユースケースを含める
4. THE Content_Generator SHALL 各スキルの説明を200〜400文字程度にまとめる
5. THE Content_Generator SHALL 技術的な正確性を保ちながら、平易な日本語で記述する
6. THE Content_Generator SHALL Agent Skillsの安全性に関するセクションを生成し、以下の内容を含める：
   - 公式Agent Skills（Anthropic/OpenAI/Google等のビッグテック提供）の定義と安全性の特徴
   - ベンダー提供Agent Skills（Microsoft/MySQL等のプロダクトベンダー提供）の定義と安全性の特徴
   - 野良Agent Skills（インターネット上の非公式なもの）の定義とリスク
   - 企業内で利用する際の安全性判断基準
   - 今回解説するAnthropicの公式Agent Skillsが信頼できる理由
7. THE Content_Generator SHALL 安全性に関する説明において、以下の観点を含める：
   - コードレビューとセキュリティ監査の有無
   - ライセンスと法的保護
   - メンテナンスとサポート体制
   - データプライバシーとセキュリティ
   - 悪意のあるコード混入のリスク
8. THE Content_Generator SHALL Agent Skillsを利用・開発するための前提ソフトウェアに関するセクションを生成し、以下の内容を含める：
   - Agent Skillsを利用できるIDE（VSCode、Kiro等）の紹介と特徴
   - Agent Skillsを利用できるCLI（Claude Code、Codex、Gemini CLI、Kiro CLI等）の紹介と特徴
   - Agent Skillsを構築するための開発環境（Node.js、Python等）の説明
   - 開発に必要なパッケージリポジトリ（npm、PyPI、uv等）の説明
   - ドキュメント処理系スキル（docx、pdf、pptx、xlsx）に必要な外部ツール（LibreOffice、Pandoc、Poppler等）の説明
   - 各スキルカテゴリごとの依存関係と必要なソフトウェアの一覧
   - 各ツールやリポジトリの企業内利用における考慮事項（セキュリティ、ライセンス、プライベートリポジトリの利用等）
9. THE Content_Generator SHALL 前提ソフトウェアの説明において、以下の観点を含める：
   - 各ツールの公式性と信頼性
   - 企業内ネットワークでの利用可否
   - プロキシやファイアウォール設定の必要性
   - オフライン環境での利用可能性
   - ライセンスコストの有無
   - ドキュメント処理系スキルの具体的な依存関係：
     * Python依存: python-docx、pandoc、LibreOffice（sofficeコマンド）、Poppler（pdftoppm）
     * JavaScript/Node依存: docx（npm）、p5.js（CDN経由）
     * MCP開発依存: TypeScript（MCP SDK、Zod）、Python（FastMCP、Pydantic）
10. THE Content_Generator SHALL 今回のブログがAnthropicの公式Agent Skillsを扱うことを明確に記載する

### 要件4: Qiita形式のMarkdown生成

**ユーザーストーリー:** ブログ執筆者として、Qiitaにそのまま投稿できる形式のMarkdownファイルが欲しい。また、初学者として、記事の見出しが理解しやすく、ストーリー性のある流れで構成されていることで、内容を順を追って学習できるようにしたい。

#### 受入基準

1. THE Markdown_Formatter SHALL Qiita Markdownの記法に準拠した記事を生成する
2. THE Markdown_Formatter SHALL 以下の構造を持つ記事を生成する：
   - タイトル（H1）
   - はじめに（H2）
   - Agent Skillsとは（H2）
   - Agent Skillsの安全性とリスク（H2）
     - 公式Agent Skills（H3）
     - ベンダー提供Agent Skills（H3）
     - 野良Agent Skills（H3）
     - 企業内での安全性判断基準（H3）
     - 本記事で扱うAnthropicの公式Agent Skillsについて（H3）
   - Agent Skillsを利用・開発するための前提ソフトウェア（H2）
     - Agent Skillsを利用できるIDE（H3）
     - Agent Skillsを利用できるCLI（H3）
     - Agent Skillsを構築するための開発環境（H3）
     - パッケージリポジトリとライブラリ管理（H3）
     - ドキュメント処理系スキルに必要な外部ツール（H3）
     - スキルカテゴリごとの依存関係（H3）
     - 企業内利用における考慮事項（H3）
   - スキル一覧（H2）
     - 各カテゴリ（H3）
       - 各スキル（H4）
   - まとめ（H2）
3. THE Markdown_Formatter SHALL コードブロックを使用する場合は、適切な言語指定を行う
4. THE Markdown_Formatter SHALL 箇条書きや番号付きリストを適切に使用する
5. THE Markdown_Formatter SHALL 記事の冒頭に目次を自動生成する
6. THE Markdown_Formatter SHALL 各見出しを初学者が理解しやすい表現にする：
   - 専門用語だけでなく、具体的な内容を示す補足を含める
   - 読者の疑問に答える形式の見出しを使用する（例：「なぜAgent Skillsが必要なのか」「どうやって始めるのか」）
   - 学習の流れに沿った順序で見出しを配置する（基礎概念 → 安全性 → 環境構築 → 実践）
7. THE Markdown_Formatter SHALL 見出しの階層構造を適切に保ち、論理的な流れを維持する
8. THE Markdown_Formatter SHALL 各セクション間の繋がりを意識した見出しを作成する

### 要件5: ライセンス情報の明記

**ユーザーストーリー:** 読者として、各スキルのライセンス情報を知ることで、自分のプロジェクトで使用できるかを判断したい。

#### 受入基準

1. WHEN スキルにlicenseフィールドが存在するとき、THE System SHALL そのライセンス情報を記事に含める
2. THE System SHALL Apache 2.0ライセンスのスキルとプロプライエタリライセンスのスキルを区別して表示する
3. THE System SHALL ドキュメントスキル（docx、pdf、pptx、xlsx）がソース公開だがプロプライエタリであることを明記する
4. THE System SHALL 各スキルの説明にライセンス種別を簡潔に記載する

### 要件6: 記事の出力と保存

**ユーザーストーリー:** システム利用者として、生成された記事を指定した場所に保存し、後で編集や投稿ができるようにしたい。

#### 受入基準

1. THE System SHALL 生成した記事をMarkdownファイルとして出力する
2. THE System SHALL ファイル名に日付とタイトルを含める（例：2025-01-XX_claude-agent-skills-guide.md）
3. THE System SHALL UTF-8エンコーディングでファイルを保存する
4. THE System SHALL 出力先ディレクトリが存在しない場合は作成する
5. WHEN 同名のファイルが既に存在するとき、THE System SHALL 上書き確認を行う

### 要件7: エラーハンドリング

**ユーザーストーリー:** システム利用者として、スキルファイルの読み込みエラーや解析エラーが発生した場合でも、処理を継続し、問題のあるスキルをスキップして残りの記事を生成したい。

#### 受入基準

1. WHEN SKILL.mdファイルの読み込みに失敗したとき、THE System SHALL エラーメッセージをログに記録し、そのスキルをスキップする
2. WHEN YAMLフロントマターの解析に失敗したとき、THE System SHALL エラーメッセージをログに記録し、そのスキルをスキップする
3. WHEN 必須フィールド（name、description）が欠けているとき、THE System SHALL 警告メッセージをログに記録し、そのスキルをスキップする
4. THE System SHALL 処理完了時に、成功したスキル数とスキップしたスキル数を報告する
5. IF すべてのスキルの処理に失敗したとき、THEN THE System SHALL エラーメッセージを表示し、処理を中止する

### 要件8: 記事の品質保証

**ユーザーストーリー:** 読者として、記事が読みやすく、情報が正確で、一貫性のある内容であることを期待する。

#### 受入基準

1. THE System SHALL 生成した記事の文字数が5000文字以上であることを確認する
2. THE System SHALL すべてのスキルカテゴリが記事に含まれていることを確認する
3. THE System SHALL 各スキルの説明が空でないことを確認する
4. THE System SHALL Markdown記法の正しさを検証する（見出しレベルの一貫性、リストの正しい記法等）
5. THE System SHALL 記事内のリンクが有効であることを確認する（該当する場合）
6. THE System SHALL 安全性に関するセクションが含まれていることを確認する
7. THE System SHALL 前提ソフトウェアに関するセクションが含まれていることを確認する
8. THE System SHALL 見出しが初学者向けの表現になっていることを確認する
9. THE System SHALL 見出しの階層構造が適切であることを確認する
10. WHEN 品質チェックに失敗したとき、THE System SHALL 警告メッセージを表示し、問題箇所を報告する

### 要件9: 設定のカスタマイズ

**ユーザーストーリー:** システム利用者として、記事のスタイルや含める情報を設定ファイルでカスタマイズしたい。

#### 受入基準

1. THE System SHALL 設定ファイル（JSON形式）から以下の設定を読み込む：
   - 出力ディレクトリパス
   - 記事タイトル
   - 含めるスキルカテゴリ
   - 各スキルの説明の最大文字数
   - 技術レベル（初学者、中級者、上級者）
2. WHERE 設定ファイルが存在しない場合、THE System SHALL デフォルト設定を使用する
3. THE System SHALL 設定ファイルの形式が不正な場合、エラーメッセージを表示し、デフォルト設定を使用する
4. THE System SHALL 使用した設定内容をログに記録する

### 要件10: 実行ログの記録

**ユーザーストーリー:** システム管理者として、処理の詳細を確認し、問題のデバッグやパフォーマンス改善に役立てたい。

#### 受入基準

1. THE System SHALL 処理開始時刻と終了時刻をログに記録する
2. THE System SHALL 各スキルの処理状況（成功/スキップ/エラー）をログに記録する
3. THE System SHALL 生成された記事のファイルパスをログに記録する
4. THE System SHALL エラーや警告の詳細情報をログに記録する
5. THE System SHALL ログファイルをタイムスタンプ付きのファイル名で保存する
6. THE System SHALL ログレベル（DEBUG、INFO、WARNING、ERROR）を設定可能にする
