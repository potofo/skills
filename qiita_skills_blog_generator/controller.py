"""
メインコントローラ

全体の制御を担当するMainControllerクラスを定義します。
設定読み込み、各コンポーネントのインスタンス化、メイン処理フローの実行を行います。

要件: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3,
      3.1〜3.10, 4.1〜4.8, 5.1〜5.4, 6.1〜6.5, 8.1〜8.10, 9.1, 9.2, 9.3, 9.4
"""

from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
import json
import re
import sys

from .config import Config, ProcessingResult, SkillData
from .constants import CATEGORY_ORDER, MIN_ARTICLE_LENGTH, REQUIRED_SECTIONS
from .content_generator import ContentGenerator
from . import diagrams
from .logger import Logger
from .markdown_formatter import MarkdownFormatter
from .skill_analyzer import SkillAnalyzer
from .translator import build_translator_from_config
from .utils import ensure_directory_exists, sanitize_filename


class MainController:
    """
    メインコントローラ

    システム全体の制御を担当します。設定の読み込み、各コンポーネントの
    インスタンス化、メイン処理フローの実行、品質検証、記事の保存を行います。
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        MainControllerを初期化する

        設定ファイルを読み込み、Loggerと各コンポーネントを初期化します。

        Args:
            config_path: 設定ファイルのパス（オプション）。
                         指定がない場合はデフォルト設定を使用します。

        要件:
            9.1: 設定ファイルから設定を読み込む
            9.2: 設定ファイルが存在しない場合はデフォルト設定を使用する
            9.3: 設定ファイルが不正な場合はデフォルト設定を使用する
            9.4: 使用した設定内容をログに記録する
        """
        # 設定を読み込む
        self.config: Config = self.load_config(config_path)

        # Loggerを初期化
        self.logger: Logger = Logger(
            log_level=self.config.log_level,
            log_file=self.config.log_file,
        )

        # 使用した設定内容をログに記録（要件9.4）
        self.logger.log_config(self.config.to_dict())

        # 各コンポーネントをインスタンス化
        self.analyzer: SkillAnalyzer = SkillAnalyzer()
        # 翻訳器を構築（translation_enabled=False または APIキー未設定時は None になりうる）
        self.translator = build_translator_from_config(self.config)

        # 図用の画像保存先（output_directory/images/）
        if self.config.diagrams_enabled:
            self.images_dir: Optional[Path] = (
                self.config.output_directory / self.config.images_subdir
            )
            self.images_url_prefix = self.config.images_subdir
        else:
            self.images_dir = None
            self.images_url_prefix = self.config.images_subdir

        self.generator: ContentGenerator = ContentGenerator(
            self.config,
            translator=self.translator,
            images_dir=self.images_dir,
            images_url_prefix=self.images_url_prefix,
        )
        self.formatter: MarkdownFormatter = MarkdownFormatter()

    def load_config(self, config_path: Optional[Path]) -> Config:
        """
        設定ファイルを読み込む

        設定ファイルが存在する場合はその内容を読み込み、
        存在しない場合や読み込みに失敗した場合はデフォルト設定を使用します。

        Args:
            config_path: 設定ファイルのパス（オプション）

        Returns:
            Configオブジェクト

        要件:
            9.1: 設定ファイル（JSON形式）から設定を読み込む
            9.2: 設定ファイルが存在しない場合はデフォルト設定を使用する
            9.3: 設定ファイルの形式が不正な場合はデフォルト設定を使用する
        """
        # 設定ファイルパスが指定されていない場合はデフォルト設定（要件9.2）
        if config_path is None:
            return Config.default()

        # ファイルが存在しない場合はデフォルト設定（要件9.2）
        if not config_path.exists():
            print(
                f"警告: 設定ファイルが見つかりません: {config_path}\n"
                f"原因: 指定されたパスにファイルが存在しません\n"
                f"対処: デフォルト設定を使用します"
            )
            return Config.default()

        # 設定ファイルを読み込む
        try:
            return Config.from_json(config_path)
        except json.JSONDecodeError as e:
            # JSON形式が不正な場合はデフォルト設定（要件9.3）
            print(
                f"警告: 設定ファイルのJSON形式が不正です: {config_path}\n"
                f"原因: {str(e)}\n"
                f"対処: デフォルト設定を使用します"
            )
            return Config.default()
        except (TypeError, ValueError) as e:
            # 設定値が不正な場合はデフォルト設定（要件9.3）
            print(
                f"警告: 設定ファイルの内容が不正です: {config_path}\n"
                f"原因: {str(e)}\n"
                f"対処: デフォルト設定を使用します"
            )
            return Config.default()
        except Exception as e:
            # その他の予期しないエラーもデフォルト設定にフォールバック
            print(
                f"警告: 設定ファイルの読み込みに失敗しました: {config_path}\n"
                f"原因: {type(e).__name__}: {str(e)}\n"
                f"対処: デフォルト設定を使用します"
            )
            return Config.default()

    def run(self, force: bool = False) -> ProcessingResult:
        """
        メイン処理を実行する

        以下のフローを順に実行します：
            1. Loggerで処理開始を記録
            2. Skill_Analyzerでskills/ディレクトリを走査
            3. 各SKILL.mdファイルを解析
            4. Content_Generatorでカテゴリ分類とコンテンツ生成
            5. Markdown_Formatterで記事を整形
            6. 品質検証を実行
            7. 記事をファイルに保存
            8. Loggerで処理終了を記録

        エラーハンドリング（要件7.1〜7.5）:
            - SKILL.md読み込み失敗 / YAML解析失敗 / 必須フィールド欠如時は、
              SkillAnalyzer.parse_skill_file() がログを記録した上でNoneを返し、
              該当スキルはスキップされる（要件7.1, 7.2, 7.3）。
            - 処理完了時に成功/スキップ/エラー数をlog_end()で報告する（要件7.4）。
            - 有効なスキルが1件もない場合は処理を中止する（要件7.5）。

        Args:
            force: True の場合、出力ファイル保存時に既存ファイルを
                確認なしで上書きする（非対話実行向け）。

        Returns:
            処理結果を表すProcessingResultオブジェクト

        要件: 1.1〜1.6, 2.1〜2.3, 3.1〜3.10, 4.1〜4.8, 7.1〜7.5
        """
        result = ProcessingResult()

        # 1. 処理開始をログに記録
        self.logger.log_start()

        try:
            # 2. skills/ディレクトリを走査（要件1.1）
            self.logger.info(
                f"スキルディレクトリを走査中: {self.config.skills_directory}"
            )
            try:
                skill_files = self.analyzer.scan_skills_directory(
                    self.config.skills_directory
                )
            except (FileNotFoundError, NotADirectoryError) as e:
                # スキルディレクトリ自体が存在しない／不正な場合は処理を中止（要件7.5）
                self.logger.log_error(
                    message="スキルディレクトリの走査に失敗しました",
                    exception=e,
                    file_path=str(self.config.skills_directory),
                    cause=str(e),
                    solution="設定ファイルのskills_directoryを確認してください",
                )
                result.add_error(
                    "skills_directory",
                    f"スキルディレクトリの走査に失敗: {str(e)}",
                )
                # log_end は finally 句で呼び出されるためここでは呼ばない
                return result

            if not skill_files:
                # SKILL.mdが1つもない場合は処理を中止（要件7.5に準ずる）
                self.logger.log_warning(
                    message="SKILL.mdファイルが見つかりませんでした",
                    file_path=str(self.config.skills_directory),
                    cause="スキルディレクトリ配下にSKILL.mdが存在しません",
                    solution="skills/ディレクトリ配下にSKILL.mdを配置してください",
                )
                # log_end は finally 句で呼び出されるためここでは呼ばない
                return result

            # 3. 各SKILL.mdファイルを解析（要件1.2〜1.6, 7.1〜7.3）
            # parse_skill_file() 側で以下のログ記録を行う:
            #   - 要件7.1: ファイル読み込み失敗 → ERROR ログを記録して None を返す
            #   - 要件7.2: YAMLフロントマター解析失敗 → ERROR ログを記録して None を返す
            #   - 要件7.3: 必須フィールド欠如 → WARNING ログを記録して None を返す
            # ここでは None が返ってきたものをまとめてスキップ扱いにする。
            skills: List[SkillData] = []
            for skill_file in skill_files:
                skill_data = self.analyzer.parse_skill_file(skill_file)

                if skill_data is None:
                    # 解析失敗時はスキップ（要件7.1〜7.3）
                    skill_name = skill_file.parent.name
                    self.logger.log_skill_processed(skill_name, "skip")
                    result.add_skip(skill_name)
                    continue

                skills.append(skill_data)
                self.logger.log_skill_processed(skill_data.name, "success")
                result.add_success()

            # すべてのスキル処理が失敗した場合は処理を中止（要件7.5）
            if not skills:
                self.logger.log_error(
                    message="すべてのスキル処理に失敗しました。処理を中止します。",
                    cause=(
                        f"有効なSKILL.mdファイルが1つもありませんでした"
                        f"（スキップ: {result.skip_count}件）"
                    ),
                    solution=(
                        "SKILL.mdファイルの内容（YAMLフロントマター、"
                        "必須フィールドname/description）を確認してください"
                    ),
                )
                result.add_error(
                    "all_skills",
                    "すべてのスキル処理に失敗したため処理を中止しました",
                )
                # log_end は finally 句で呼び出されるためここでは呼ばない
                return result

            # 4. カテゴリ分類とコンテンツ生成（要件2.1〜2.3, 3.1〜3.10）
            self.logger.info("スキルをカテゴリに分類しています")
            categorized_skills = self.generator.categorize_skills(skills)

            self.logger.info("記事コンテンツを生成しています")
            content_sections = self._generate_content_sections(categorized_skills)

            # 5. 記事を整形（要件4.1〜4.8）
            self.logger.info("記事を整形しています")
            article = self.formatter.format_article(content_sections)

            # 6. 品質検証を実行（要件8.1〜8.10、詳細はタスク8.2で実装）
            self.logger.info("記事の品質を検証しています")
            self.validate_output(article, len(skills))

            # 7. 記事をファイルに保存（要件6.1〜6.5）
            output_path = self._build_output_path()
            saved_path = self.save_article(article, output_path, force=force)
            self.logger.log_output_file(saved_path)

        except Exception as e:
            # 予期しないエラー
            self.logger.log_error(
                message="メイン処理中に予期しないエラーが発生しました",
                exception=e,
                cause=f"{type(e).__name__}: {str(e)}",
                solution="ログの詳細を確認し、設定や入力ファイルを見直してください",
            )
            result.add_error("main_process", str(e))

        finally:
            # 8. 処理終了をログに記録
            self.logger.log_end(
                success_count=result.success_count,
                skip_count=result.skip_count,
                error_count=result.error_count,
            )

        return result

    def _generate_content_sections(
        self, categorized_skills: Dict[str, List[SkillData]]
    ) -> Dict[str, str]:
        """
        記事の各セクションを生成する

        Args:
            categorized_skills: カテゴリごとに分類されたスキル

        Returns:
            セクション名をキー、Markdownコンテンツを値とする辞書

        要件: 3.1〜3.10, 4.2
        """
        # 各セクションを生成
        sections: Dict[str, str] = {
            "title": self.config.article_title,
            "introduction": self.generator.generate_introduction(),
            "what_is_agent_skills": self.generator.generate_what_is_agent_skills(),
            "history": self.generator.generate_history_section(),
            "safety": self.generator.generate_safety_section(),
            "prerequisites": self.generator.generate_prerequisites_section(),
            "skills": self._generate_skills_section(categorized_skills),
            "conclusion": self.generator.generate_conclusion(),
        }

        return sections

    def _generate_skills_section(
        self, categorized_skills: Dict[str, List[SkillData]]
    ) -> str:
        """
        スキル一覧セクションを生成する

        各カテゴリ内でアルファベット順にスキルを並べ、
        各スキルの説明をMarkdownで構築します。スキル一覧の冒頭には
        ライセンスモデルを説明する「ライセンスについて」サブセクションを
        含めます（要件5.1〜5.4）。

        Args:
            categorized_skills: カテゴリごとに分類されたスキル

        Returns:
            スキル一覧セクションのMarkdownテキスト

        要件: 2.1〜2.3, 3.1〜3.5, 4.2, 4.6, 4.7, 5.1〜5.4
        """
        parts: List[str] = ["## スキル一覧", ""]

        # ライセンスモデルの概要を最初に説明する（要件5.1〜5.4）
        parts.append(self._generate_license_overview())
        parts.append("")

        # CATEGORY_ORDERの順に出力（要件2.1）。
        # CATEGORY_ORDERにない「その他」は最後に追加（要件2.2）。
        ordered_categories: List[str] = []
        for category in CATEGORY_ORDER:
            if category in categorized_skills and categorized_skills[category]:
                ordered_categories.append(category)
        for category in categorized_skills:
            if (
                category not in ordered_categories
                and categorized_skills[category]
            ):
                ordered_categories.append(category)

        # スキル一覧の俯瞰図（カテゴリ別の表）。スキル数が多いとMermaidツリーは
        # 縦長になって読みにくいため、表形式で簡潔に示す。
        if self.config.diagrams_enabled:
            tree_data = {
                cat: [s.name for s in categorized_skills[cat]]
                for cat in ordered_categories
            }
            parts.append(diagrams.category_table(tree_data))
            parts.append("")

        for category in ordered_categories:
            skills = categorized_skills[category]
            parts.append(f"### {category}")
            parts.append("")

            # アルファベット順に並べる（要件2.3）
            for skill in skills:
                parts.append(f"#### {skill.name}")
                parts.append("")
                description = self.generator.generate_skill_description(skill)
                parts.append(description)
                parts.append("")

        return "\n".join(parts)

    def _generate_license_overview(self) -> str:
        """
        スキル一覧セクション冒頭のライセンス概要を生成する

        Anthropic公式Agent Skillsのライセンスモデル（Apache 2.0と
        プロプライエタリの2種類）を説明し、ドキュメントスキル
        （docx、pdf、pptx、xlsx）がソース公開だがプロプライエタリで
        あることを明記します。

        Returns:
            ライセンス概要のMarkdownテキスト

        要件: 5.1, 5.2, 5.3, 5.4
        """
        return (
            "### ライセンスについて\n"
            "\n"
            "本記事で紹介するAnthropic公式Agent Skillsは、以下の2種類のライセンス"
            "モデルで提供されています。各スキルの説明にも、それぞれのライセンス"
            "種別を併記しています。\n"
            "\n"
            "- **Apache 2.0（オープンソース）**: ほとんどのサンプルスキルが"
            "対象です。商用・改変・再配布が可能で、企業内での利用にも適して"
            "います。各スキルディレクトリの`LICENSE.txt`に正式な条文が含まれて"
            "います。\n"
            "- **プロプライエタリ（ソース公開だが参照・学習用）**: ドキュメント"
            "スキル（`docx`、`pdf`、`pptx`、`xlsx`）が対象です。Anthropicの"
            "ドキュメント機能を支える本番品質のスキルパターンを学べるように"
            "ソースコードは公開されていますが、Apache 2.0のようなオープン"
            "ソースライセンスではありません。再配布や商用利用には各スキルの"
            "`LICENSE.txt`に記載された条件を必ず確認してください。\n"
            "\n"
            "なお、`SKILL.md`の`license`フィールドが`\"Complete terms in "
            "LICENSE.txt\"`のように汎用的な記述になっているスキルでも、"
            "実際の`LICENSE.txt`はApache 2.0です。一方、ドキュメントスキルは"
            "`license`フィールドに`\"Proprietary. LICENSE.txt has complete "
            "terms\"`と明示されています。\n"
            "\n"
            "#### ドキュメントスキル（`docx` / `pdf` / `pptx` / `xlsx`）の"
            "企業内・商用利用について\n"
            "\n"
            "ドキュメントスキルの`LICENSE.txt`はAnthropicが`© 2025 Anthropic, PBC. "
            "All rights reserved.`として権利を留保しており、利用条件はユーザーが"
            "Anthropicと結ぶ「Agreement」（個別契約、または[Consumer Terms of "
            "Service](https://www.anthropic.com/legal/consumer-terms) / "
            "[Commercial Terms of Service](https://www.anthropic.com/legal/"
            "commercial-terms)のいずれか該当する方）に従います。要点を整理すると"
            "次のとおりです。\n"
            "\n"
            "| # | 観点 | 結論 | 根拠（`LICENSE.txt`より要約） |\n"
            "|---|---|---|---|\n"
            "| 1 | 企業内での商用利用 | **可能**（条件付き） | "
            "Anthropicの**Commercial Terms of Service**または個別契約の範囲内で"
            "あれば、企業として業務目的に利用できる |\n"
            "| 2 | 利用形態 | **Anthropic自身が提供するサービス上での利用が前提** | "
            "Claude.ai / Claude API / Claude Code 等、Anthropicが提供する"
            "「Services」を介して使うことを基本とする。Microsoft Foundry / "
            "Kiro / Amazon Bedrockなど第三者経由の場合は別途扱いを要確認"
            "（後述） |\n"
            "| 3 | サービス外へのコピー保持 | **禁止** | サービス外にスキルを"
            "抽出・保管しないこと（テンポラリの自動コピーは除く） |\n"
            "| 4 | 派生物の作成 | **禁止** | スキルをベースにした派生物を"
            "作成してはならない |\n"
            "| 5 | 第三者への再配布・サブライセンス | **禁止** | 第三者への"
            "配布・サブライセンス・譲渡は不可 |\n"
            "| 6 | リバースエンジニアリング | **禁止** | デコンパイル・"
            "ディスアセンブル等は不可 |\n"
            "| 7 | 含まれる発明の商品化 | **禁止** | スキル内の発明を製造・"
            "販売・輸入することはできない |\n"
            "\n"
            "**つまり**「Claude.ai / Claude API / Claude Code 上でスキルを"
            "呼び出して業務文書（docx・pdf・pptx・xlsx）を生成する」ような"
            "通常の利用であれば、Anthropicとの契約条件下で**企業として商用利用"
            "可能**です。一方、スキルそのものを社内のローカル環境にコピーして"
            "改変したり、自社製品に組み込んで再配布したりすることは**契約違反"
            "になる**ため避けてください。\n"
            "\n"
            "##### サードパーティ経由（Kiro / Microsoft Foundry / Amazon Bedrock 等）"
            "での利用について\n"
            "\n"
            "ドキュメントスキルの`LICENSE.txt`は「Anthropic と結んだ Agreement に基づく "
            "Anthropic の Services 上での利用」を前提としています。Anthropic 以外の"
            "事業者が提供するサービス経由でClaudeを使う場合、利用規約の主体が変わる"
            "ため扱いが異なります。代表的なケースを整理します。\n"
            "\n"
            "| 利用ルート | 規約の主体 | ドキュメントスキルの扱い |\n"
            "|---|---|---|\n"
            "| Claude.ai / Claude API / Claude Code | Anthropic（直接） | "
            "`LICENSE.txt`の対象「Services」に該当。本記事の条件で利用可能 |\n"
            "| **Microsoft Foundry の Claude モデル** | "
            "Microsoftで購入するが、"
            "**Anthropic がデータ処理者**となり、Anthropic の[利用規約](https://"
            "www.anthropic.com/legal/commercial-terms)に同意することがMicrosoftの"
            "公式ドキュメントで明示されている | Claudeモデル自体はAnthropic規約下で"
            "利用可能だが、**ドキュメントスキル（docx 等）が Foundry 経由で公式配信"
            "されているかは別問題**。Foundryのモデルカタログにスキル本体が含まれない"
            "場合、`LICENSE.txt`の「サービス外への持ち出し禁止」に抵触する可能性が"
            "あるため、自前で取り込む前にAnthropicに確認 |\n"
            "| **Kiro（AWS提供のIDE）** | AWS（Amazon Web Services）。"
            "AnthropicとAWSは投資・提携関係にあるがKiro自体はAWSの独自製品 | "
            "Kiroが内部でClaudeをどのルートで呼ぶか（Bedrock経由か、Anthropic API"
            "直結か）で扱いが変わる。**Bedrock経由の場合は AWS の Service Terms と"
            "Bedrock個別規約**が適用される。スキルが Bedrock のスキルカタログとして"
            "配信されていない限り、`docx`等のドキュメントスキルの動作はサポート"
            "されていない可能性がある |\n"
            "| Amazon Bedrock の Claude モデル | AWS（Anthropic はサブプロセッサー） | "
            "上記Kiroと同様、AWSの規約が主体。スキルの公式配信状況は別途確認が必要 |\n"
            "\n"
            "**判断のポイント**: ドキュメントスキルの`LICENSE.txt`が言う"
            "「Anthropicの Services」とは、**Anthropic自身が提供・課金している"
            "サービス**を指すと読むのが自然です。サードパーティ（Microsoft、AWS等）"
            "経由でClaudeモデルを呼べる場合でも、`docx`/`pdf`/`pptx`/`xlsx`スキルの"
            "ような Anthropic の本番サービス用アセットが配信・利用許諾されている"
            "とは限りません。"
            "**サードパーティ経由でドキュメントスキルを業務利用したい場合は、必ず**"
            "**(1) その事業者の規約とスキルの配信状況を確認し、(2) 不明確であれば**"
            "**Anthropic 営業またはサードパーティのサポートに直接問い合わせる**"
            "ことを推奨します。\n"
            "\n"
            "**留意事項**: 上記は記事執筆時点の`LICENSE.txt`の記載と公開規約を"
            "もとにした要約であり、法的助言ではありません。実際の利用前には、"
            "（1）契約しているAnthropicの規約区分（Consumer / Commercialまたは"
            "個別契約）と最新の条文、（2）サードパーティ経由の場合はその事業者の"
            "規約と最新のサービス内容、（3）自社の法務・情報セキュリティ部門の"
            "判断、を必ず確認してください。"
        )

    def _build_output_path(self) -> Path:
        """
        出力ファイルのパスを構築する

        Returns:
            出力ファイルのパス（YYYY-MM-DD_<slug>.md形式）

        要件: 6.2
        """
        date_prefix = datetime.now().strftime("%Y-%m-%d")
        slug = sanitize_filename(self.config.article_title)
        # 半角スペースをハイフンに、コロンや読点を除去して短いファイル名に
        slug = re.sub(r"[\s　:：]+", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")
        if not slug:
            slug = "claude-agent-skills-guide"

        filename = f"{date_prefix}_{slug}.md"
        return self.config.output_directory / filename

    def validate_output(self, article: str, skills_count: int) -> bool:
        """
        出力記事の品質を検証する

        以下の観点で記事の品質を多面的に検証します：
            - 文字数（要件8.1）
            - すべてのカテゴリの包含（要件8.2）
            - 各スキルの説明が空でないこと（要件8.3）
            - Markdown記法の正しさ（要件8.4）
            - 安全性セクションの存在（要件8.6）
            - 前提ソフトウェアセクションの存在（要件8.7）
            - 見出しの初学者向け表現（要件8.8）
            - 見出しの階層構造の適切性（要件8.9）
            - 必須セクションの存在
        品質チェックに失敗したときは警告メッセージを表示し、問題箇所を報告します（要件8.10）。

        Args:
            article: 検証対象の記事
            skills_count: 処理したスキル数

        Returns:
            すべての品質チェックに合格した場合True、警告がある場合False

        要件: 8.1, 8.2, 8.3, 8.4, 8.6, 8.7, 8.8, 8.9, 8.10
        """
        warnings: List[str] = []

        # 1. 文字数チェック（要件8.1）
        warnings.extend(self._validate_article_length(article))

        # 2. カテゴリの存在チェック（要件8.2）
        warnings.extend(self._validate_categories_present(article))

        # 3. 必須セクションの存在チェック
        warnings.extend(self._validate_required_sections(article))

        # 4. 安全性セクションの存在チェック（要件8.6）
        warnings.extend(self._validate_safety_section(article))

        # 5. 前提ソフトウェアセクションの存在チェック（要件8.7）
        warnings.extend(self._validate_prerequisites_section(article))

        # 6. 各スキル説明が空でないことのチェック（要件8.3）
        warnings.extend(self._validate_skill_descriptions(article))

        # 7. Markdown記法の正しさを検証（要件8.4）
        warnings.extend(self._validate_markdown_syntax(article))

        # 8. 見出しの階層構造の適切性を検証（要件8.9）
        warnings.extend(self._validate_heading_hierarchy(article))

        # 9. 見出しが初学者向けの表現になっているかチェック（要件8.8）
        warnings.extend(self._validate_heading_readability(article))

        # 警告があればログに記録（要件8.10）
        if warnings:
            self.logger.log_warning(
                message=f"品質検証で{len(warnings)}件の問題を検出しました",
                cause="; ".join(warnings[:5])
                + ("..." if len(warnings) > 5 else ""),
                solution="ContentGeneratorまたはMarkdownFormatterの出力を確認してください",
            )
            for warning in warnings:
                self.logger.log_warning(
                    message="品質検証で問題を検出しました",
                    cause=warning,
                    solution="該当セクションの生成ロジックを確認してください",
                )
        else:
            self.logger.info("品質検証: すべてのチェックに合格しました")

        return len(warnings) == 0

    def _validate_article_length(self, article: str) -> List[str]:
        """記事の文字数が最小要件を満たしているか検証する（要件8.1）"""
        warnings: List[str] = []
        article_length = len(article)
        if article_length < MIN_ARTICLE_LENGTH:
            warnings.append(
                f"記事の文字数が不足しています: {article_length}文字"
                f"（最小: {MIN_ARTICLE_LENGTH}文字）"
            )
        return warnings

    def _validate_categories_present(self, article: str) -> List[str]:
        """設定で指定されたすべてのカテゴリが記事に含まれているか検証する（要件8.2）"""
        warnings: List[str] = []
        for category in self.config.included_categories:
            if category not in article:
                warnings.append(
                    f"カテゴリが記事に含まれていません: {category}"
                )
        return warnings

    def _validate_required_sections(self, article: str) -> List[str]:
        """必須セクション（はじめに、まとめ等）が記事に含まれているか検証する"""
        warnings: List[str] = []
        for section in REQUIRED_SECTIONS:
            if section not in article:
                warnings.append(f"必須セクションが見つかりません: {section}")
        return warnings

    def _validate_safety_section(self, article: str) -> List[str]:
        """安全性に関するセクションが記事に含まれているか検証する（要件8.6）"""
        warnings: List[str] = []
        # 「Agent Skillsの安全性とリスク」または「安全性」セクションのいずれかを確認
        if (
            "安全性とリスク" not in article
            and "## Agent Skillsの安全性" not in article
        ):
            warnings.append(
                "安全性に関するセクションが見つかりません: "
                "「Agent Skillsの安全性とリスク」セクションを含める必要があります"
            )
        # サブセクションの存在も確認
        safety_subsections = [
            "公式Agent Skills",
            "ベンダー提供Agent Skills",
            "野良Agent Skills",
        ]
        missing_subsections = [
            sub for sub in safety_subsections if sub not in article
        ]
        if missing_subsections:
            warnings.append(
                f"安全性セクションのサブセクションが不足しています: "
                f"{', '.join(missing_subsections)}"
            )
        return warnings

    def _validate_prerequisites_section(self, article: str) -> List[str]:
        """前提ソフトウェアに関するセクションが記事に含まれているか検証する（要件8.7）"""
        warnings: List[str] = []
        if "前提ソフトウェア" not in article:
            warnings.append(
                "前提ソフトウェアに関するセクションが見つかりません: "
                "「Agent Skillsを利用・開発するための前提ソフトウェア」セクションを"
                "含める必要があります"
            )
        # 必須キーワードの存在確認（IDE、CLI、開発環境）
        prerequisite_keywords = ["IDE", "CLI"]
        missing_keywords = [
            kw for kw in prerequisite_keywords if kw not in article
        ]
        if missing_keywords:
            warnings.append(
                f"前提ソフトウェアセクションに重要なキーワードが不足しています: "
                f"{', '.join(missing_keywords)}"
            )
        return warnings

    def _validate_skill_descriptions(self, article: str) -> List[str]:
        """各スキル（H4見出し）の説明が空でないことを検証する（要件8.3）"""
        warnings: List[str] = []
        # H4見出し（####）以下の本文を取得
        # H4 = 個別スキルの見出し
        h4_pattern = re.compile(r"^####\s+(.+)$", re.MULTILINE)
        h4_matches = list(h4_pattern.finditer(article))

        for match in h4_matches:
            skill_name = match.group(1).strip()
            # 次のH1〜H4見出しまでを本文とする
            start = match.end()
            # 次の見出し（H1〜H4のいずれか）を探す
            next_heading_match = re.search(
                r"^#{1,4}\s+", article[start:], re.MULTILINE
            )
            if next_heading_match:
                end = start + next_heading_match.start()
            else:
                end = len(article)
            body = article[start:end].strip()
            if not body:
                warnings.append(
                    f"スキル説明が空です: {skill_name}"
                )
        return warnings

    def _validate_markdown_syntax(self, article: str) -> List[str]:
        """Markdown記法の正しさを検証する（要件8.4）"""
        warnings: List[str] = []

        # 1. H1見出しは1つだけであること（記事タイトル）
        h1_pattern = re.compile(r"^#\s+", re.MULTILINE)
        h1_count = len(h1_pattern.findall(article))
        if h1_count == 0:
            warnings.append("H1見出し（記事タイトル）が見つかりません")
        elif h1_count > 1:
            warnings.append(
                f"H1見出しが複数あります: {h1_count}個"
                f"（記事タイトルは1つのみであるべき）"
            )

        # 2. 見出し記法（# の後にスペース）が正しいこと
        # # の後にスペースなしで文字が続く場合は記法エラー
        invalid_heading_pattern = re.compile(r"^#{1,6}[^\s#]", re.MULTILINE)
        invalid_headings = invalid_heading_pattern.findall(article)
        if invalid_headings:
            warnings.append(
                f"不正な見出し記法が検出されました: {len(invalid_headings)}件"
                f"（# の後にスペースが必要です）"
            )

        # 3. コードブロックが正しく閉じられていること（``` のペア）
        # コードブロック開始（言語指定あり/なし）と終了
        code_fence_count = len(re.findall(r"^```", article, re.MULTILINE))
        if code_fence_count % 2 != 0:
            warnings.append(
                f"コードブロックが正しく閉じられていません: "
                f"```マーカーが{code_fence_count}個（偶数である必要があります）"
            )

        # 4. リンク記法 [text](url) の妥当性
        # 空のリンクテキストやURLをチェック
        empty_link_pattern = re.compile(r"\[\s*\]\([^)]+\)|\[[^\]]+\]\(\s*\)")
        empty_links = empty_link_pattern.findall(article)
        if empty_links:
            warnings.append(
                f"空のリンクテキストまたはURLが検出されました: {len(empty_links)}件"
            )

        return warnings

    def _validate_heading_hierarchy(self, article: str) -> List[str]:
        """見出しの階層構造が適切かを検証する（要件8.9）

        - 見出しレベルが2つ以上飛ばないこと（例: H2の直後にH4は不可）
        - 記事の論理的な階層構造が保たれていること
        """
        warnings: List[str] = []
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        headings: List[Tuple[int, str]] = [
            (len(m.group(1)), m.group(2).strip())
            for m in heading_pattern.finditer(article)
        ]

        if not headings:
            warnings.append("見出しが1つも見つかりません")
            return warnings

        # 見出しレベルが2つ以上飛んでいないかチェック
        prev_level = 0
        for level, text in headings:
            if prev_level > 0 and level > prev_level + 1:
                warnings.append(
                    f"見出しレベルが飛んでいます: H{prev_level}の直後にH{level}"
                    f"（見出し: 「{text}」）"
                )
            prev_level = level

        # 期待される論理構造のチェック
        # H1（タイトル）→ H2（主要セクション）→ H3（サブ）→ H4（個別スキル）
        levels = [lvl for lvl, _ in headings]
        if levels and levels[0] != 1:
            warnings.append(
                f"記事はH1見出し（タイトル）から始まる必要があります。"
                f"検出された最初の見出しレベル: H{levels[0]}"
            )

        # H4見出し（個別スキル）が存在する場合、その親（H3）が存在することを確認
        for i, (level, text) in enumerate(headings):
            if level == 4:
                # 直前のH3を探す
                has_parent_h3 = False
                for j in range(i - 1, -1, -1):
                    parent_level = headings[j][0]
                    if parent_level == 3:
                        has_parent_h3 = True
                        break
                    if parent_level < 3:
                        break
                if not has_parent_h3:
                    warnings.append(
                        f"H4見出し「{text}」に対応するH3親見出しが見つかりません"
                    )

        return warnings

    def _validate_heading_readability(self, article: str) -> List[str]:
        """見出しが初学者向けの表現になっているかを検証する（要件8.8）

        - H2見出しが期待される論理的な流れに沿っているか
        - 見出しテキストが空でないこと
        """
        warnings: List[str] = []
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

        for match in heading_pattern.finditer(article):
            level = len(match.group(1))
            text = match.group(2).strip()
            if not text:
                warnings.append(f"H{level}見出しのテキストが空です")
            # 見出しテキストが極端に短い場合（1文字など）は警告
            elif len(text) < 2:
                warnings.append(
                    f"H{level}見出しのテキストが短すぎます: 「{text}」"
                )

        return warnings

    def save_article(
        self,
        article: str,
        output_path: Path,
        force: bool = False,
        prompt_func: Optional[Callable[[str], str]] = None,
    ) -> Path:
        """
        記事をファイルに保存する

        ファイル保存時は以下を行います：
            - 出力先ディレクトリが存在しない場合は作成（要件6.4）
            - UTF-8エンコーディングで保存（要件6.3）
            - 同名ファイルが存在する場合は上書き確認（要件6.5）

        上書き確認の挙動:
            - ``force=True`` の場合は確認なしで上書きします。
            - ``prompt_func`` を渡した場合はそれを使って確認します
              （テストや非対話実行で利用可能）。
            - 既定では ``input()`` で対話的に確認します。標準入力が利用できない
              非対話実行（``sys.stdin`` が tty でないなど）では、衝突を避けるため
              ファイル名末尾に連番を付与した一意のパスへ自動的に保存します。

        Args:
            article: 保存する記事
            output_path: 出力ファイルのパス
            force: True の場合、確認なしで上書きする
            prompt_func: 上書き確認に使用する関数（``input`` 互換）。
                指定しない場合は ``input()`` を使用する。

        Returns:
            実際に保存したファイルのパス。上書きをスキップした場合や
            自動的に別名保存した場合は元の output_path と異なる場合がある。

        要件: 6.1, 6.2, 6.3, 6.4, 6.5
        """
        # 出力ディレクトリを作成（要件6.4）
        ensure_directory_exists(output_path.parent)

        # 同名ファイルが存在する場合の上書き確認（要件6.5）
        target_path = output_path
        if target_path.exists() and not force:
            should_overwrite = self._confirm_overwrite(
                target_path, prompt_func
            )
            if not should_overwrite:
                # 上書きしない場合は、一意なファイル名で保存する
                target_path = self._build_unique_path(output_path)
                self.logger.info(
                    f"上書きをスキップし、別名で保存します: {target_path}"
                )

        # UTF-8エンコーディングで保存（要件6.1, 6.3）
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(article)

        return target_path

    def _confirm_overwrite(
        self,
        target_path: Path,
        prompt_func: Optional[Callable[[str], str]] = None,
    ) -> bool:
        """
        既存ファイルの上書き確認を行う

        対話的に実行されている場合は ``input()`` で y/n を尋ねます。
        標準入力が利用できない場合（パイプ実行、テスト等）は False を返し、
        呼び出し側で別名保存などの代替手段を取れるようにします。

        Args:
            target_path: 確認対象のファイルパス
            prompt_func: 入力取得関数（テストや代替実装用）。
                未指定の場合は組み込み ``input`` を使用する。

        Returns:
            上書きする場合は True、上書きしない場合は False
        """
        # 明示的なプロンプト関数が渡された場合は常にそれを使う
        if prompt_func is None:
            # 標準入力が利用できない場合は対話せずFalseを返す
            if not sys.stdin or not sys.stdin.isatty():
                self.logger.log_warning(
                    message="既存ファイルが存在しますが対話モードではないため、別名で保存します",
                    file_path=str(target_path),
                    cause="標準入力が対話モードではない",
                    solution="上書きしたい場合は force=True を指定してください",
                )
                return False
            prompt_func = input

        prompt_message = (
            f"ファイルが既に存在します: {target_path}\n"
            f"上書きしますか? [y/N]: "
        )
        try:
            answer = prompt_func(prompt_message)
        except (EOFError, KeyboardInterrupt):
            # 入力が取得できない/中断された場合は上書きしない
            return False

        return str(answer).strip().lower() in ("y", "yes")

    @staticmethod
    def _build_unique_path(output_path: Path) -> Path:
        """
        既存ファイルと衝突しない一意のパスを生成する

        ``foo.md`` が既に存在する場合は ``foo_1.md``、``foo_2.md`` のように
        連番を付与したパスを返します。

        Args:
            output_path: 元の出力パス

        Returns:
            既存ファイルと衝突しない一意のパス
        """
        if not output_path.exists():
            return output_path

        stem = output_path.stem
        suffix = output_path.suffix
        parent = output_path.parent
        counter = 1
        while True:
            candidate = parent / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1
