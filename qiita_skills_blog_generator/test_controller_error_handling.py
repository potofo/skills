"""
MainController のエラーハンドリングに関するユニットテスト

タスク8.5のエラーハンドリングロジックを検証します。
要件: 7.1, 7.2, 7.3, 7.4, 7.5

要件の対応関係:
    7.1: SKILL.mdファイルの読み込みに失敗したとき、ログに記録してスキップする
    7.2: YAMLフロントマターの解析に失敗したとき、ログに記録してスキップする
    7.3: 必須フィールド（name、description）が欠けているとき、警告ログを記録してスキップする
    7.4: 処理完了時に、成功したスキル数とスキップしたスキル数を報告する
    7.5: すべてのスキルの処理に失敗したとき、エラーメッセージを表示し処理を中止する
"""

import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from qiita_skills_blog_generator.config import Config
from qiita_skills_blog_generator.controller import MainController
from qiita_skills_blog_generator.skill_analyzer import SkillAnalyzer


def _build_controller_with_temp_paths(tempdir: Path) -> MainController:
    """
    テスト用に、ログ／出力先を一時ディレクトリに向けた MainController を生成する。

    Loggerはモックに差し替えてログ呼び出しを検証可能にする。
    """
    with patch(
        "qiita_skills_blog_generator.controller.Logger"
    ) as mock_logger_cls:
        controller = MainController(config_path=None)
    controller.logger = mock_logger_cls.return_value
    # 出力先を一時ディレクトリに上書きしておく
    controller.config.skills_directory = tempdir / "skills"
    controller.config.output_directory = tempdir / "output"
    return controller


def _write_skill_md(skill_dir: Path, content: str) -> Path:
    """SKILL.md を任意の生コンテンツで書き出すヘルパー"""
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(content, encoding="utf-8")
    return skill_file


class ParseSkillFileErrorHandlingTests(unittest.TestCase):
    """SkillAnalyzer.parse_skill_file() のエラー区分に対応したログ出力を検証する"""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tempdir.name)
        self.analyzer = SkillAnalyzer()
        # ログ呼び出しを差し替えて検証可能にする
        self.analyzer.logger = MagicMock(spec=logging.Logger)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    # 要件7.1: ファイル読み込み失敗 → ERROR ログ + None
    def test_returns_none_and_logs_error_when_file_missing(self) -> None:
        missing = self.tmp_path / "missing-skill" / "SKILL.md"

        result = self.analyzer.parse_skill_file(missing)

        self.assertIsNone(result)
        self.analyzer.logger.error.assert_called_once()
        message = self.analyzer.logger.error.call_args.args[0]
        self.assertIn("存在しません", message)

    # 要件7.2: YAMLパース失敗 → ERROR ログ + None
    def test_returns_none_and_logs_error_when_yaml_invalid(self) -> None:
        skill_dir = self.tmp_path / "broken-yaml"
        _write_skill_md(
            skill_dir,
            "---\nname: broken\ndescription: [invalid yaml\n---\n\n# 本文",
        )

        result = self.analyzer.parse_skill_file(skill_dir / "SKILL.md")

        self.assertIsNone(result)
        self.analyzer.logger.error.assert_called_once()
        message = self.analyzer.logger.error.call_args.args[0]
        self.assertIn("YAMLフロントマターの解析に失敗", message)

    def test_returns_none_and_logs_error_when_frontmatter_missing(self) -> None:
        skill_dir = self.tmp_path / "no-frontmatter"
        _write_skill_md(skill_dir, "# 本文だけ\n\nYAMLが無いSKILL.md")

        result = self.analyzer.parse_skill_file(skill_dir / "SKILL.md")

        self.assertIsNone(result)
        self.analyzer.logger.error.assert_called_once()
        message = self.analyzer.logger.error.call_args.args[0]
        self.assertIn("YAMLフロントマターの解析に失敗", message)

    # 要件7.3: 必須フィールド欠如 → WARNING ログ + None
    def test_returns_none_and_logs_warning_when_name_missing(self) -> None:
        skill_dir = self.tmp_path / "no-name"
        _write_skill_md(
            skill_dir,
            "---\ndescription: nameが無い\n---\n\n# 本文",
        )

        result = self.analyzer.parse_skill_file(skill_dir / "SKILL.md")

        self.assertIsNone(result)
        # warning が呼ばれ、error は呼ばれないこと
        self.analyzer.logger.warning.assert_called_once()
        self.analyzer.logger.error.assert_not_called()
        message = self.analyzer.logger.warning.call_args.args[0]
        self.assertIn("'name'", message)

    def test_returns_none_and_logs_warning_when_description_missing(
        self,
    ) -> None:
        skill_dir = self.tmp_path / "no-desc"
        _write_skill_md(
            skill_dir,
            "---\nname: only-name\n---\n\n# 本文",
        )

        result = self.analyzer.parse_skill_file(skill_dir / "SKILL.md")

        self.assertIsNone(result)
        self.analyzer.logger.warning.assert_called_once()
        self.analyzer.logger.error.assert_not_called()
        message = self.analyzer.logger.warning.call_args.args[0]
        self.assertIn("'description'", message)

    def test_returns_none_and_logs_warning_when_required_fields_empty(
        self,
    ) -> None:
        """name/description が空文字列でも警告ログを記録してスキップされる"""
        skill_dir = self.tmp_path / "empty-fields"
        _write_skill_md(
            skill_dir,
            '---\nname: ""\ndescription: ""\n---\n\n# 本文',
        )

        result = self.analyzer.parse_skill_file(skill_dir / "SKILL.md")

        self.assertIsNone(result)
        self.analyzer.logger.warning.assert_called_once()
        self.analyzer.logger.error.assert_not_called()


