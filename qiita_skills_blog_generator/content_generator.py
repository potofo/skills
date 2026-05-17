"""
コンテンツ生成

解析されたスキル情報から記事コンテンツを生成します。
"""

from pathlib import Path
from typing import Dict, List, Optional
from .config import Config, SkillData
from .constants import CATEGORY_MAPPING, CATEGORY_ORDER, DOCUMENT_SKILLS
from .translator import Translator
from . import diagrams


class ContentGenerator:
    """
    コンテンツ生成クラス
    
    解析されたスキル情報から初学者向けの記事コンテンツを生成します。
    """
    
    def __init__(
        self,
        config: Config,
        translator: Optional[Translator] = None,
        images_dir: Optional[Path] = None,
        images_url_prefix: str = "images",
    ):
        """
        ContentGeneratorを初期化

        Args:
            config: システム設定
            translator: スキル説明文を翻訳する ``Translator``。
                ``None`` の場合は翻訳を行わず英語のまま使用する。
            images_dir: SVG画像を保存するディレクトリ（``output/images/`` など）。
                ``None`` の場合はSVG画像を生成せず、Markdown内図表のみ使用する。
            images_url_prefix: Markdownから画像を参照するときのURLプレフィックス。
        """
        self.config = config
        self.translator = translator
        self.images_dir = images_dir
        self.images_url_prefix = images_url_prefix
    
    def categorize_skills(self, skills: List[SkillData]) -> Dict[str, List[SkillData]]:
        """
        スキルを5つのカテゴリに分類する
        
        スキル名（ディレクトリ名）に基づいて、各スキルを適切なカテゴリに分類します。
        カテゴリマッピングに存在しないスキルは「その他」カテゴリに分類されます。
        各カテゴリ内でスキルはアルファベット順にソートされます。
        
        Args:
            skills: 分類するスキルのリスト
            
        Returns:
            カテゴリ名をキー、スキルリストを値とする辞書
        """
        # カテゴリごとのスキルリストを初期化
        categorized: Dict[str, List[SkillData]] = {
            category: [] for category in CATEGORY_ORDER
        }
        categorized["その他"] = []  # 未分類スキル用
        
        # 逆引きマッピングを作成（スキル名 -> カテゴリ名）
        skill_to_category: Dict[str, str] = {}
        for category, skill_names in CATEGORY_MAPPING.items():
            for skill_name in skill_names:
                skill_to_category[skill_name] = category
        
        # 各スキルを適切なカテゴリに分類
        for skill in skills:
            # スキル名からカテゴリを特定
            category = skill_to_category.get(skill.name, "その他")
            categorized[category].append(skill)
        
        # 各カテゴリ内でスキルをアルファベット順にソート
        for category in categorized:
            categorized[category].sort(key=lambda s: s.name)
        
        # 設定で指定されたカテゴリのみを含める
        filtered_categorized = {}
        for category in CATEGORY_ORDER:
            if category in self.config.included_categories:
                if categorized[category]:  # スキルが存在する場合のみ追加
                    filtered_categorized[category] = categorized[category]
        
        # 「その他」カテゴリにスキルがある場合は追加
        if categorized["その他"]:
            filtered_categorized["その他"] = categorized["その他"]
        
        return filtered_categorized
    
    def generate_introduction(self) -> str:
        """
        はじめにセクションを生成
        
        記事の導入部分を生成します。Agent Skillsの概要と、
        本記事の目的・対象読者を説明します。
        
        Returns:
            はじめにセクションのMarkdownテキスト
        """
        intro = """## はじめに

AI開発の世界では、大規模言語モデル（LLM）を活用したアプリケーション開発が急速に進化しています。その中でも、**Agent Skills**（エージェントスキル）は、AIエージェントに特定のタスクを効率的に実行させるための重要な仕組みとして注目を集めています。

Agent Skillsは、AIエージェント（Claude、ChatGPT、Geminiなど）が特定のタスクを実行する際に参照する、指示やスクリプト、リソースをまとめたパッケージです。例えば、「ブランドガイドラインに沿った文書を作成する」「特定のワークフローでデータを分析する」「Word文書やPDFを操作する」といった専門的なタスクを、再現可能な方法で実行できるようにします。

本記事では、**Anthropic社が公開しているClaude用Agent Skills**を初学者向けに解説します。クリエイティブ&デザイン、開発&技術、ドキュメント処理、エンタープライズ&コミュニケーション、メタスキルの5つのカテゴリに分類された全スキルについて、その目的、使用場面、主要な機能を分かりやすく紹介します。

また、企業内でAgent Skillsを利用する際に重要となる**安全性とリスク評価**、そして実際に利用・開発するために必要な**前提ソフトウェアとエコシステム**についても詳しく解説します。これにより、Agent Skillsを安全かつ効果的に活用するための知識を身につけることができます。

**対象読者**: Agent Skillsの概念や使い方を初めて学ぶ方、AIエージェントを活用した開発に興味がある方
"""
        return intro
    
    def generate_history_section(self) -> str:
        """
        Agent Skillsの歴史と公式ロードマップセクションを生成

        Anthropic公式の発表・公開タイミング、オープン標準化、
        パートナーエコシステム、現在の規模を、出典リンク付きでまとめる。
        Research/Anthropic-Agent-Skills.md の調査内容をマージしたもの。

        Returns:
            歴史・ロードマップセクションのMarkdownテキスト
        """
        section = """## Agent Skillsの歴史と公式ロードマップ

Agent Skillsは段階的に展開されてきた仕組みで、概念の発表とオープン標準化に大きな節目があります。歴史を押さえておくと、エコシステムの広がりや今後の方向性が理解しやすくなります。

### 主要な節目

| 時期 | 出来事 | 概要 |
|---|---|---|
| 2025年10月16日（米国時間） | Anthropicが**Agent Skills**をClaude向け機能として初公開 | 「指示・スクリプト・リソースをAIエージェントが必要に応じて段階的に読み込む」という**Progressive Disclosure（段階的開示）**を中核設計とする概念を提唱 |
| 2025年10月16日前後 | 公式GitHubリポジトリ [`anthropics/skills`](https://github.com/anthropics/skills) を公開 | `docx` / `xlsx` / `pdf` / `pptx` / `skill-creator` / `mcp-builder` / `frontend-design` などの推奨スキル群を提供開始。ドキュメント系4スキル（`docx`/`xlsx`/`pdf`/`pptx`）はClaude.aiのドキュメント作成機能の基盤として組み込まれた |
| 2025年12月18日 | Agent Skillsを**オープン標準（open standard）**として公開 | 同時にClaudeのコネクタディレクトリ（claude.com/connectors）でAtlassian、Canva、Cloudflare、Figma、Notion、Ramp、Sentry、Zapier、Stripe、Vercelなどのパートナー製スキルを提供開始 |
| 2026年4月7日時点 | 公式リポジトリは17スキル体制に拡大 | 本記事で扱うのもこの17スキル |

### Progressive Disclosureが解決する問題

Anthropicが当初から強調しているのは、AIエージェントの**コンテキスト効率**の問題です。すべての専門知識を常時ロードするとコンテキストが飽和してしまうため、メタデータ → 本文 → リソースの3段階で読み込む設計が採用されました（詳細は次の「Agent Skillsとは」セクションで解説）。

### オープン標準化の意義

2025年12月18日のオープン標準化により、AnthropicはAgent Skillsを**自社プロダクトだけの仕組みから、複数のAIプラットフォームで使える共通仕様へ**広げる方針を明確にしました。これにより、企業はAgent Skillsを「Claudeに特化した投資」ではなく「より長期的な再利用可能資産」として位置づけやすくなっています。

### 主な出典

- [Equipping agents for the real world with Agent Skills（Anthropic Engineering Blog）](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Agent Skills（Claude API Docs）](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [`anthropics/skills`（公式GitHubリポジトリ）](https://github.com/anthropics/skills)
- [Anthropic launches enterprise 'Agent Skills' and opens the standard（VentureBeat）](https://venturebeat.com/technology/anthropic-launches-enterprise-agent-skills-and-opens-the-standard)
- [Agent Skills: Anthropic's Next Bid to Define AI Standards（The New Stack）](https://thenewstack.io/agent-skills-anthropics-next-bid-to-define-ai-standards/)
- [Anthropic publishes Agent Skills as an open standard（The Decoder）](https://the-decoder.com/anthropic-publishes-agent-skills-as-an-open-standard-for-ai-platforms/)
- [Anthropic makes agent Skills an open standard（SiliconANGLE、2025/12/18）](https://siliconangle.com/2025/12/18/anthropic-makes-agent-skills-open-standard/)
- [Anthropic Official Skills Repository: 17 Skills Walkthrough（claudecn.com）](https://claudecn.com/en/blog/claude-official-skills-walkthrough/)
"""
        return section

    def generate_what_is_agent_skills(self) -> str:
        """
        Agent Skillsとはセクションを生成
        
        Agent Skillsの基本概念、仕組み、利用方法を初学者向けに説明します。
        
        Returns:
            Agent SkillsとはセクションのMarkdownテキスト
        """
        # 図表（SVG概念図 + Mermaid構造図 + Mermaid段階的開示）
        overview_image = ""
        if self.images_dir is not None:
            overview_image = diagrams.system_overview_svg(
                self.images_dir, self.images_url_prefix
            )
        skill_structure = diagrams.skill_structure_mermaid()
        progressive_disclosure = diagrams.progressive_disclosure_mermaid()
        usage_sequence = diagrams.usage_sequence_mermaid()

        section = """## Agent Skillsとは

### Agent Skillsの基本概念

**Agent Skills**（エージェントスキル）は、AIエージェントが特定のタスクを効率的に実行するための「知識パッケージ」です。人間が新しいスキルを学ぶように、AIエージェントも特定の分野やタスクに関する専門知識を必要とします。Agent Skillsは、その専門知識を構造化された形で提供します。

""" + overview_image + """

具体的には、Agent Skillsは以下の要素で構成されています：

- **SKILL.md**: スキルの中核となるファイル。YAMLフロントマター（メタデータ）とMarkdown本文（指示・ガイドライン）を含みます
- **バンドルリソース**（オプション）:
  - `scripts/`: 決定論的タスク用のPython、JavaScript、シェルスクリプト
  - `references/`: 必要に応じて読み込まれる詳細なドキュメント
  - `assets/`: 出力で使用されるテンプレート、フォント、画像
  - `templates/`: 再利用可能なファイルテンプレート

スキルディレクトリの構造は次のようになります。

""" + skill_structure + """

### Agent Skillsの仕組み：段階的開示

Agent Skillsは「段階的開示」という効率的な仕組みを採用しています。これは、必要な情報を必要なタイミングで読み込むことで、AIエージェントのコンテキスト（作業メモリ）を効率的に使用する仕組みです。

各レベルの位置づけは次のとおりです。

| レベル | 名称 | 読み込みタイミング | サイズ目安 | 含まれる内容 |
|---|---|---|---|---|
| 1 | メタデータ | 常時コンテキスト内 | 約100語 | スキル名、`description`、いつ使うかの判断材料 |
| 2 | SKILL.md 本文 | スキルがトリガーされた時 | 理想は500行未満 | 詳細な指示・ガイドライン、使用例、ベストプラクティス |
| 3 | バンドルリソース | 必要に応じて | 無制限 | 大規模なリファレンス、スクリプト、テンプレート、アセット |

""" + progressive_disclosure + """

この段階的なアプローチにより、AIエージェントは必要な情報だけを効率的に利用できます。

### Agent Skillsの利用方法

Agent Skillsは、以下の環境で利用できます：

| 利用環境 | 提供形態 | 補足 |
|---|---|---|
| Claude.ai | 有料プラン（Pro / Team）にプリインストール | UIから自動でスキルが選ばれる |
| Claude Code | プラグインマーケットプレイス経由でインストール | `/plugin install <skill>@anthropic-agent-skills` |
| Claude API | Skills API 経由でプログラムから利用 | カスタムスキルのアップロードも可能 |

スキルを利用する際は、AIエージェントが自動的に適切なスキルを選択して読み込みます。ユーザーは特別な操作をする必要はありません。例えば、「Word文書を作成して」と依頼すると、AIエージェントは自動的に`docx`スキルを読み込み、適切な形式で文書を生成します。

具体的なやり取りは次のシーケンスのように進みます。

""" + usage_sequence + """

### Agent Skillsの利点

Agent Skillsを使用することで、以下のような利点が得られます。

| 利点 | 内容 |
|---|---|
| 再現性 | 同じタスクを一貫した品質で実行できる |
| 専門性 | 特定分野の深い知識を活用できる |
| 効率性 | 段階的開示により、必要な情報だけを効率的に利用できる |
| 拡張性 | 新しいスキルを追加することで、AIエージェントの能力を拡張できる |
| 標準化 | 組織内で共通のワークフローやガイドラインを適用できる |
"""
        return section
    
    def generate_safety_section(self) -> str:
        """
        安全性とリスクセクションを生成
        
        Agent Skillsの安全性に関する情報を初学者向けに説明します。
        公式Agent Skills、ベンダー提供Agent Skills、野良Agent Skillsの違いと、
        企業内での安全性判断基準、Anthropicの公式Agent Skillsが信頼できる理由を含めます。
        
        Returns:
            安全性とリスクセクションのMarkdownテキスト
        """
        # 3区分の比較は厳密に幅を揃えたいのでSVGで描画。
        # ``images_dir`` が無い場合（テスト等）は Mermaid にフォールバック。
        if self.images_dir is not None:
            safety_compare = diagrams.safety_comparison_svg(
                self.images_dir, self.images_url_prefix
            )
        else:
            safety_compare = diagrams.safety_comparison_mermaid()
        safety_flow = diagrams.safety_decision_plantuml()

        section = """## Agent Skillsの安全性とリスク

企業内でAgent Skillsを利用する際には、安全性とリスクを適切に評価することが重要です。Agent Skillsは、その提供元や開発プロセスによって信頼性が大きく異なります。ここでは、Agent Skillsを3つのカテゴリに分類し、それぞれの特徴と安全性について解説します。

""" + safety_compare + """
### 公式Agent Skills

**公式Agent Skills**とは、Anthropic、OpenAI、Googleなどの大手AI企業（ビッグテック）が自社で開発・公開・メンテナンスしているAgent Skillsです。

**安全性の特徴**:

- **厳格なコードレビューとセキュリティ監査**: 企業内の専門チームによる多層的なレビュープロセスを経ています
- **明確なライセンスと法的保護**: Apache 2.0などのオープンソースライセンス、またはプロプライエタリライセンスで明確に保護されています
- **継続的なメンテナンスとサポート**: バグ修正、セキュリティパッチ、機能改善が定期的に提供されます
- **データプライバシーとセキュリティ**: 企業のプライバシーポリシーとセキュリティ基準に準拠しています
- **悪意のあるコード混入のリスクが極めて低い**: 開発プロセスの透明性と企業の評判により、悪意のあるコードが混入する可能性は極めて低いです

**企業内利用における推奨度**: ★★★★★（最も推奨）

### ベンダー提供Agent Skills

**ベンダー提供Agent Skills**とは、Microsoft、MySQL、AWS、Salesforceなどのプロダクトベンダーが、自社製品やサービスとの統合を目的として開発・公開しているAgent Skillsです。

**安全性の特徴**:

- **製品ベンダーによる品質保証**: 自社製品との互換性と品質が保証されています
- **公式ドキュメントとサポート**: 製品の公式ドキュメントやサポートチャネルが利用できます
- **製品のライフサイクルに連動**: 製品のアップデートに合わせてスキルも更新されます
- **セキュリティ基準の遵守**: ベンダーのセキュリティポリシーに準拠しています
- **特定製品への依存**: そのベンダーの製品やサービスを使用していることが前提となります

**企業内利用における推奨度**: ★★★★☆（推奨、ただし製品依存に注意）

### 野良Agent Skills

**野良Agent Skills**とは、インターネット上で個人や非公式な組織が公開しているAgent Skillsです。GitHubなどのプラットフォームで公開されていますが、出所や品質が不明確な場合があります。

**リスクと注意点**:

- **コードレビューの不在**: 専門的なセキュリティ監査を受けていない可能性があります
- **メンテナンスの不確実性**: 開発者が突然メンテナンスを停止する可能性があります
- **悪意のあるコードのリスク**: 意図的または非意図的に、セキュリティ上の脆弱性や悪意のあるコードが含まれる可能性があります
- **ライセンスの不明確さ**: ライセンス条項が不明確または存在しない場合があります
- **データ漏洩のリスク**: 外部サーバーへのデータ送信など、意図しないデータ漏洩のリスクがあります
- **サポートの欠如**: 問題が発生しても、サポートを受けられない可能性があります

**企業内利用における推奨度**: ★☆☆☆☆（非推奨、使用する場合は徹底的な検証が必要）

### 企業内での安全性判断基準

企業内でAgent Skillsを利用する際は、以下の基準で安全性を評価することを推奨します。

| # | 評価軸 | 確認すべき問い |
|---|---|---|
| 1 | 提供元の信頼性 | 提供元は信頼できる企業または組織か？評判やトラックレコードはどうか？ |
| 2 | コードの透明性 | ソースコードは公開されているか？コードレビューやセキュリティ監査を受けているか？ |
| 3 | ライセンスの明確性 | ライセンス条項が明示されているか？企業内利用が許可されているか？ |
| 4 | メンテナンス体制 | 定期的にアップデートされているか？セキュリティパッチが迅速に提供されているか？ |
| 5 | データの取り扱い | 外部サーバーへのデータ送信があるか？データプライバシーポリシーは明確か？ |
| 6 | 依存関係 | 使用している外部ライブラリやツールは安全か？既知の脆弱性はないか？ |
| 7 | 社内ポリシー整合性 | 自社のセキュリティポリシーに準拠しているか？情報セキュリティ部門の承認は取得済みか？ |

""" + safety_flow + """

1. **提供元の信頼性**:
   - 提供元は信頼できる企業または組織か？
   - 提供元の評判やトラックレコードはどうか？

2. **コードの透明性**:
   - ソースコードが公開されているか？
   - コードレビューやセキュリティ監査を受けているか？

3. **ライセンスの明確性**:
   - ライセンス条項が明確に記載されているか？
   - 企業内利用が許可されているか？

4. **メンテナンス体制**:
   - 定期的にアップデートされているか？
   - セキュリティパッチが迅速に提供されているか？

5. **データの取り扱い**:
   - 外部サーバーへのデータ送信はあるか？
   - データプライバシーポリシーは明確か？

6. **依存関係の確認**:
   - 使用している外部ライブラリやツールは安全か？
   - 依存関係に既知の脆弱性はないか？

7. **社内セキュリティポリシーとの整合性**:
   - 自社のセキュリティポリシーに準拠しているか？
   - 情報セキュリティ部門の承認を得ているか？

### 本記事で扱うAnthropicの公式Agent Skillsについて

本記事で解説するAgent Skillsは、すべて**Anthropic社が開発・公開している公式Agent Skills**です。これらのスキルは以下の理由から信頼できます：

**信頼できる理由**:

1. **Anthropic社の開発**: Claude（大規模言語モデル）を開発したAnthropic社が、自社製品の機能を最大限に活用するために設計・開発しています

2. **厳格な品質管理**: Anthropic社内の専門チームによる多層的なコードレビュー、セキュリティ監査、品質保証プロセスを経ています

3. **オープンソースとプロプライエタリの明確な区別**:
   - ほとんどのサンプルスキル: Apache 2.0ライセンス（オープンソース）
   - ドキュメントスキル（docx、pdf、pptx、xlsx）: ソース公開、プロプライエタリライセンス（参照・学習用）

4. **継続的なメンテナンス**: Anthropic社が継続的にメンテナンスし、Claudeの新機能やアップデートに合わせて改善しています

5. **公式ドキュメントとサポート**: 公式ドキュメント、サンプルコード、コミュニティサポートが充実しています

6. **透明性**: ソースコードがGitHub上で公開されており、誰でも内容を確認できます（プロプライエタリスキルも参照可能）

7. **企業利用を想定した設計**: エンタープライズ環境での利用を想定し、セキュリティとプライバシーに配慮した設計になっています

**企業内利用における推奨度**: ★★★★★（最も推奨）

本記事では、これらの信頼性の高い公式Agent Skillsを安心して学習・利用していただけます。ただし、実際に企業内で利用する際は、必ず自社のセキュリティポリシーに照らし合わせて評価し、情報セキュリティ部門の承認を得ることを推奨します。
"""
        return section
    
    def generate_prerequisites_section(self) -> str:
        """
        前提ソフトウェアセクションを生成
        
        Agent Skillsを利用・開発するために必要なソフトウェアとエコシステムを
        初学者向けに説明します。IDE、CLI、開発環境、パッケージリポジトリ、
        ドキュメント処理ツール、スキルカテゴリごとの依存関係、
        企業内利用における考慮事項を含めます。
        
        Returns:
            前提ソフトウェアセクションのMarkdownテキスト
        """
        section = """## Agent Skillsを利用・開発するための前提ソフトウェア

Agent Skillsを効果的に利用・開発するためには、適切なソフトウェア環境が必要です。このセクションでは、Agent Skillsを利用できるツール、開発に必要な環境、そして企業内で利用する際の考慮事項について解説します。

### Agent Skillsを利用できるIDE（統合開発環境）

| IDE | 提供元 | Agent Skills対応 | 企業内利用上の留意点 | 公式サイト |
|---|---|---|---|---|
| VSCode（Visual Studio Code） | Microsoft（公式） | 拡張機能経由でClaude APIと連携 | 無料。Claude API接続のためのインターネットアクセスが必要 | https://code.visualstudio.com/ |
| Kiro | Anthropic（公式） | Agent Skillsをネイティブにサポート | Claude APIへのアクセスが必要。企業向けプランあり | https://www.anthropic.com/ |
| Cursor | Anysphere | Claude統合により利用可能 | 商用利用は要ライセンス確認 | https://www.cursor.com/ |
| JetBrains IDEs（IntelliJ IDEA / PyCharm 等） | JetBrains | プラグイン経由でClaude APIと連携 | 商用利用は要ライセンス | https://www.jetbrains.com/ |

### Agent Skillsを利用できるCLI（コマンドラインインターフェース）

| CLI | 提供元 | Agent Skills対応 | 必要なAPIキー |
|---|---|---|---|
| Claude Code | Anthropic（公式） | プラグインマーケットプレイス経由でインストール | Anthropic APIキー |
| Codex | OpenAI（公式） | OpenAI独自のAgent Skills形式に対応 | OpenAI APIキー |
| Gemini CLI | Google（公式） | Google独自のAgent Skills形式に対応 | Google Cloud APIキー |
| Kiro CLI | Anthropic（公式） | Agent Skillsをネイティブサポート | Anthropic APIキー |

### Agent Skillsを構築するための開発環境

| ランタイム | 用途 | 推奨バージョン | 主な依存 | 公式サイト |
|---|---|---|---|---|
| Node.js | JS/TSベースのスキルやMCPサーバー開発 | 18 以上（LTS推奨） | npm | https://nodejs.org/ |
| Python | Pythonベースのスキル、ドキュメント処理スクリプト | 3.8 以上 | pip / uv | https://www.python.org/ |
| TypeScript | MCPサーバー開発（推奨言語） | 5.x 以上 | MCP SDK、Zod | https://www.typescriptlang.org/ |

### パッケージリポジトリとライブラリ管理

| リポジトリ / ツール | 用途 | 主な関連パッケージ | 企業内利用上の留意点 |
|---|---|---|---|
| npm | JS/TSライブラリ管理 | `docx`、`@modelcontextprotocol/sdk`、`zod` | `.npmrc` でプロキシ設定可。プライベートレジストリ（Verdaccio、Artifactory）対応 |
| PyPI | Pythonライブラリ管理 | `python-docx`、`fastmcp`、`pydantic` | `pip.conf` でプロキシ設定可。devpi、Artifactory対応 |
| uv | 高速Pythonパッケージマネージャ（pip互換） | （pip互換） | pipと同じプロキシ設定が利用可能 |

### ドキュメント処理系スキルに必要な外部ツール

| ツール | 用途 | 起動コマンド例 | ライセンス | 公式サイト |
|---|---|---|---|---|
| LibreOffice | ドキュメント形式変換、PDF生成 | `soffice --headless --convert-to docx FILE` | Mozilla Public License 2.0 | https://www.libreoffice.org/ |
| Pandoc | 文書変換とテキスト抽出 | `pandoc --track-changes=all FILE.docx -o OUT.md` | GPL v2 以上 | https://pandoc.org/ |
| Poppler | PDFユーティリティ | `pdftoppm INPUT.pdf OUT` | GPL v2 以上 | https://poppler.freedesktop.org/ |
| p5.js | クリエイティブコーディング | CDN経由（`<script src="...p5.js">`） | LGPL v2.1 | https://p5js.org/ |

### スキルカテゴリごとの依存関係

| # | カテゴリ | スキル | 主な依存 |
|---|---|---|---|
| 1 | クリエイティブ&デザイン | algorithmic-art | p5.js（CDN）、Webブラウザ |
| 2 | クリエイティブ&デザイン | canvas-design | Node.js、Canvas API、カスタムフォント |
| 3 | クリエイティブ&デザイン | frontend-design | HTML / CSS / JavaScript、Webブラウザ |
| 4 | クリエイティブ&デザイン | theme-factory | Node.js、CSS処理ライブラリ |
| 5 | 開発&技術 | claude-api | Claude API（Python SDK / TypeScript SDK / cURL） |
| 6 | 開発&技術 | mcp-builder | Node.js + TypeScript + MCP SDK + Zod、または Python + FastMCP + Pydantic |
| 7 | 開発&技術 | webapp-testing | テストフレームワーク（Jest、Pytest 等） |
| 8 | 開発&技術 | web-artifacts-builder | HTML / CSS / JavaScript、Webブラウザ |
| 9 | ドキュメント処理 | docx | Python（python-docx）、Pandoc、LibreOffice（soffice） |
| 10 | ドキュメント処理 | pdf | Poppler（pdftoppm）、Python（PyPDF2 等） |
| 11 | ドキュメント処理 | pptx | Python（python-pptx）、LibreOffice |
| 12 | ドキュメント処理 | xlsx | Python（openpyxl、pandas 等）、LibreOffice |
| 13 | エンタープライズ&コミュニケーション | brand-guidelines | 特別な依存なし（Markdownベース） |
| 14 | エンタープライズ&コミュニケーション | doc-coauthoring | ドキュメント処理ツール（docx、pdf 等） |
| 15 | エンタープライズ&コミュニケーション | internal-comms | 特別な依存なし（テンプレートベース） |
| 16 | エンタープライズ&コミュニケーション | slack-gif-creator | Slack API、画像処理ライブラリ |
| 17 | メタスキル | skill-creator | 特別な依存なし（Markdownベース） |

### 企業内利用における考慮事項

| # | 観点 | 主な内容 |
|---|---|---|
| 1 | ネットワークとセキュリティ | Claude APIへのインターネットアクセス、ファイアウォール / プロキシ設定、CDN経由ライブラリのアクセス可否を事前確認 |
| 2 | プライベートリポジトリの利用 | Verdaccio / JFrog Artifactory / GitHub Packages、devpi など、社内専用のnpm / PyPIサーバーを構築 |
| 3 | ライセンスコストとコンプライアンス | LibreOffice / Pandoc / Poppler / Node.js / Python は無料。Claude APIは従量課金。各ツールのライセンス条項を要確認 |
| 4 | オフライン環境での利用 | 開発ツール本体はオフラインインストール可能。Claude APIはオフライン不可 |
| 5 | データプライバシーとセキュリティ | 入力データはClaude APIに送信される。Anthropicはユーザーデータを学習に使用しないことを明言 |
| 6 | 情報セキュリティ部門の承認 | 導入前に必ず承認を取得。本記事「Agent Skillsの安全性とリスク」のチェック項目を活用 |
| 7 | サポートとメンテナンス | Anthropic公式は継続メンテあり。OSSはコミュニティサポート。Claude API企業向けプランは専任サポートあり |
"""
        return section
    
    def resolve_license_type(self, skill: SkillData) -> str:
        """
        スキルの実際のライセンス種別を判定する

        SKILL.mdのlicenseフィールドの値だけでは判別が難しいケースがあるため、
        ドキュメントスキル（docx、pdf、pptx、xlsx）はプロプライエタリ、
        それ以外のAnthropic公式スキルは原則Apache 2.0として扱います。

        Args:
            skill: 判定するスキルデータ

        Returns:
            "Apache 2.0", "Proprietary", "その他" のいずれか
        """
        # ドキュメントスキルは常にプロプライエタリ（要件5.3）
        if skill.name in DOCUMENT_SKILLS:
            return "Proprietary"

        # licenseフィールドの値で明示的にプロプライエタリと指定されていればそれに従う
        license_value = (skill.license or "").strip()
        license_lower = license_value.lower()
        if "proprietary" in license_lower:
            return "Proprietary"

        # 明示的にApacheと指定されていればApache
        if "apache" in license_lower:
            return "Apache 2.0"

        # それ以外（"Complete terms in LICENSE.txt" や未指定）は
        # Anthropic公式リポジトリの標準であるApache 2.0として扱う
        return "Apache 2.0"

    def format_license_label(self, skill: SkillData) -> str:
        """
        スキル説明に付与するライセンスラベル文字列を生成する

        Apache 2.0とプロプライエタリを明確に区別して表示します（要件5.2、5.4）。
        ドキュメントスキルについては「ソース公開」だがプロプライエタリである旨を
        明記します（要件5.3）。

        Args:
            skill: ライセンスラベルを生成するスキルデータ

        Returns:
            括弧付きのライセンスラベル（例: "（ライセンス: Apache 2.0 - オープンソース）"）
        """
        license_type = self.resolve_license_type(skill)
        if license_type == "Apache 2.0":
            return "（ライセンス: Apache 2.0 - オープンソース）"
        if license_type == "Proprietary":
            # ドキュメントスキルは「ソース公開だがプロプライエタリ」を明記
            if skill.name in DOCUMENT_SKILLS:
                return "（ライセンス: プロプライエタリ - ソース公開だが参照・学習用）"
            return "（ライセンス: プロプライエタリ - ソース公開、参照・学習用）"
        # その他のライセンス（フォールバック）
        return f"（ライセンス: {skill.license}）"

    def generate_skill_description(self, skill: SkillData) -> str:
        """
        個別スキルの説明を生成（200-400文字）
        
        スキルの目的、使用場面、主要な機能、技術的な特徴を含めた
        初学者向けの説明を生成します。専門用語には補足説明を追加し、
        具体的な使用例やユースケースを含めます。
        
        Args:
            skill: 説明を生成するスキルデータ
            
        Returns:
            スキルの説明文（200-400文字程度）
        """
        # スキル名に基づいて説明を生成
        # 基本的な説明はskill.descriptionから取得し、初学者向けに補足
        
        description_parts = []
        
        # スキルの基本説明を追加
        if skill.description:
            # 説明文は英語で書かれているため、Translatorがあれば日本語に翻訳する
            base_description = skill.description
            if self.translator is not None:
                base_description = self.translator.translate(base_description)
            description_parts.append(base_description)
        
        # ライセンス情報を判定（要件5.1〜5.4）
        # licenseフィールドの有無に関わらず、スキル種別に基づいて
        # Apache 2.0またはプロプライエタリのいずれかを明示する
        license_info = self.format_license_label(skill)
        
        # バンドルリソースの情報を追加
        resources = []
        if skill.has_scripts:
            resources.append("実行スクリプト")
        if skill.has_references:
            resources.append("リファレンスドキュメント")
        if skill.has_templates:
            resources.append("テンプレートファイル")
        if skill.has_assets:
            resources.append("アセット（フォント、画像等）")
        
        if resources:
            resources_text = f"バンドルリソースとして{' / '.join(resources)}を含みます。"
            description_parts.append(resources_text)
        
        # 文字数制限を適用（設定で指定された最大文字数）。
        # ライセンス情報は要件5.1〜5.4により必須なので、必ず末尾に含める。
        # スキル説明本文が長い場合は、ライセンス情報の分の領域を確保した上で
        # 本文を切り詰める。
        max_length = self.config.max_skill_description_length
        license_suffix = f" {license_info}" if license_info else ""
        body_text = " ".join(description_parts)
        body_budget = max_length - len(license_suffix)

        # ライセンスサフィックスだけで上限を超える病的なケースは考えにくいが、
        # 安全のため最低限の本文長を確保しつつ可能な範囲で切り詰める。
        if body_budget < 0:
            body_budget = 0

        if len(body_text) > body_budget:
            # 末尾を「...」で省略しつつライセンスは残す
            ellipsis = "..."
            if body_budget > len(ellipsis):
                body_text = body_text[: body_budget - len(ellipsis)] + ellipsis
            else:
                body_text = body_text[:body_budget]

        full_description = body_text + license_suffix
        
        return full_description
    
    def generate_conclusion(self) -> str:
        """
        まとめセクションを生成
        
        記事全体のまとめと、Agent Skillsの活用に向けた
        次のステップを提示します。
        
        Returns:
            まとめセクションのMarkdownテキスト
        """
        conclusion = """## まとめ

本記事では、Anthropic社が公開しているClaude用Agent Skillsについて、初学者向けに解説しました。Agent Skillsは、AIエージェントに特定のタスクを効率的に実行させるための「知識パッケージ」であり、段階的開示という効率的な仕組みを採用しています。

### 本記事で学んだこと

**Agent Skillsの基本概念**:
- Agent Skillsは、指示、スクリプト、リソースをまとめたパッケージ
- 段階的開示により、必要な情報を必要なタイミングで読み込む
- 再現性、専門性、効率性、拡張性、標準化という利点がある

**安全性とリスク評価**:
- 公式Agent Skills（Anthropic等）は最も信頼性が高い
- ベンダー提供Agent Skillsは製品依存に注意が必要
- 野良Agent Skillsは徹底的な検証が必要
- 企業内利用では、提供元の信頼性、コードの透明性、ライセンスの明確性などを評価する

**前提ソフトウェアとエコシステム**:
- Agent Skillsを利用できるIDE（VSCode、Kiro等）とCLI（Claude Code等）
- 開発に必要な環境（Node.js、Python、TypeScript）
- パッケージリポジトリ（npm、PyPI、uv）
- ドキュメント処理ツール（LibreOffice、Pandoc、Poppler）
- 企業内利用における考慮事項（ネットワーク、セキュリティ、ライセンス等）

**5つのカテゴリのスキル**:
- **クリエイティブ&デザイン**: アルゴリズミックアート、キャンバスデザイン、フロントエンドデザイン、テーマファクトリー
- **開発&技術**: Claude API統合、MCPサーバー開発、Webアプリテスト、Webアーティファクト構築
- **ドキュメント処理**: Word、PDF、PowerPoint、Excelの操作
- **エンタープライズ&コミュニケーション**: ブランドガイドライン、ドキュメント共同作業、社内コミュニケーション、Slack統合
- **メタスキル**: スキル作成支援

### 次のステップ

Agent Skillsを実際に活用するための次のステップを紹介します：

**1. 環境のセットアップ**:
- Claude.ai（有料プラン）またはClaude Code（CLI）をセットアップ
- 必要に応じて、開発環境（Node.js、Python）をインストール
- ドキュメント処理スキルを使用する場合は、LibreOffice、Pandoc、Popplerをインストール

**2. スキルの試用**:
- Claude.aiまたはClaude Codeで、興味のあるスキルを試してみる
- 簡単なタスクから始めて、スキルの動作を理解する
- 異なるパラメータや入力で実験し、スキルの挙動を学ぶ

**3. 企業内での評価**:
- 本記事の「安全性とリスク」セクションを参考に、自社のセキュリティポリシーに照らし合わせて評価
- 情報セキュリティ部門に相談し、承認を得る
- パイロットプロジェクトで小規模に試用し、効果を測定

**4. カスタムスキルの開発**:
- 既存のスキルをベースに、自社のワークフローに合わせたカスタムスキルを開発
- skill-creatorスキルを活用して、効率的にスキルを作成
- 社内で共有し、チーム全体の生産性を向上

**5. 継続的な学習**:
- Anthropicの公式ドキュメントやコミュニティを活用
- 新しいスキルやアップデートを定期的にチェック
- 他のユーザーの事例やベストプラクティスを学ぶ

### 最後に

Agent Skillsは、AIエージェントの能力を大幅に拡張し、特定のタスクを効率的に実行するための強力なツールです。本記事で紹介したAnthropicの公式Agent Skillsは、信頼性が高く、企業内でも安心して利用できます。

ただし、実際に利用する際は、必ず自社のセキュリティポリシーに準拠し、適切なリスク評価を行うことが重要です。また、Agent Skillsは継続的に進化しているため、最新の情報を常にチェックし、新しい機能やベストプラクティスを取り入れることをお勧めします。

Agent Skillsを活用することで、AIエージェントとの協働がより効率的かつ効果的になり、開発やビジネスの生産性を大幅に向上させることができます。ぜひ、本記事を参考に、Agent Skillsの世界を探索してみてください。

**参考リンク**:
- Anthropic公式サイト: https://www.anthropic.com/
- Claude API ドキュメント: https://docs.anthropic.com/
- Agent Skills リポジトリ: https://github.com/anthropics/anthropic-agent-skills
- Agent Skills 仕様: https://agentskills.io/

本記事が、Agent Skillsの理解と活用の一助となれば幸いです。
"""
        return conclusion
