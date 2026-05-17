"""
ContentGeneratorのユニットテスト
"""

import unittest
from pathlib import Path
from .config import Config, SkillData
from .content_generator import ContentGenerator


class TestContentGenerator(unittest.TestCase):
    """ContentGeneratorクラスのテストケース"""
    
    def setUp(self):
        """各テストの前に実行される初期化処理"""
        self.config = Config.default()
        self.generator = ContentGenerator(self.config)
    
    def test_init(self):
        """__init__メソッドのテスト"""
        self.assertIsNotNone(self.generator)
        self.assertEqual(self.generator.config, self.config)
    
    def test_categorize_skills_empty(self):
        """空のスキルリストの分類テスト"""
        skills = []
        categorized = self.generator.categorize_skills(skills)
        
        # 空のリストの場合、カテゴリは空の辞書になる
        self.assertEqual(categorized, {})
    
    def test_categorize_skills_single_category(self):
        """単一カテゴリのスキル分類テスト"""
        skills = [
            SkillData(name="algorithmic-art", description="Test skill 1"),
            SkillData(name="canvas-design", description="Test skill 2"),
        ]
        categorized = self.generator.categorize_skills(skills)
        
        # クリエイティブ&デザインカテゴリに2つのスキルが含まれる
        self.assertIn("クリエイティブ&デザイン", categorized)
        self.assertEqual(len(categorized["クリエイティブ&デザイン"]), 2)
        
        # アルファベット順にソートされている
        self.assertEqual(categorized["クリエイティブ&デザイン"][0].name, "algorithmic-art")
        self.assertEqual(categorized["クリエイティブ&デザイン"][1].name, "canvas-design")
    
    def test_categorize_skills_multiple_categories(self):
        """複数カテゴリのスキル分類テスト"""
        skills = [
            SkillData(name="docx", description="Word document skill"),
            SkillData(name="claude-api", description="API skill"),
            SkillData(name="skill-creator", description="Meta skill"),
        ]
        categorized = self.generator.categorize_skills(skills)
        
        # 3つの異なるカテゴリに分類される
        self.assertIn("ドキュメント処理", categorized)
        self.assertIn("開発&技術", categorized)
        self.assertIn("メタスキル", categorized)
        
        self.assertEqual(len(categorized["ドキュメント処理"]), 1)
        self.assertEqual(len(categorized["開発&技術"]), 1)
        self.assertEqual(len(categorized["メタスキル"]), 1)
    
    def test_categorize_skills_unknown_skill(self):
        """未知のスキルの分類テスト"""
        skills = [
            SkillData(name="unknown-skill", description="Unknown skill"),
        ]
        categorized = self.generator.categorize_skills(skills)
        
        # 「その他」カテゴリに分類される
        self.assertIn("その他", categorized)
        self.assertEqual(len(categorized["その他"]), 1)
        self.assertEqual(categorized["その他"][0].name, "unknown-skill")
    
    def test_categorize_skills_sorting(self):
        """カテゴリ内のソートテスト"""
        skills = [
            SkillData(name="xlsx", description="Spreadsheet skill"),
            SkillData(name="docx", description="Word skill"),
            SkillData(name="pdf", description="PDF skill"),
            SkillData(name="pptx", description="PowerPoint skill"),
        ]
        categorized = self.generator.categorize_skills(skills)
        
        # アルファベット順にソートされている
        doc_skills = categorized["ドキュメント処理"]
        self.assertEqual(doc_skills[0].name, "docx")
        self.assertEqual(doc_skills[1].name, "pdf")
        self.assertEqual(doc_skills[2].name, "pptx")
        self.assertEqual(doc_skills[3].name, "xlsx")
    
    def test_categorize_skills_filtered_categories(self):
        """設定によるカテゴリフィルタリングのテスト"""
        # 特定のカテゴリのみを含める設定
        config = Config.default()
        config.included_categories = ["クリエイティブ&デザイン", "メタスキル"]
        generator = ContentGenerator(config)
        
        skills = [
            SkillData(name="algorithmic-art", description="Art skill"),
            SkillData(name="docx", description="Word skill"),
            SkillData(name="skill-creator", description="Meta skill"),
        ]
        categorized = generator.categorize_skills(skills)
        
        # 指定されたカテゴリのみが含まれる
        self.assertIn("クリエイティブ&デザイン", categorized)
        self.assertIn("メタスキル", categorized)
        self.assertNotIn("ドキュメント処理", categorized)
    
    def test_generate_introduction(self):
        """はじめにセクション生成のテスト"""
        intro = self.generator.generate_introduction()
        
        # 空でないことを確認
        self.assertIsNotNone(intro)
        self.assertGreater(len(intro), 0)
        
        # 見出しが含まれることを確認
        self.assertIn("## はじめに", intro)
        
        # キーワードが含まれることを確認
        self.assertIn("Agent Skills", intro)
        self.assertIn("初学者", intro)
        self.assertIn("Anthropic", intro)
    
    def test_generate_what_is_agent_skills(self):
        """Agent Skillsとはセクション生成のテスト"""
        section = self.generator.generate_what_is_agent_skills()
        
        # 空でないことを確認
        self.assertIsNotNone(section)
        self.assertGreater(len(section), 0)
        
        # 見出しが含まれることを確認
        self.assertIn("## Agent Skillsとは", section)
        
        # キーワードが含まれることを確認
        self.assertIn("SKILL.md", section)
        self.assertIn("段階的開示", section)
        self.assertIn("バンドルリソース", section)
    
    def test_generate_safety_section(self):
        """安全性とリスクセクション生成のテスト"""
        section = self.generator.generate_safety_section()
        
        # 空でないことを確認
        self.assertIsNotNone(section)
        self.assertGreater(len(section), 0)
        
        # 見出しが含まれることを確認
        self.assertIn("## Agent Skillsの安全性とリスク", section)
        
        # 3つのカテゴリの見出しが含まれることを確認
        self.assertIn("### 公式Agent Skills", section)
        self.assertIn("### ベンダー提供Agent Skills", section)
        self.assertIn("### 野良Agent Skills", section)
        
        # 企業内での安全性判断基準の見出しが含まれることを確認
        self.assertIn("### 企業内での安全性判断基準", section)
        
        # Anthropicの公式Agent Skillsについての見出しが含まれることを確認
        self.assertIn("### 本記事で扱うAnthropicの公式Agent Skillsについて", section)
        
        # キーワードが含まれることを確認
        self.assertIn("Anthropic", section)
        self.assertIn("OpenAI", section)
        self.assertIn("Google", section)
        self.assertIn("セキュリティ監査", section)
        self.assertIn("コードレビュー", section)
        self.assertIn("ライセンス", section)
        self.assertIn("メンテナンス", section)
        self.assertIn("データプライバシー", section)
        
        # 推奨度の記載が含まれることを確認
        self.assertIn("企業内利用における推奨度", section)
        
        # 安全性判断基準の項目が含まれることを確認
        self.assertIn("提供元の信頼性", section)
        self.assertIn("コードの透明性", section)
        self.assertIn("ライセンスの明確性", section)
        self.assertIn("メンテナンス体制", section)
        self.assertIn("データの取り扱い", section)
        self.assertIn("依存関係の確認", section)
        self.assertIn("社内セキュリティポリシーとの整合性", section)
        
        # Anthropicの公式Agent Skillsが信頼できる理由が含まれることを確認
        self.assertIn("信頼できる理由", section)
        self.assertIn("Apache 2.0", section)
    
    def test_generate_prerequisites_section(self):
        """前提ソフトウェアセクション生成のテスト"""
        section = self.generator.generate_prerequisites_section()
        
        # 空でないことを確認
        self.assertIsNotNone(section)
        self.assertGreater(len(section), 0)
        
        # メインの見出しが含まれることを確認
        self.assertIn("## Agent Skillsを利用・開発するための前提ソフトウェア", section)
        
        # サブセクションの見出しが含まれることを確認
        self.assertIn("### Agent Skillsを利用できるIDE（統合開発環境）", section)
        self.assertIn("### Agent Skillsを利用できるCLI（コマンドラインインターフェース）", section)
        self.assertIn("### Agent Skillsを構築するための開発環境", section)
        self.assertIn("### パッケージリポジトリとライブラリ管理", section)
        self.assertIn("### ドキュメント処理系スキルに必要な外部ツール", section)
        self.assertIn("### スキルカテゴリごとの依存関係", section)
        self.assertIn("### 企業内利用における考慮事項", section)
        
        # IDE関連のキーワードが含まれることを確認
        self.assertIn("VSCode", section)
        self.assertIn("Kiro", section)
        self.assertIn("Cursor", section)
        
        # CLI関連のキーワードが含まれることを確認
        self.assertIn("Claude Code", section)
        self.assertIn("Codex", section)
        self.assertIn("Gemini CLI", section)
        self.assertIn("Kiro CLI", section)
        
        # 開発環境関連のキーワードが含まれることを確認
        self.assertIn("Node.js", section)
        self.assertIn("Python", section)
        self.assertIn("TypeScript", section)
        
        # パッケージリポジトリ関連のキーワードが含まれることを確認
        self.assertIn("npm", section)
        self.assertIn("PyPI", section)
        self.assertIn("uv", section)
        
        # ドキュメント処理ツール関連のキーワードが含まれることを確認
        self.assertIn("LibreOffice", section)
        self.assertIn("Pandoc", section)
        self.assertIn("Poppler", section)
        self.assertIn("p5.js", section)
        
        # スキルカテゴリごとの依存関係が含まれることを確認
        self.assertIn("クリエイティブ&デザイン", section)
        self.assertIn("開発&技術", section)
        self.assertIn("ドキュメント処理", section)
        self.assertIn("エンタープライズ&コミュニケーション", section)
        self.assertIn("メタスキル", section)
        
        # 企業内利用における考慮事項が含まれることを確認
        self.assertIn("ネットワークとセキュリティ", section)
        self.assertIn("プライベートリポジトリの利用", section)
        self.assertIn("ライセンスコストとコンプライアンス", section)
        self.assertIn("オフライン環境での利用", section)
        self.assertIn("データプライバシーとセキュリティ", section)
        self.assertIn("情報セキュリティ部門の承認", section)
        self.assertIn("サポートとメンテナンス", section)
        
        # 具体的な依存関係の記載が含まれることを確認
        self.assertIn("python-docx", section)
        self.assertIn("MCP SDK", section)
        self.assertIn("Zod", section)
        self.assertIn("FastMCP", section)
        self.assertIn("Pydantic", section)


if __name__ == '__main__':
    unittest.main()
