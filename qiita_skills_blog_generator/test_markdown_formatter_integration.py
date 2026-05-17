"""
MarkdownFormatterの統合テスト

ContentGeneratorと連携して動作することを確認します。
"""

import unittest
from pathlib import Path
from .config import Config, SkillData
from .content_generator import ContentGenerator
from .markdown_formatter import MarkdownFormatter


class TestMarkdownFormatterIntegration(unittest.TestCase):
    """MarkdownFormatterの統合テストケース"""
    
    def setUp(self):
        """各テストの前に実行される初期化処理"""
        self.config = Config.default()
        self.generator = ContentGenerator(self.config)
        self.formatter = MarkdownFormatter()
    
    def test_format_article_with_generated_content(self):
        """ContentGeneratorで生成したコンテンツをMarkdownFormatterで整形できることをテスト"""
        # コンテンツセクションを生成
        content_sections = {
            'title': self.config.article_title,
            'introduction': self.generator.generate_introduction(),
            'what_is_agent_skills': self.generator.generate_what_is_agent_skills(),
            'safety': self.generator.generate_safety_section(),
            'prerequisites': self.generator.generate_prerequisites_section(),
            'conclusion': self.generator.generate_conclusion()
        }
        
        # 記事を整形
        article = self.formatter.format_article(content_sections)
        
        # 記事が生成されたことを確認
        self.assertIsNotNone(article)
        self.assertGreater(len(article), 0)
        
        # タイトルが含まれることを確認
        self.assertIn("# ", article)
        
        # 目次が含まれることを確認
        self.assertIn("## 目次", article)
        
        # 各セクションが含まれることを確認
        self.assertIn("## はじめに", article)
        self.assertIn("## Agent Skillsとは", article)
        self.assertIn("## Agent Skillsの安全性とリスク", article)
        self.assertIn("## Agent Skillsを利用・開発するための前提ソフトウェア", article)
        self.assertIn("## まとめ", article)
    
    def test_format_article_with_skills_section(self):
        """スキル一覧セクションを含む記事の整形をテスト"""
        # テスト用のスキルデータを作成
        test_skills = [
            SkillData(
                name="test-skill-1",
                description="テストスキル1の説明",
                license="Apache 2.0",
                directory_path=Path("skills/test-skill-1"),
                markdown_body="テスト本文",
                has_scripts=True,
                has_references=False,
                has_assets=False,
                has_templates=False
            ),
            SkillData(
                name="test-skill-2",
                description="テストスキル2の説明",
                license="Proprietary",
                directory_path=Path("skills/test-skill-2"),
                markdown_body="テスト本文",
                has_scripts=False,
                has_references=True,
                has_assets=True,
                has_templates=True
            )
        ]
        
        # スキルをカテゴリ分類
        categorized_skills = self.generator.categorize_skills(test_skills)
        
        # スキル一覧セクションを生成
        skills_section = "## スキル一覧\n\n"
        for category, skills in categorized_skills.items():
            skills_section += f"### {category}\n\n"
            for skill in skills:
                skills_section += f"#### {skill.name}\n\n"
                description = self.generator.generate_skill_description(skill)
                skills_section += f"{description}\n\n"
        
        # コンテンツセクションを作成
        content_sections = {
            'title': 'テスト記事',
            'introduction': '## はじめに\n\nテスト内容。',
            'skills': skills_section,
            'conclusion': '## まとめ\n\nまとめです。'
        }
        
        # 記事を整形
        article = self.formatter.format_article(content_sections)
        
        # 記事が生成されたことを確認
        self.assertIsNotNone(article)
        self.assertGreater(len(article), 0)
        
        # スキル一覧セクションが含まれることを確認
        self.assertIn("## スキル一覧", article)
        
        # スキル名が含まれることを確認
        self.assertIn("test-skill-1", article)
        self.assertIn("test-skill-2", article)
    
    def test_format_article_heading_hierarchy(self):
        """記事の見出し階層が正しいことをテスト"""
        content_sections = {
            'title': 'テスト記事',
            'introduction': '## はじめに\n\nテスト内容。',
            'what_is_agent_skills': '## Agent Skillsとは\n\n### 基本概念\n\n説明。',
            'skills': '## スキル一覧\n\n### カテゴリ1\n\n#### スキル1\n\n説明。',
            'conclusion': '## まとめ\n\nまとめです。'
        }
        
        # 記事を整形
        article = self.formatter.format_article(content_sections)
        
        # 見出し階層を確認
        # H1（タイトル）が存在する
        self.assertTrue(article.startswith("# ") or "\n# " in article)
        
        # H2（主要セクション）が存在する
        self.assertIn("## ", article)
        
        # H3（サブセクション）が存在する
        self.assertIn("### ", article)
        
        # H4（個別スキル）が存在する
        self.assertIn("#### ", article)
    
    def test_format_article_qiita_markdown_compliance(self):
        """生成された記事がQiita Markdown形式に準拠していることをテスト"""
        content_sections = {
            'title': 'テスト記事',
            'introduction': '## はじめに\n\nテスト内容。',
            'conclusion': '## まとめ\n\nまとめです。'
        }
        
        # 記事を整形
        article = self.formatter.format_article(content_sections)
        
        # Qiita Markdown形式の基本要素を確認
        # 1. 見出しが正しい形式（#の後にスペース）
        import re
        headings = re.findall(r'^#{1,6} .+$', article, re.MULTILINE)
        self.assertGreater(len(headings), 0, "見出しが存在する")
        
        # 2. 空行が適切に挿入されている
        self.assertIn("\n\n", article, "セクション間に空行が存在する")
        
        # 3. 目次が正しい形式
        if "## 目次" in article:
            # 目次のリンク形式を確認
            toc_links = re.findall(r'\d+\. \[.+\]\(#.+\)', article)
            self.assertGreater(len(toc_links), 0, "目次のリンクが存在する")


if __name__ == '__main__':
    unittest.main()
