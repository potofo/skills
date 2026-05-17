"""
MainController.validate_output() のユニットテスト

タスク8.2の品質検証ロジックを検証します。
要件: 8.1, 8.2, 8.3, 8.4, 8.6, 8.7, 8.8, 8.9, 8.10
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from qiita_skills_blog_generator.controller import MainController
from qiita_skills_blog_generator.constants import MIN_ARTICLE_LENGTH


def _build_valid_article() -> str:
    """品質検証に合格する模擬記事を生成"""
    body_filler = "これはテスト記事の本文です。" * 200  # 約2400文字
    return f"""# Claude Agent Skills完全ガイド

## 目次

1. はじめに
2. Agent Skillsとは
3. Agent Skillsの安全性とリスク
4. Agent Skillsを利用・開発するための前提ソフトウェア
5. スキル一覧
6. まとめ

## はじめに

本記事はAgent Skillsについて初学者向けに解説します。
{body_filler}

## Agent Skillsとは

Agent Skillsは知識パッケージです。
{body_filler}

## Agent Skillsの安全性とリスク

### 公式Agent Skills

公式のAgent Skillsについて説明します。

### ベンダー提供Agent Skills

ベンダー提供のAgent Skillsについて説明します。

### 野良Agent Skills

野良のAgent Skillsについて説明します。

## Agent Skillsを利用・開発するための前提ソフトウェア

### IDE（統合開発環境）

VSCodeやKiroなどのIDEで利用できます。

### CLI（コマンドラインインターフェース）

Claude CodeなどのCLIで利用できます。

## スキル一覧

### クリエイティブ&デザイン

#### algorithmic-art

p5.jsを使ったクリエイティブコーディングのスキルです。具体的な使用例として作品制作があります。

### 開発&技術

#### claude-api

Claude APIを利用するためのスキルです。

### ドキュメント処理

#### docx

Word文書を操作するスキルです。

### エンタープライズ&コミュニケーション

#### brand-guidelines

ブランドガイドラインに沿った文書を作成するスキルです。

### メタスキル

#### skill-creator

スキル作成を支援するメタスキルです。

## まとめ

本記事ではAgent Skillsについて解説しました。
{body_filler}
"""


class ValidateOutputTests(unittest.TestCase):
    """validate_output() の品質検証ロジックを検証する"""

    def setUp(self) -> None:
        """テスト用のMainControllerをログを実ファイルに書かずに初期化"""
        self.tempdir = tempfile.TemporaryDirectory()
        log_file = Path(self.tempdir.name) / "test.log"
        # ログ出力先を一時ディレクトリに差し替えるため、Configをパッチ
        with patch(
            "qiita_skills_blog_generator.controller.Logger"
        ) as mock_logger_cls:
            self.controller = MainController(config_path=None)
        # Loggerをモックに差し替え（log_warning呼び出しを記録するため）
        self.controller.logger = mock_logger_cls.return_value
        self.controller.logger.log_warning.reset_mock()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    # 要件8.1: 文字数チェック
    def test_validate_passes_for_valid_article(self) -> None:
        article = _build_valid_article()
        self.assertGreaterEqual(len(article), MIN_ARTICLE_LENGTH)
        result = self.controller.validate_output(article, skills_count=5)
        self.assertTrue(result, "妥当な記事は品質検証に合格する必要があります")

    def test_validate_fails_for_short_article(self) -> None:
        article = "# 短い記事\n\n本文がほとんどない記事です。"
        result = self.controller.validate_output(article, skills_count=0)
        self.assertFalse(result)
        self.controller.logger.log_warning.assert_called()

    # 要件8.2: カテゴリの存在チェック
    def test_validate_fails_when_category_missing(self) -> None:
        article = _build_valid_article()
        # 「メタスキル」カテゴリを削除して検証
        article_missing = article.replace("### メタスキル", "### ダミーカテゴリ")
        article_missing = article_missing.replace(
            "メタスキル", "ダミー"  # 配列内の参照も置換
        )
        result = self.controller.validate_output(article_missing, skills_count=5)
        self.assertFalse(result)

    # 要件8.3: スキル説明が空でないこと
    def test_validate_fails_for_empty_skill_description(self) -> None:
        article = _build_valid_article()
        # スキル説明を空にする
        article_empty = article.replace(
            "p5.jsを使ったクリエイティブコーディングのスキルです。"
            "具体的な使用例として作品制作があります。",
            "",
        )
        result = self.controller.validate_output(article_empty, skills_count=5)
        self.assertFalse(result)

    # 要件8.4: Markdown記法の正しさ
    def test_validate_fails_for_unclosed_code_block(self) -> None:
        article = _build_valid_article()
        # 閉じられていないコードブロックを追加
        article_broken = article + "\n```python\nprint('hello')\n"
        result = self.controller.validate_output(article_broken, skills_count=5)
        self.assertFalse(result)

    def test_validate_fails_for_multiple_h1_headings(self) -> None:
        article = _build_valid_article()
        # 追加のH1見出しを挿入
        article_broken = article.replace(
            "## はじめに", "# 追加のH1\n\n## はじめに"
        )
        result = self.controller.validate_output(article_broken, skills_count=5)
        self.assertFalse(result)

    # 要件8.6: 安全性セクションの存在
    def test_validate_fails_when_safety_section_missing(self) -> None:
        article = _build_valid_article()
        # 安全性セクションを削除
        article_no_safety = article.replace(
            "## Agent Skillsの安全性とリスク", "## ダミーセクション"
        )
        article_no_safety = article_no_safety.replace("安全性とリスク", "ダミー記述")
        result = self.controller.validate_output(article_no_safety, skills_count=5)
        self.assertFalse(result)

    # 要件8.7: 前提ソフトウェアセクションの存在
    def test_validate_fails_when_prerequisites_section_missing(self) -> None:
        article = _build_valid_article()
        article_no_prereq = article.replace("前提ソフトウェア", "別の見出し")
        result = self.controller.validate_output(
            article_no_prereq, skills_count=5
        )
        self.assertFalse(result)

    # 要件8.9: 見出しの階層構造の適切性
    def test_validate_fails_for_skipped_heading_levels(self) -> None:
        article = "# タイトル\n\n#### 突然のH4\n\n本文。\n"
        result = self.controller.validate_output(article, skills_count=0)
        self.assertFalse(result)

    def test_validate_fails_when_starting_with_non_h1(self) -> None:
        article = "## H2から始まる\n\n本文です。\n"
        result = self.controller.validate_output(article, skills_count=0)
        self.assertFalse(result)

    # 要件8.10: 警告メッセージ表示
    def test_warning_logged_on_failure(self) -> None:
        article = "# 短い\n\n本文。"
        self.controller.validate_output(article, skills_count=0)
        # log_warningが呼ばれていることを確認
        self.assertTrue(
            self.controller.logger.log_warning.called,
            "品質チェック失敗時には警告メッセージが表示される必要があります",
        )


if __name__ == "__main__":
    unittest.main()
