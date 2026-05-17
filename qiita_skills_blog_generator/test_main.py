"""
エントリーポイント（main.py）のユニットテスト

タスク9.1の実装を検証します。
要件: 9.1, 9.2, 9.3, 9.4

注意:
    - 実際の skills/ ディレクトリに対してエントリーポイントは実行しない。
    - MainController をモックすることで、ファイル I/O やネットワーク I/O を
      発生させずに CLI のロジックのみを検証する。
"""

from __future__ import annotations

import io
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from qiita_skills_blog_generator import main as main_module
from qiita_skills_blog_generator.config import ProcessingResult


def _make_result(
    success: int = 1, skip: int = 0, error: int = 0
) -> ProcessingResult:
    """テスト用の ProcessingResult を生成するヘルパ"""
    result = ProcessingResult()
    for _ in range(success):
        result.add_success()
    for i in range(skip):
        result.add_skip(f"skipped-{i}")
    for i in range(error):
        result.add_error(f"errored-{i}", "テストエラー")
    return result


class BuildArgParserTests(unittest.TestCase):
    """build_arg_parser() の構築結果を検証する"""

    def test_default_arguments(self) -> None:
        """引数なしの場合、--config は None、--force は False"""
        parser = main_module.build_arg_parser()
        args = parser.parse_args([])
        self.assertIsNone(args.config)
        self.assertFalse(args.force)

    def test_config_argument_is_path(self) -> None:
        """--config はパスとして解釈される（要件9.1）"""
        parser = main_module.build_arg_parser()
        args = parser.parse_args(["--config", "config.json"])
        self.assertEqual(args.config, Path("config.json"))

    def test_force_argument_is_flag(self) -> None:
        """--force はブールフラグ"""
        parser = main_module.build_arg_parser()
        args = parser.parse_args(["--force"])
        self.assertTrue(args.force)

    def test_help_flag_exits(self) -> None:
        """--help は SystemExit(0) で終了する（argparse標準動作）"""
        parser = main_module.build_arg_parser()
        with self.assertRaises(SystemExit) as cm:
            with patch("sys.stdout", new_callable=io.StringIO):
                parser.parse_args(["--help"])
        self.assertEqual(cm.exception.code, 0)


class MainSuccessTests(unittest.TestCase):
    """main() の正常系を検証する（MainControllerをモック）"""

    def test_default_invocation_returns_zero(self) -> None:
        """引数なしで成功した場合、終了コードは0（要件9.2）"""
        with patch.object(main_module, "MainController") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.run.return_value = _make_result(success=3)
            mock_cls.return_value = mock_instance

            exit_code = main_module.main([])

        self.assertEqual(exit_code, 0)
        # config_path=None でインスタンス化されること（要件9.2）
        mock_cls.assert_called_once_with(config_path=None)
        # force=False で run() が呼ばれること
        mock_instance.run.assert_called_once_with(force=False)

    def test_config_argument_passed_to_controller(self) -> None:
        """--config の値が MainController に渡される（要件9.1）"""
        with patch.object(main_module, "MainController") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.run.return_value = _make_result(success=1)
            mock_cls.return_value = mock_instance

            exit_code = main_module.main(["--config", "custom.json"])

        self.assertEqual(exit_code, 0)
        mock_cls.assert_called_once_with(config_path=Path("custom.json"))

    def test_force_flag_passed_to_run(self) -> None:
        """--force の値が controller.run() に渡される"""
        with patch.object(main_module, "MainController") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.run.return_value = _make_result(success=1)
            mock_cls.return_value = mock_instance

            exit_code = main_module.main(["--force"])

        self.assertEqual(exit_code, 0)
        mock_instance.run.assert_called_once_with(force=True)

    def test_skip_only_is_treated_as_success(self) -> None:
        """エラーがない（スキップのみ）の場合、終了コードは0"""
        with patch.object(main_module, "MainController") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.run.return_value = _make_result(success=2, skip=1)
            mock_cls.return_value = mock_instance

            exit_code = main_module.main([])

        self.assertEqual(exit_code, 0)


class MainErrorTests(unittest.TestCase):
    """main() のエラーハンドリングを検証する"""

    def test_processing_errors_return_one(self) -> None:
        """ProcessingResult にエラーが含まれる場合、終了コードは1"""
        with patch.object(main_module, "MainController") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.run.return_value = _make_result(
                success=1, error=1
            )
            mock_cls.return_value = mock_instance

            exit_code = main_module.main([])

        self.assertEqual(exit_code, 1)

    def test_unexpected_exception_returns_one(self) -> None:
        """予期しない例外が発生した場合、終了コードは1"""
        with patch.object(main_module, "MainController") as mock_cls:
            mock_cls.side_effect = RuntimeError("テストエラー")

            with patch("sys.stderr", new_callable=io.StringIO) as stderr:
                exit_code = main_module.main([])

        self.assertEqual(exit_code, 1)
        self.assertIn("テストエラー", stderr.getvalue())

    def test_keyboard_interrupt_returns_one(self) -> None:
        """KeyboardInterrupt が発生した場合、終了コードは1"""
        with patch.object(main_module, "MainController") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.run.side_effect = KeyboardInterrupt()
            mock_cls.return_value = mock_instance

            with patch("sys.stderr", new_callable=io.StringIO):
                exit_code = main_module.main([])

        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