class RunErrorHandlingTests(unittest.TestCase):
    """MainController.run() のエラーハンドリング統合動作を検証する"""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tempdir.name)
        self.controller = _build_controller_with_temp_paths(self.tmp_path)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    # 要件7.5: スキルディレクトリが存在しない → 処理を中止
    def test_run_aborts_when_skills_directory_missing(self) -> None:
        # skills_directory は作成しない（存在しない状態）
        self.assertFalse(self.controller.config.skills_directory.exists())

        result = self.controller.run()

        # 処理は中止され、エラーがカウントされる（要件7.4, 7.5）
        self.assertEqual(result.success_count, 0)
        self.assertEqual(result.skip_count, 0)
        self.assertEqual(result.error_count, 1)
        # エラーログが呼ばれている
        self.controller.logger.log_error.assert_called()
        # log_end で実際のカウントが報告される（要件7.4）
        self.controller.logger.log_end.assert_called_once()
        end_kwargs = self.controller.logger.log_end.call_args.kwargs
        self.assertEqual(end_kwargs["success_count"], 0)
        self.assertEqual(end_kwargs["skip_count"], 0)
        self.assertEqual(end_kwargs["error_count"], 1)

    def test_run_returns_early_when_no_skill_md_found(self) -> None:
        """skills/ ディレクトリは存在するがSKILL.mdが無い場合は警告ログを残して終了する"""
        self.controller.config.skills_directory.mkdir(parents=True)

        result = self.controller.run()

        self.assertEqual(result.success_count, 0)
        # 警告ログが呼ばれている
        self.controller.logger.log_warning.assert_called()
        # log_end が呼ばれていることを確認
        self.controller.logger.log_end.assert_called_once()

    # 要件7.1, 7.2, 7.3, 7.4: 不正スキル混在時に成功/スキップが正しく集計される
    def test_run_counts_success_and_skip_correctly(self) -> None:
        """正常スキル・YAML不正スキル・必須欠如スキルが混在する場合の集計を検証"""
        skills_root = self.controller.config.skills_directory
        # 正常スキル（algorithmic-art カテゴリに含まれる名前を使う）
        _write_skill_md(
            skills_root / "algorithmic-art",
            "---\nname: algorithmic-art\n"
            "description: A valid skill\n"
            "license: Apache 2.0\n"
            "---\n\n# 本文\n",
        )
        # YAML 不正（要件7.2 のスキップ要因）
        _write_skill_md(
            skills_root / "broken-yaml",
            "---\nname: broken-yaml\n"
            "description: [invalid yaml\n"
            "---\n\n# 本文\n",
        )
        # 必須フィールド欠如（要件7.3 のスキップ要因）
        _write_skill_md(
            skills_root / "no-name",
            "---\ndescription: name欠如\n---\n\n# 本文\n",
        )

        result = self.controller.run()

        # 1件成功、2件スキップ
        self.assertEqual(result.success_count, 1)
        self.assertEqual(result.skip_count, 2)
        # スキップされたスキル名が記録されていること
        self.assertIn("broken-yaml", result.skipped_skills)
        self.assertIn("no-name", result.skipped_skills)
        # log_end の集計値が正しいこと（要件7.4）
        self.controller.logger.log_end.assert_called_once()
        end_kwargs = self.controller.logger.log_end.call_args.kwargs
        self.assertEqual(end_kwargs["success_count"], 1)
        self.assertEqual(end_kwargs["skip_count"], 2)

    # 要件7.5: 全スキル失敗時は処理を中止し、ProcessingResult にエラーを記録する
    def test_run_aborts_when_all_skills_fail(self) -> None:
        """すべてのSKILL.mdが解析失敗する場合は処理を中止する"""
        skills_root = self.controller.config.skills_directory
        # すべて YAML 不正
        _write_skill_md(
            skills_root / "broken-1",
            "---\nname: broken-1\ndescription: [bad\n---\n\n# 本文\n",
        )
        _write_skill_md(
            skills_root / "broken-2",
            "---\nname: broken-2\ndescription: [bad\n---\n\n# 本文\n",
        )

        result = self.controller.run()

        # 処理が中止される: 成功0、スキップ2、エラー1（要件7.5）
        self.assertEqual(result.success_count, 0)
        self.assertEqual(result.skip_count, 2)
        self.assertEqual(result.error_count, 1)
        # 処理中止に関するエラーログが呼ばれている
        self.controller.logger.log_error.assert_called()
        # log_error の呼び出しのうち少なくとも1つは「すべてのスキル処理に失敗」を含む
        error_calls = self.controller.logger.log_error.call_args_list
        abort_called = any(
            "すべてのスキル処理に失敗"
            in str(call.kwargs.get("message", call.args))
            for call in error_calls
        )
        self.assertTrue(
            abort_called,
            "全スキル失敗時のエラーログが記録される必要があります",
        )
        # 出力ファイルが生成されていないことを確認
        if self.controller.config.output_directory.exists():
            output_files = list(
                self.controller.config.output_directory.glob("*.md")
            )
            self.assertEqual(
                len(output_files),
                0,
                "全スキル失敗時は記事ファイルが生成されない必要があります",
            )

    # 要件7.4: 処理完了時に成功/スキップ/エラー数が報告される
    def test_run_reports_counts_via_log_end(self) -> None:
        """log_end が success/skip/error を正しく報告すること（要件7.4）"""
        skills_root = self.controller.config.skills_directory
        skills_root.mkdir(parents=True)
        # SKILL.md が0件 → log_end は呼ばれ、すべて0件で報告される
        result = self.controller.run()

        self.controller.logger.log_end.assert_called_once()
        end_kwargs = self.controller.logger.log_end.call_args.kwargs
        # 引数名が期待どおりであること
        self.assertIn("success_count", end_kwargs)
        self.assertIn("skip_count", end_kwargs)
        self.assertIn("error_count", end_kwargs)
        # 結果と一致していること
        self.assertEqual(end_kwargs["success_count"], result.success_count)
        self.assertEqual(end_kwargs["skip_count"], result.skip_count)
        self.assertEqual(end_kwargs["error_count"], result.error_count)


if __name__ == "__main__":
    unittest.main()
