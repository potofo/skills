"""
MarkdownFormatterのユニットテスト
"""

import unittest
from .markdown_formatter import MarkdownFormatter


class TestMarkdownFormatter(unittest.TestCase):
    """MarkdownFormatterクラスのテストケース"""
    
    def setUp(self):
        """各テストの前に実行される初期化処理"""
        self.formatter = MarkdownFormatter()
    
    def test_format_heading_h1(self):
        """H1見出しの正しい生成をテスト"""
        result = self.formatter.format_heading("タイトル", 1)
        self.assertEqual(result, "# タイトル")
    
    def test_format_heading_h2(self):
        """H2見出しの正しい生成をテスト"""
        result = self.formatter.format_heading("セクション", 2)
        self.assertEqual(result, "## セクション")
    
    def test_format_heading_h3(self):
        """H3見出しの正しい生成をテスト"""
        result = self.formatter.format_heading("サブセクション", 3)
        self.assertEqual(result, "### サブセクション")
    
    def test_format_heading_h4(self):
        """H4見出しの正しい生成をテスト"""
        result = self.formatter.format_heading("個別スキル", 4)
        self.assertEqual(result, "#### 個別スキル")
    
    def test_format_heading_invalid_level_too_low(self):
        """不正な見出しレベル（0以下）でValueErrorが発生することをテスト"""
        with self.assertRaises(ValueError):
            self.formatter.format_heading("テスト", 0)
    
    def test_format_heading_invalid_level_too_high(self):
        """不正な見出しレベル（7以上）でValueErrorが発生することをテスト"""
        with self.assertRaises(ValueError):
            self.formatter.format_heading("テスト", 7)
    
    def test_format_code_block_with_language(self):
        """言語指定ありのコードブロックの正しい整形をテスト"""
        code = "print('Hello, World!')"
        result = self.formatter.format_code_block(code, "python")
        expected = "```python\nprint('Hello, World!')\n```"
        self.assertEqual(result, expected)
    
    def test_format_code_block_without_language(self):
        """言語指定なしのコードブロックの正しい整形をテスト"""
        code = "echo 'Hello, World!'"
        result = self.formatter.format_code_block(code)
        expected = "```\necho 'Hello, World!'\n```"
        self.assertEqual(result, expected)
    
    def test_format_code_block_multiline(self):
        """複数行のコードブロックの正しい整形をテスト"""
        code = "def hello():\n    print('Hello')\n    return True"
        result = self.formatter.format_code_block(code, "python")
        expected = "```python\ndef hello():\n    print('Hello')\n    return True\n```"
        self.assertEqual(result, expected)
    
    def test_format_list_unordered(self):
        """箇条書きリストの正しい整形をテスト"""
        items = ["項目1", "項目2", "項目3"]
        result = self.formatter.format_list(items, ordered=False)
        expected = "- 項目1\n- 項目2\n- 項目3"
        self.assertEqual(result, expected)
    
    def test_format_list_ordered(self):
        """番号付きリストの正しい整形をテスト"""
        items = ["最初", "次", "最後"]
        result = self.formatter.format_list(items, ordered=True)
        expected = "1. 最初\n2. 次\n3. 最後"
        self.assertEqual(result, expected)
    
    def test_format_list_empty(self):
        """空のリストで空文字列が返されることをテスト"""
        result = self.formatter.format_list([], ordered=False)
        self.assertEqual(result, "")
    
    def test_format_list_single_item(self):
        """単一項目のリストの正しい整形をテスト"""
        items = ["唯一の項目"]
        result = self.formatter.format_list(items, ordered=False)
        expected = "- 唯一の項目"
        self.assertEqual(result, expected)
    
    def test_generate_table_of_contents(self):
        """目次の正しい生成をテスト"""
        sections = ["はじめに", "Agent Skillsとは", "まとめ"]
        result = self.formatter.generate_table_of_contents(sections)
        
        # 目次の見出しが含まれることを確認
        self.assertIn("## 目次", result)
        
        # 各セクションへのリンクが含まれることを確認
        self.assertIn("1. [はじめに]", result)
        self.assertIn("2. [Agent Skillsとは]", result)
        self.assertIn("3. [まとめ]", result)
    
    def test_generate_table_of_contents_empty(self):
        """空のセクションリストで目次が生成されることをテスト"""
        sections = []
        result = self.formatter.generate_table_of_contents(sections)
        
        # 目次の見出しは含まれる
        self.assertIn("## 目次", result)
    
    def test_format_article_complete(self):
        """完全な記事の正しい生成をテスト"""
        content_sections = {
            'title': 'テスト記事',
            'introduction': '## はじめに\n\nこれはテストです。',
            'what_is_agent_skills': '## Agent Skillsとは\n\n説明文。',
            'safety': '## 安全性とリスク\n\n安全性について。',
            'prerequisites': '## 前提ソフトウェア\n\n必要なソフトウェア。',
            'skills': '## スキル一覧\n\nスキルの説明。',
            'conclusion': '## まとめ\n\nまとめです。'
        }
        
        result = self.formatter.format_article(content_sections)
        
        # タイトルが含まれることを確認
        self.assertIn("# テスト記事", result)
        
        # 目次が含まれることを確認
        self.assertIn("## 目次", result)
        
        # 各セクションが含まれることを確認
        self.assertIn("## はじめに", result)
        self.assertIn("## Agent Skillsとは", result)
        self.assertIn("## 安全性とリスク", result)
        self.assertIn("## 前提ソフトウェア", result)
        self.assertIn("## スキル一覧", result)
        self.assertIn("## まとめ", result)
    
    def test_format_article_partial(self):
        """一部のセクションのみの記事の正しい生成をテスト"""
        content_sections = {
            'title': 'テスト記事',
            'introduction': '## はじめに\n\nこれはテストです。',
            'conclusion': '## まとめ\n\nまとめです。'
        }
        
        result = self.formatter.format_article(content_sections)
        
        # タイトルが含まれることを確認
        self.assertIn("# テスト記事", result)
        
        # 含まれるセクションが存在することを確認
        self.assertIn("## はじめに", result)
        self.assertIn("## まとめ", result)
        
        # 含まれないセクションが存在しないことを確認
        self.assertNotIn("## Agent Skillsとは", result)
        self.assertNotIn("## 安全性とリスク", result)
    
    def test_format_article_empty(self):
        """空のコンテンツセクションで空に近い記事が生成されることをテスト"""
        content_sections = {}
        result = self.formatter.format_article(content_sections)
        
        # 空または空白のみの文字列が返される
        self.assertTrue(len(result.strip()) == 0 or result.strip() == "## 目次")
    
    def test_format_article_markdown_structure(self):
        """生成された記事のMarkdown構造が正しいことをテスト"""
        content_sections = {
            'title': 'テスト記事',
            'introduction': '## はじめに\n\nテスト内容。'
        }
        
        result = self.formatter.format_article(content_sections)
        
        # 見出しレベルの一貫性を確認（H1が1つ存在する）
        # H1は記事の先頭にあるため、"# "で始まるか"\n# "を含むかをチェック
        h1_exists = result.startswith("# ") or "\n# " in result
        self.assertTrue(h1_exists, "H1見出しが少なくとも1つ存在する")
        
        # 空行が適切に挿入されていることを確認
        self.assertIn("\n\n", result, "セクション間に空行が存在する")


if __name__ == '__main__':
    unittest.main()
