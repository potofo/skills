"""
MainController のライセンス情報処理に関するユニットテスト

タスク8.4のライセンス情報処理ロジックを検証します。
要件: 5.1, 5.2, 5.3, 5.4

要件の対応関係:
    5.1: スキルにlicenseフィールドが存在するとき、ライセンス情報を記事に含める
    5.2: Apache 2.0ライセンスとプロプライエタリライセンスを区別して表示する
    5.3: ドキュメントスキル（docx、pdf、pptx、xlsx）がソース公開だが
         プロプライエタリであることを明記する
    5.4: 各スキルの説明にライセンス種別を簡潔に記載する
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from qiita_skills_blog_generator.config import Config, SkillData
from qiita_skills_blog_generator.constants import DOCUMENT_SKILLS
from qiita_skills_blog_generator.content_generator import ContentGenerator
from qiita_skills_blog_generator.controller import MainController


def _build_controller() -> MainController:
    """
    テスト用に、ログを実ファイルに書かない MainController を生成する。
    """
    with patch("qiita_skills_blog_generator.controller.Logger") as mock_logger_cls:
        controller = MainController(config_path=None)
    controller.logger = mock_logger_cls.return_value
    return controller


class LicenseOverviewTests(unittest.TestCase):
    """_generate_license_overview() のライセンス概要セクションを検証する"""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.controller = _build_controller()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    # 要件5.2: Apache 2.0 と プロプライエタリ を区別して表示する
    def test_overview_distinguishes_apache_and_proprietary(self) -> None:
        overview = self.controller._generate_license_overview()

        self.assertIn("Apache 2.0", overview)
        self.assertIn("オープンソース", overview)
        self.assertIn("プロプライエタリ", overview)

    # 要件5.3: ドキュメントスキルがソース公開だがプロプライエタリであることを明記
    def test_overview_explains_document_skills_are_source_available_proprietary(
        self,
    ) -> None:
        overview = self.controller._generate_license_overview()

        # ドキュメントスキルが列挙されている
        for doc_skill in DOCUMENT_SKILLS:
            self.assertIn(doc_skill, overview)
        # 「ソース公開」かつ「プロプライエタリ」と明記
        self.assertIn("ソース公開", overview)
        self.assertIn("プロプライエタリ", overview)

    # 要件4.2: ライセンス概要が「ライセンスについて」H3サブセクションとして配置される
    def test_overview_uses_h3_subsection_heading(self) -> None:
        overview = self.controller._generate_license_overview()

        self.assertIn("### ライセンスについて", overview)


class SkillsSectionLicenseTests(unittest.TestCase):
    """_generate_skills_section() がライセンス情報を含めることを検証する"""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.controller = _build_controller()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _build_categorized_skills(self) -> dict:
        """
        テスト用のカテゴリ別スキル辞書を生成する。
        Apache 2.0スキル、プロプライエタリスキル、ドキュメントスキルを含める。
        """
        return {
            "クリエイティブ&デザイン": [
                SkillData(
                    name="algorithmic-art",
                    description="Apache 2.0ライセンスのスキルです。",
                    license="Complete terms in LICENSE.txt",
                ),
            ],
            "開発&技術": [
                SkillData(
                    name="claude-api",
                    description="Apache 2.0ライセンスのAPIスキルです。",
                    license="Complete terms in LICENSE.txt",
                ),
            ],
            "ドキュメント処理": [
                SkillData(
                    name="docx",
                    description="Word文書を扱うプロプライエタリスキルです。",
                    license="Proprietary. LICENSE.txt has complete terms",
                ),
                SkillData(
                    name="pdf",
                    description="PDFを扱うプロプライエタリスキルです。",
                    license="Proprietary. LICENSE.txt has complete terms",
                ),
            ],
        }

    # 要件5.1: スキルにlicenseフィールドが存在するとき、ライセンス情報を記事に含める
    def test_skills_section_includes_license_info_for_each_skill(self) -> None:
        section = self.controller._generate_skills_section(
            self._build_categorized_skills()
        )

        # 各スキルの説明にライセンスラベルが含まれる
        # （ContentGeneratorが毎スキル必ずライセンスラベルを付与する）
        license_labels = section.count("（ライセンス: ")
        self.assertGreaterEqual(
            license_labels,
            4,
            "各スキルの説明にライセンス情報が含まれる必要があります",
        )

    # 要件5.2: Apache 2.0 と プロプライエタリ を区別して表示する
    def test_skills_section_distinguishes_apache_and_proprietary(self) -> None:
        section = self.controller._generate_skills_section(
            self._build_categorized_skills()
        )

        # Apache 2.0 と プロプライエタリ の両方が記事に登場する
        self.assertIn("Apache 2.0", section)
        self.assertIn("プロプライエタリ", section)

    # 要件5.3: ドキュメントスキル（docx、pdf、pptx、xlsx）が
    #          ソース公開だがプロプライエタリであることを明記する
    def test_skills_section_marks_document_skills_as_source_available_proprietary(
        self,
    ) -> None:
        section = self.controller._generate_skills_section(
            self._build_categorized_skills()
        )

        # docx/pdfスキルの説明エリアが「プロプライエタリ」かつ「ソース公開」を含む
        # まずdocxセクションを切り出す
        docx_index = section.index("#### docx")
        docx_section = section[docx_index : docx_index + 500]
        self.assertIn("プロプライエタリ", docx_section)
        self.assertIn("ソース公開", docx_section)

        pdf_index = section.index("#### pdf")
        pdf_section = section[pdf_index : pdf_index + 500]
        self.assertIn("プロプライエタリ", pdf_section)
        self.assertIn("ソース公開", pdf_section)

    # 要件5.4: 各スキルの説明にライセンス種別を簡潔に記載する
    def test_skills_section_each_skill_has_license_label(self) -> None:
        section = self.controller._generate_skills_section(
            self._build_categorized_skills()
        )

        # 各スキル見出しの直後の本文ブロックにライセンスラベルが入っていることを確認
        # H4見出しごとに、次のH3/H4までの本文を取り出して、ライセンスラベルを検証
        skill_names = ["algorithmic-art", "claude-api", "docx", "pdf"]
        for skill_name in skill_names:
            heading = f"#### {skill_name}"
            self.assertIn(heading, section, f"{skill_name} の見出しが見つかりません")

            # 見出し直後の本文を切り出す
            heading_index = section.index(heading) + len(heading)
            # 次の H3/H4 見出しを探す
            next_h3 = section.find("\n### ", heading_index)
            next_h4 = section.find("\n#### ", heading_index)
            candidates = [pos for pos in (next_h3, next_h4) if pos != -1]
            end = min(candidates) if candidates else len(section)
            body = section[heading_index:end]

            self.assertIn(
                "（ライセンス: ",
                body,
                f"{skill_name} の説明にライセンスラベルが見つかりません",
            )

    # 要件5.1, 4.2: ライセンス概要サブセクションがスキル一覧の冒頭に配置される
    def test_skills_section_starts_with_license_overview(self) -> None:
        section = self.controller._generate_skills_section(
            self._build_categorized_skills()
        )

        license_overview_index = section.find("### ライセンスについて")
        creative_category_index = section.find("### クリエイティブ&デザイン")
        self.assertNotEqual(
            license_overview_index,
            -1,
            "ライセンス概要サブセクションが含まれている必要があります",
        )
        self.assertNotEqual(
            creative_category_index,
            -1,
            "カテゴリ見出しが含まれている必要があります",
        )
        # ライセンス概要は最初のカテゴリより前に置かれる
        self.assertLess(license_overview_index, creative_category_index)


class ContentGeneratorLicenseLabelTests(unittest.TestCase):
    """ContentGenerator のライセンスラベル生成ロジックを検証する

    Main Controller がライセンス情報を組み立てる際の基盤となる
    ContentGenerator の責務を、要件5.1〜5.4の観点から検証する。
    """

    def setUp(self) -> None:
        self.config = Config.default()
        self.generator = ContentGenerator(self.config)

    # 要件5.2: Apache 2.0 ライセンスのスキルは Apache 2.0 として表示
    def test_apache_skill_label_uses_apache_2_0(self) -> None:
        skill = SkillData(
            name="algorithmic-art",
            description="dummy",
            license="Complete terms in LICENSE.txt",
        )

        label = self.generator.format_license_label(skill)

        self.assertIn("Apache 2.0", label)
        self.assertIn("オープンソース", label)
        self.assertNotIn("プロプライエタリ", label)

    # 要件5.2: プロプライエタリと明示されたスキルはプロプライエタリとして表示
    def test_proprietary_skill_label_uses_proprietary(self) -> None:
        skill = SkillData(
            name="some-proprietary",
            description="dummy",
            license="Proprietary. LICENSE.txt has complete terms",
        )

        label = self.generator.format_license_label(skill)

        self.assertIn("プロプライエタリ", label)
        self.assertNotIn("Apache 2.0", label)

    # 要件5.3: ドキュメントスキルはプロプライエタリ＆ソース公開と明記
    def test_document_skill_label_marks_source_available_proprietary(self) -> None:
        for doc_skill_name in DOCUMENT_SKILLS:
            with self.subTest(doc_skill=doc_skill_name):
                skill = SkillData(
                    name=doc_skill_name,
                    description="dummy",
                    license="Proprietary. LICENSE.txt has complete terms",
                )

                label = self.generator.format_license_label(skill)

                self.assertIn("プロプライエタリ", label)
                self.assertIn("ソース公開", label)

    # 要件5.1, 5.4: license フィールドが存在する場合、説明にラベルが含まれる
    def test_skill_description_includes_license_label_when_license_present(
        self,
    ) -> None:
        skill = SkillData(
            name="algorithmic-art",
            description="アルゴリズムでアートを生成するスキル。",
            license="Complete terms in LICENSE.txt",
        )

        description = self.generator.generate_skill_description(skill)

        self.assertIn("（ライセンス: ", description)
        self.assertIn("Apache 2.0", description)


if __name__ == "__main__":
    unittest.main()
