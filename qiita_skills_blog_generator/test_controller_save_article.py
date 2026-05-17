"""
MainController.save_article() のユニットテスト

タスク8.3のファイル保存機能を検証します。
要件: 6.1, 6.2, 6.3, 6.4, 6.5
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from qiita_skills_blog_generator.controller import MainController


class SaveArticleTests(unittest.TestCase):
    """save_article() のファイル保存ロジックを検証する"""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        # MainControllerのLoggerを差し替えて、ログファイルを実機に書かない
        with patch("qiita_skills_blog_generator.controller.Logger") as mock_logger_cls:
            self.controller = MainController(config_path=None)
        self.controller.logger = mock_logger_cls.return_value

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    # 要件6.1: 記事をMarkdownファイルとして出力する
    def test_save_article_writes_content_to_file(self) -> None:
        article = "# タイトル\n\n本文です。"
        output_path = Path(self.tempdir.name) / "article.md"
        saved_path = self.controller.save_article(article, output_path)

        self.assertTrue(saved_path.exists())
        self.assertEqual(saved_path, output_path)
        self.assertEqual(saved_path.read_text(encoding="utf-8"), article)

    # 要件6.3: UTF-8エンコーディングでファイルを保存する
    def test_save_article_uses_utf8_encoding(self) -> None:
        article = "# タイトル\n\n日本語の本文です。絵文字も含みます: 🎉"
        output_path = Path(self.tempdir.name) / "article.md"
        saved_path = self.controller.save_article(article, output_path)

        # UTF-8でデコードして読み取れることを確認
        # （テキストモードでの読み取り = 改行コード変換も含めUTF-8 round-trip）
        self.assertEqual(saved_path.read_text(encoding="utf-8"), article)

        # 非ASCII文字（日本語・絵文字）がUTF-8バイト列で書き込まれていることを確認
        with open(saved_path, "rb") as f:
            raw_bytes = f.read()
        # 日本語 「タ」 の UTF-8 バイト列
        self.assertIn("タイトル".encode("utf-8"), raw_bytes)
        # 絵文字 🎉 の UTF-8 バイト列
        self.assertIn("🎉".encode("utf-8"), raw_bytes)

    # 要件6.4: 出力先ディレクトリが存在しない場合は作成する
    def test_save_article_creates_missing_output_directory(self) -> None:
        article = "# 本文"
        output_path = (
            Path(self.tempdir.name) / "missing" / "subdir" / "article.md"
        )
        self.assertFalse(output_path.parent.exists())

        saved_path = self.controller.save_article(article, output_path)

        self.assertTrue(saved_path.parent.exists())
        self.assertTrue(saved_path.exists())

    # 要件6.5: 同名のファイルが既に存在するときは上書き確認を行う
    def test_save_article_overwrites_when_force_is_true(self) -> None:
        output_path = Path(self.tempdir.name) / "article.md"
        output_path.write_text("古い内容", encoding="utf-8")

        new_article = "新しい内容"
        saved_path = self.controller.save_article(
            new_article, output_path, force=True
        )

        self.assertEqual(saved_path, output_path)
        self.assertEqual(saved_path.read_text(encoding="utf-8"), new_article)

    def test_save_article_overwrites_when_user_confirms_yes(self) -> None:
        output_path = Path(self.tempdir.name) / "article.md"
        output_path.write_text("古い内容", encoding="utf-8")

        new_article = "新しい内容"
        saved_path = self.controller.save_article(
            new_article,
            output_path,
            prompt_func=lambda _msg: "y",
        )

        self.assertEqual(saved_path, output_path)
        self.assertEqual(saved_path.read_text(encoding="utf-8"), new_article)

    def test_save_article_keeps_original_when_user_declines(self) -> None:
        output_path = Path(self.tempdir.name) / "article.md"
        output_path.write_text("古い内容", encoding="utf-8")

        new_article = "新しい内容"
        saved_path = self.controller.save_article(
            new_article,
            output_path,
            prompt_func=lambda _msg: "n",
        )

        # 元のファイルは保持される
        self.assertEqual(output_path.read_text(encoding="utf-8"), "古い内容")
        # 別名で新規ファイルが保存される
        self.assertNotEqual(saved_path, output_path)
        self.assertTrue(saved_path.exists())
        self.assertEqual(saved_path.read_text(encoding="utf-8"), new_article)
        # 連番付きファイル名であることを確認
        self.assertEqual(saved_path.suffix, ".md")
        self.assertTrue(saved_path.stem.startswith(output_path.stem + "_"))

    def test_save_article_generates_unique_path_for_multiple_collisions(
        self,
    ) -> None:
        base_dir = Path(self.tempdir.name)
        original = base_dir / "article.md"
        original.write_text("元", encoding="utf-8")
        (base_dir / "article_1.md").write_text("既存1", encoding="utf-8")
        (base_dir / "article_2.md").write_text("既存2", encoding="utf-8")

        saved_path = self.controller.save_article(
            "新しい内容",
            original,
            prompt_func=lambda _msg: "no",
        )

        # 既存と衝突しない連番が選ばれる
        self.assertEqual(saved_path.name, "article_3.md")
        self.assertEqual(saved_path.read_text(encoding="utf-8"), "新しい内容")

    def test_save_article_handles_eof_error_in_prompt(self) -> None:
        output_path = Path(self.tempdir.name) / "article.md"
        output_path.write_text("古い内容", encoding="utf-8")

        def raise_eof(_msg: str) -> str:
            raise EOFError()

        saved_path = self.controller.save_article(
            "新しい内容",
            output_path,
            prompt_func=raise_eof,
        )

        # 上書きせず別名で保存される
        self.assertNotEqual(saved_path, output_path)
        self.assertEqual(output_path.read_text(encoding="utf-8"), "古い内容")
        self.assertEqual(saved_path.read_text(encoding="utf-8"), "新しい内容")

    # 要件6.2: ファイル名に日付とタイトルを含める
    def test_build_output_path_includes_date_and_title(self) -> None:
        path = self.controller._build_output_path()
        # YYYY-MM-DD_<slug>.md 形式
        self.assertEqual(path.suffix, ".md")
        # 日付プレフィックスを検証（先頭に YYYY-MM-DD_ がある）
        import re

        self.assertRegex(path.name, r"^\d{4}-\d{2}-\d{2}_.+\.md$")
        # 出力先ディレクトリが設定の output_directory と一致
        self.assertEqual(path.parent, self.controller.config.output_directory)


if __name__ == "__main__":
    unittest.main()
