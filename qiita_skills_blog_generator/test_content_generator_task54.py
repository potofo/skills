"""
Task 5.4のテスト: generate_skill_description()とgenerate_conclusion()メソッドのテスト
"""

import unittest
from pathlib import Path
from .config import Config, SkillData
from .content_generator import ContentGenerator


class TestContentGeneratorTask54(unittest.TestCase):
    """Task 5.4で実装したメソッドのテスト"""
    
    def setUp(self):
        """テストのセットアップ"""
        self.config = Config.default()
        self.generator = ContentGenerator(self.config)
    
    def test_generate_skill_description_basic(self):
        """基本的なスキル説明の生成をテスト"""
        skill = SkillData(
            name="test-skill",
            description="This is a test skill for testing purposes.",
            license="Apache 2.0",
            directory_path=Path("skills/test-skill")
        )
        
        description = self.generator.generate_skill_description(skill)
        
        # 説明が生成されることを確認
        self.assertIsNotNone(description)
        self.assertIsInstance(description, str)
        self.assertGreater(len(description), 0)
        
        # 基本説明が含まれることを確認
        self.assertIn("test skill", description.lower())
    
    def test_generate_skill_description_with_license(self):
        """ライセンス情報を含むスキル説明の生成をテスト"""
        skill = SkillData(
            name="apache-skill",
            description="A skill with Apache license.",
            license="Apache 2.0",
            directory_path=Path("skills/apache-skill")
        )
        
        description = self.generator.generate_skill_description(skill)
        
        # Apache 2.0ライセンスの表記を確認
        self.assertIn("Apache 2.0", description)
        self.assertIn("オープンソース", description)
    
    def test_generate_skill_description_proprietary(self):
        """プロプライエタリライセンスのスキル説明の生成をテスト"""
        skill = SkillData(
            name="proprietary-skill",
            description="A skill with proprietary license.",
            license="Proprietary. LICENSE.txt has complete terms",
            directory_path=Path("skills/proprietary-skill")
        )
        
        description = self.generator.generate_skill_description(skill)
        
        # プロプライエタリライセンスの表記を確認
        self.assertIn("プロプライエタリ", description)
    
    def test_generate_skill_description_with_resources(self):
        """バンドルリソースを含むスキル説明の生成をテスト"""
        skill = SkillData(
            name="resource-skill",
            description="A skill with bundled resources.",
            license="Apache 2.0",
            directory_path=Path("skills/resource-skill"),
            has_scripts=True,
            has_references=True,
            has_templates=True,
            has_assets=True
        )
        
        description = self.generator.generate_skill_description(skill)
        
        # バンドルリソースの情報が含まれることを確認
        self.assertIn("バンドルリソース", description)
        self.assertIn("実行スクリプト", description)
        self.assertIn("リファレンスドキュメント", description)
        self.assertIn("テンプレートファイル", description)
        self.assertIn("アセット", description)
    
    def test_generate_skill_description_length_limit(self):
        """文字数制限が適用されることをテスト"""
        # 非常に長い説明を持つスキル
        long_description = "A" * 1000  # 1000文字の説明
        skill = SkillData(
            name="long-skill",
            description=long_description,
            license="Apache 2.0",
            directory_path=Path("skills/long-skill")
        )
        
        description = self.generator.generate_skill_description(skill)
        
        # 設定された最大文字数を超えないことを確認
        self.assertLessEqual(len(description), self.config.max_skill_description_length)
    
    def test_generate_conclusion(self):
        """まとめセクションの生成をテスト"""
        conclusion = self.generator.generate_conclusion()
        
        # まとめが生成されることを確認
        self.assertIsNotNone(conclusion)
        self.assertIsInstance(conclusion, str)
        self.assertGreater(len(conclusion), 0)
        
        # 重要なキーワードが含まれることを確認
        self.assertIn("まとめ", conclusion)
        self.assertIn("Agent Skills", conclusion)
        self.assertIn("次のステップ", conclusion)
    
    def test_generate_conclusion_structure(self):
        """まとめセクションの構造をテスト"""
        conclusion = self.generator.generate_conclusion()
        
        # 主要なセクションが含まれることを確認
        self.assertIn("本記事で学んだこと", conclusion)
        self.assertIn("安全性とリスク評価", conclusion)
        self.assertIn("前提ソフトウェアとエコシステム", conclusion)
        self.assertIn("5つのカテゴリのスキル", conclusion)
        self.assertIn("次のステップ", conclusion)
        self.assertIn("最後に", conclusion)
    
    def test_generate_conclusion_contains_links(self):
        """まとめセクションに参考リンクが含まれることをテスト"""
        conclusion = self.generator.generate_conclusion()
        
        # 参考リンクが含まれることを確認
        self.assertIn("参考リンク", conclusion)
        self.assertIn("https://www.anthropic.com/", conclusion)
        self.assertIn("https://docs.anthropic.com/", conclusion)
        self.assertIn("https://github.com/anthropics/anthropic-agent-skills", conclusion)
        self.assertIn("https://agentskills.io/", conclusion)


if __name__ == '__main__':
    unittest.main()


class TestContentGeneratorTranslator(unittest.TestCase):
    """generate_skill_description() が翻訳器を利用することを検証する"""

    def setUp(self) -> None:
        self.config = Config.default()

    def test_translator_is_called_for_skill_description(self) -> None:
        """Translatorが渡されている場合、skill.descriptionが翻訳器を通る"""
        from unittest.mock import MagicMock

        translator = MagicMock()
        translator.translate.return_value = "日本語の説明文です。"
        generator = ContentGenerator(self.config, translator=translator)

        skill = SkillData(
            name="docx",
            description="Use this skill to create Word documents.",
            license="Proprietary. LICENSE.txt has complete terms",
            directory_path=Path("skills/docx"),
        )

        description = generator.generate_skill_description(skill)

        translator.translate.assert_called_once_with(
            "Use this skill to create Word documents."
        )
        self.assertIn("日本語の説明文です。", description)
        self.assertNotIn("Use this skill", description)

    def test_falls_back_to_english_when_translator_is_none(self) -> None:
        """Translatorが未指定なら原文（英語）がそのまま使われる"""
        generator = ContentGenerator(self.config, translator=None)

        skill = SkillData(
            name="algorithmic-art",
            description="Creating algorithmic art using p5.js.",
            license="Complete terms in LICENSE.txt",
            directory_path=Path("skills/algorithmic-art"),
        )

        description = generator.generate_skill_description(skill)

        self.assertIn("Creating algorithmic art", description)
