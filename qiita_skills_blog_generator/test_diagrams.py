"""
diagrams モジュールのユニットテスト
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from qiita_skills_blog_generator import diagrams


class MermaidBlockTests(unittest.TestCase):
    def test_mermaid_block_wraps_in_code_fence(self) -> None:
        result = diagrams.mermaid_block("flowchart TD\n    A --> B")
        self.assertTrue(result.startswith("```mermaid\n"))
        self.assertIn("flowchart TD", result)
        self.assertIn("A --> B", result)
        self.assertIn("\n```\n", result)

    def test_mermaid_block_includes_caption(self) -> None:
        result = diagrams.mermaid_block(
            "graph LR\nA --> B", caption="サンプル"
        )
        self.assertIn("*図: サンプル*", result)


class PlantumlBlockTests(unittest.TestCase):
    def test_plantuml_block_adds_start_end_markers(self) -> None:
        result = diagrams.plantuml_block("Alice -> Bob: Hello")
        self.assertIn("@startuml", result)
        self.assertIn("Alice -> Bob: Hello", result)
        self.assertIn("@enduml", result)
        self.assertIn("```plantuml", result)
        self.assertIn("```", result)

    def test_plantuml_block_keeps_existing_markers(self) -> None:
        code = "@startuml\nstart\nstop\n@enduml"
        result = diagrams.plantuml_block(code)
        # @startuml が二重にならない
        self.assertEqual(result.count("@startuml"), 1)
        self.assertEqual(result.count("@enduml"), 1)


class SaveSvgTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.images_dir = Path(self.tempdir.name) / "images"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_save_svg_writes_file_and_returns_markdown(self) -> None:
        svg = "<svg xmlns='http://www.w3.org/2000/svg'/>"

        result = diagrams.save_svg(
            svg_content=svg,
            images_dir=self.images_dir,
            filename="my-diagram",
            images_url_prefix="images",
            alt_text="テスト図",
            caption="テストキャプション",
        )

        # ファイルが output/images/my-diagram.svg に保存される
        saved = self.images_dir / "my-diagram.svg"
        self.assertTrue(saved.exists())
        self.assertEqual(saved.read_text(encoding="utf-8"), svg)

        # Markdown 参照が返る
        self.assertIn("![テスト図](images/my-diagram.svg)", result)
        self.assertIn("*図: テストキャプション*", result)

    def test_save_svg_creates_missing_directory(self) -> None:
        nested = self.images_dir / "deep" / "nested"
        diagrams.save_svg(
            svg_content="<svg/>",
            images_dir=nested,
            filename="x",
        )
        self.assertTrue((nested / "x.svg").exists())

    def test_save_svg_sanitizes_unsafe_filename(self) -> None:
        result = diagrams.save_svg(
            svg_content="<svg/>",
            images_dir=self.images_dir,
            filename="my:weird/name?.svg",
        )
        # コロンやスラッシュ、クエスチョンマークはハイフンに変換
        # かつ拡張子は1つだけ
        files = list(self.images_dir.glob("*.svg"))
        self.assertEqual(len(files), 1)
        self.assertNotIn(":", files[0].name)
        self.assertNotIn("?", files[0].name)
        # 戻り値の URL も同じファイル名になっている
        self.assertIn(files[0].name, result)


class PrebuiltDiagramTests(unittest.TestCase):
    def test_progressive_disclosure_returns_mermaid(self) -> None:
        result = diagrams.progressive_disclosure_mermaid()
        self.assertIn("```mermaid", result)
        self.assertIn("レベル1", result)
        self.assertIn("レベル2", result)
        self.assertIn("レベル3", result)

    def test_skill_structure_returns_mermaid(self) -> None:
        result = diagrams.skill_structure_mermaid()
        self.assertIn("```mermaid", result)
        self.assertIn("SKILL.md", result)
        self.assertIn("scripts/", result)

    def test_safety_comparison_returns_mermaid(self) -> None:
        result = diagrams.safety_comparison_mermaid()
        self.assertIn("```mermaid", result)
        self.assertIn("公式", result)
        self.assertIn("ベンダー提供", result)
        self.assertIn("野良", result)

    def test_safety_decision_plantuml(self) -> None:
        result = diagrams.safety_decision_plantuml()
        self.assertIn("```plantuml", result)
        self.assertIn("@startuml", result)
        self.assertIn("@enduml", result)
        self.assertIn("情報セキュリティ部門", result)

    def test_usage_sequence_mermaid(self) -> None:
        result = diagrams.usage_sequence_mermaid()
        self.assertIn("```mermaid", result)
        self.assertIn("sequenceDiagram", result)
        self.assertIn("ユーザー", result)

    def test_category_tree_mermaid(self) -> None:
        data = {
            "クリエイティブ&デザイン": ["algorithmic-art", "canvas-design"],
            "ドキュメント処理": ["docx", "pdf"],
        }
        result = diagrams.category_tree_mermaid(data)
        self.assertIn("```mermaid", result)
        self.assertIn("クリエイティブ&デザイン", result)
        self.assertIn("algorithmic-art", result)
        self.assertIn("docx", result)

    def test_system_overview_svg_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            images_dir = Path(td) / "images"
            result = diagrams.system_overview_svg(images_dir)
            self.assertTrue(
                (images_dir / "agent-skills-overview.svg").exists()
            )
            self.assertIn("agent-skills-overview.svg", result)


if __name__ == "__main__":
    unittest.main()
