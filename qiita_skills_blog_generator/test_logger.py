"""
Loggerクラスのユニットテスト

要件10の受入基準を検証します。
"""

import unittest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

from .logger import Logger


class TestLogger(unittest.TestCase):
    """Loggerクラスのテストケース"""
    
    def setUp(self):
        """各テストの前に実行される準備処理"""
        # 一時ディレクトリを作成
        self.test_dir = Path(tempfile.mkdtemp())
        self.log_file = self.test_dir / "test.log"
        self.loggers = []  # 作成したロガーを追跡
    
    def tearDown(self):
        """各テストの後に実行されるクリーンアップ処理"""
        # すべてのロガーを閉じる
        for logger in self.loggers:
            logger.close()
        
        # 一時ディレクトリを削除
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def create_logger(self, log_level: str, log_file: Path) -> Logger:
        """ロガーを作成して追跡リストに追加"""
        logger = Logger(log_level, log_file)
        self.loggers.append(logger)
        return logger
    
    def test_logger_initialization(self):
        """Loggerの初期化をテスト"""
        logger = self.create_logger("INFO", self.log_file)
        
        # ログファイルが作成されることを確認
        self.assertTrue(self.log_file.parent.exists())
        self.assertIsNotNone(logger.logger)
    
    def test_log_start(self):
        """処理開始ログのテスト（要件10.1）"""
        logger = self.create_logger("INFO", self.log_file)
        logger.log_start()
        
        # start_timeが設定されることを確認
        self.assertIsNotNone(logger.start_time)
        self.assertIsInstance(logger.start_time, datetime)
        
        # ログファイルに内容が書き込まれることを確認
        self.assertTrue(self.log_file.exists())
        content = self.log_file.read_text(encoding='utf-8')
        self.assertIn("処理開始", content)
        self.assertIn("開始時刻", content)
    
    def test_log_skill_processed(self):
        """スキル処理状況ログのテスト（要件10.2）"""
        logger = self.create_logger("INFO", self.log_file)
        
        # 成功ケース
        logger.log_skill_processed("test-skill", "success")
        content = self.log_file.read_text(encoding='utf-8')
        self.assertIn("test-skill", content)
        self.assertIn("成功", content)
        
        # スキップケース
        logger.log_skill_processed("skip-skill", "skip")
        content = self.log_file.read_text(encoding='utf-8')
        self.assertIn("skip-skill", content)
        self.assertIn("スキップ", content)
        
        # エラーケース
        logger.log_skill_processed("error-skill", "error")
        content = self.log_file.read_text(encoding='utf-8')
        self.assertIn("error-skill", content)
        self.assertIn("エラー", content)
    
    def test_log_output_file(self):
        """出力ファイルパスログのテスト（要件10.3）"""
        logger = self.create_logger("INFO", self.log_file)
        output_path = Path("output/article.md")
        
        logger.log_output_file(output_path)
        
        content = self.log_file.read_text(encoding='utf-8')
        self.assertIn("article.md", content)
        self.assertIn("出力", content)
    
    def test_log_error_with_details(self):
        """詳細なエラーログのテスト（要件10.4）"""
        logger = self.create_logger("INFO", self.log_file)
        
        logger.log_error(
            message="ファイルの読み込みに失敗しました",
            file_path="skills/test-skill/SKILL.md",
            cause="ファイルが存在しません",
            solution="ファイルパスを確認してください"
        )
        
        content = self.log_file.read_text(encoding='utf-8')
        # エラーメッセージの4要素が含まれることを確認
        self.assertIn("ERROR", content)
        self.assertIn("ファイルの読み込みに失敗", content)  # 事象
        self.assertIn("場所: skills/test-skill/SKILL.md", content)  # 場所
        self.assertIn("原因: ファイルが存在しません", content)  # 原因
        self.assertIn("対処: ファイルパスを確認してください", content)  # 対処方法
    
    def test_log_error_with_exception(self):
        """例外付きエラーログのテスト（要件10.4）"""
        logger = self.create_logger("INFO", self.log_file)
        
        try:
            raise ValueError("テスト例外")
        except ValueError as e:
            logger.log_error(
                message="処理中にエラーが発生しました",
                exception=e,
                file_path="test.py"
            )
        
        content = self.log_file.read_text(encoding='utf-8')
        self.assertIn("ERROR", content)
        self.assertIn("処理中にエラーが発生", content)
        self.assertIn("ValueError", content)
        self.assertIn("テスト例外", content)
    
    def test_log_warning(self):
        """警告ログのテスト（要件10.4）"""
        logger = self.create_logger("INFO", self.log_file)
        
        logger.log_warning(
            message="必須フィールドが欠けています",
            file_path="skills/test-skill/SKILL.md",
            cause="descriptionフィールドが見つかりません",
            solution="SKILL.mdにdescriptionを追加してください"
        )
        
        content = self.log_file.read_text(encoding='utf-8')
        self.assertIn("WARNING", content)
        self.assertIn("必須フィールドが欠けています", content)
        self.assertIn("場所:", content)
        self.assertIn("原因:", content)
        self.assertIn("対処:", content)
    
    def test_log_end(self):
        """処理終了ログのテスト（要件10.1）"""
        logger = self.create_logger("INFO", self.log_file)
        logger.log_start()
        
        # 少し待機（処理時間を測定するため）
        import time
        time.sleep(0.1)
        
        logger.log_end(success_count=10, skip_count=2, error_count=1)
        
        content = self.log_file.read_text(encoding='utf-8')
        self.assertIn("処理完了", content)
        self.assertIn("終了時刻", content)
        self.assertIn("処理時間", content)
        self.assertIn("成功: 10件", content)
        self.assertIn("スキップ: 2件", content)
        self.assertIn("エラー: 1件", content)
        self.assertIn("合計: 13件", content)
    
    def test_log_config(self):
        """設定ログのテスト（要件9.4）"""
        logger = self.create_logger("INFO", self.log_file)
        
        config_dict = {
            "skills_directory": "skills",
            "output_directory": "output",
            "log_level": "INFO"
        }
        
        logger.log_config(config_dict)
        
        content = self.log_file.read_text(encoding='utf-8')
        self.assertIn("使用する設定", content)
        self.assertIn("skills_directory", content)
        self.assertIn("output_directory", content)
        self.assertIn("log_level", content)
    
    def test_log_levels(self):
        """ログレベルのテスト（要件10.6）"""
        # DEBUGレベル
        debug_logger = self.create_logger("DEBUG", self.test_dir / "debug.log")
        debug_logger.debug("デバッグメッセージ")
        debug_content = (self.test_dir / "debug.log").read_text(encoding='utf-8')
        self.assertIn("デバッグメッセージ", debug_content)
        
        # INFOレベル
        info_logger = self.create_logger("INFO", self.test_dir / "info.log")
        info_logger.info("情報メッセージ")
        info_content = (self.test_dir / "info.log").read_text(encoding='utf-8')
        self.assertIn("情報メッセージ", info_content)
        
        # WARNINGレベル
        warning_logger = self.create_logger("WARNING", self.test_dir / "warning.log")
        warning_logger.log_warning("警告メッセージ")
        warning_content = (self.test_dir / "warning.log").read_text(encoding='utf-8')
        self.assertIn("警告メッセージ", warning_content)
        
        # ERRORレベル
        error_logger = self.create_logger("ERROR", self.test_dir / "error.log")
        error_logger.log_error("エラーメッセージ")
        error_content = (self.test_dir / "error.log").read_text(encoding='utf-8')
        self.assertIn("エラーメッセージ", error_content)
    
    def test_log_file_creation(self):
        """ログファイルの作成テスト（要件10.5）"""
        # 深い階層のログファイルパス
        deep_log_file = self.test_dir / "logs" / "subdir" / "test.log"
        logger = self.create_logger("INFO", deep_log_file)
        logger.info("テストメッセージ")
        
        # ディレクトリとファイルが作成されることを確認
        self.assertTrue(deep_log_file.parent.exists())
        self.assertTrue(deep_log_file.exists())


if __name__ == '__main__':
    unittest.main()
