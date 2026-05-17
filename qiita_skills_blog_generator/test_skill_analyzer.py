"""
SkillAnalyzerのユニットテスト
"""

import unittest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import logging

from qiita_skills_blog_generator.skill_analyzer import SkillAnalyzer
from qiita_skills_blog_generator.config import SkillData


class TestSkillAnalyzer(unittest.TestCase):
    """SkillAnalyzerクラスのテストケース"""
    
    def setUp(self):
        """各テストの前に実行される初期化処理"""
        self.analyzer = SkillAnalyzer()
        # テスト用の一時ディレクトリを作成
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # ロガーの設定（テスト中はWARNINGレベル以上のみ表示）
        logging.basicConfig(level=logging.WARNING)
    
    def tearDown(self):
        """各テストの後に実行されるクリーンアップ処理"""
        # 一時ディレクトリを削除
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_skill_file(self, skill_name: str, yaml_content: str, markdown_content: str) -> Path:
        """テスト用のSKILL.mdファイルを作成するヘルパーメソッド"""
        skill_dir = self.temp_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        skill_file = skill_dir / "SKILL.md"
        content = f"---\n{yaml_content}\n---\n\n{markdown_content}"
        skill_file.write_text(content, encoding='utf-8')
        
        return skill_file
    
    def test_scan_skills_directory_success(self):
        """正常なスキルディレクトリの走査をテスト"""
        # テスト用のスキルファイルを作成
        self.create_skill_file(
            "test-skill-1",
            "name: test-skill-1\ndescription: Test skill 1",
            "# Test Skill 1"
        )
        self.create_skill_file(
            "test-skill-2",
            "name: test-skill-2\ndescription: Test skill 2",
            "# Test Skill 2"
        )
        
        # スキルディレクトリを走査
        skill_files = self.analyzer.scan_skills_directory(self.temp_dir)
        
        # 2つのSKILL.mdファイルが見つかることを確認
        self.assertEqual(len(skill_files), 2)
        self.assertTrue(all(f.name == "SKILL.md" for f in skill_files))
    
    def test_scan_skills_directory_not_found(self):
        """存在しないディレクトリの走査でエラーが発生することをテスト"""
        non_existent_dir = self.temp_dir / "non_existent"
        
        with self.assertRaises(FileNotFoundError):
            self.analyzer.scan_skills_directory(non_existent_dir)
    
    def test_scan_skills_directory_not_a_directory(self):
        """ファイルパスを指定した場合にエラーが発生することをテスト"""
        file_path = self.temp_dir / "test_file.txt"
        file_path.write_text("test", encoding='utf-8')
        
        with self.assertRaises(NotADirectoryError):
            self.analyzer.scan_skills_directory(file_path)
    
    def test_extract_yaml_frontmatter_success(self):
        """正常なYAMLフロントマターの抽出をテスト"""
        content = """---
name: test-skill
description: A test skill
license: Apache 2.0
---

# Test Content
"""
        frontmatter = self.analyzer.extract_yaml_frontmatter(content)
        
        self.assertEqual(frontmatter['name'], 'test-skill')
        self.assertEqual(frontmatter['description'], 'A test skill')
        self.assertEqual(frontmatter['license'], 'Apache 2.0')
    
    def test_extract_yaml_frontmatter_missing(self):
        """YAMLフロントマターがない場合にエラーが発生することをテスト"""
        content = "# Test Content\nNo frontmatter here"
        
        with self.assertRaises(ValueError) as context:
            self.analyzer.extract_yaml_frontmatter(content)
        
        self.assertIn("YAMLフロントマターが見つかりません", str(context.exception))
    
    def test_extract_yaml_frontmatter_invalid_yaml(self):
        """不正なYAMLの場合にエラーが発生することをテスト"""
        content = """---
name: test-skill
description: [invalid yaml structure
---

# Test Content
"""
        with self.assertRaises(ValueError) as context:
            self.analyzer.extract_yaml_frontmatter(content)
        
        self.assertIn("YAMLのパースに失敗しました", str(context.exception))
    
    def test_extract_markdown_body_success(self):
        """正常なMarkdown本文の抽出をテスト"""
        content = """---
name: test-skill
description: A test skill
---

# Test Content

This is the markdown body.
"""
        markdown_body = self.analyzer.extract_markdown_body(content)
        
        self.assertIn("# Test Content", markdown_body)
        self.assertIn("This is the markdown body.", markdown_body)
        self.assertNotIn("---", markdown_body)
        self.assertNotIn("name: test-skill", markdown_body)
    
    def test_check_bundled_resources_all_present(self):
        """すべてのバンドルリソースが存在する場合をテスト"""
        skill_dir = self.temp_dir / "test-skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        # すべてのリソースディレクトリを作成
        (skill_dir / "scripts").mkdir()
        (skill_dir / "references").mkdir()
        (skill_dir / "assets").mkdir()
        (skill_dir / "templates").mkdir()
        
        result = self.analyzer.check_bundled_resources(skill_dir)
        
        self.assertTrue(result['scripts'])
        self.assertTrue(result['references'])
        self.assertTrue(result['assets'])
        self.assertTrue(result['templates'])
    
    def test_check_bundled_resources_none_present(self):
        """バンドルリソースが存在しない場合をテスト"""
        skill_dir = self.temp_dir / "test-skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        result = self.analyzer.check_bundled_resources(skill_dir)
        
        self.assertFalse(result['scripts'])
        self.assertFalse(result['references'])
        self.assertFalse(result['assets'])
        self.assertFalse(result['templates'])
    
    def test_check_bundled_resources_partial(self):
        """一部のバンドルリソースのみ存在する場合をテスト"""
        skill_dir = self.temp_dir / "test-skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        # scriptsとtemplatesのみ作成
        (skill_dir / "scripts").mkdir()
        (skill_dir / "templates").mkdir()
        
        result = self.analyzer.check_bundled_resources(skill_dir)
        
        self.assertTrue(result['scripts'])
        self.assertFalse(result['references'])
        self.assertFalse(result['assets'])
        self.assertTrue(result['templates'])
    
    def test_parse_skill_file_success(self):
        """正常なSKILL.mdファイルの解析をテスト"""
        skill_file = self.create_skill_file(
            "test-skill",
            "name: test-skill\ndescription: A test skill\nlicense: Apache 2.0",
            "# Test Skill\n\nThis is a test skill."
        )
        
        # バンドルリソースを作成
        skill_dir = skill_file.parent
        (skill_dir / "scripts").mkdir()
        (skill_dir / "templates").mkdir()
        
        skill_data = self.analyzer.parse_skill_file(skill_file)
        
        self.assertIsNotNone(skill_data)
        self.assertEqual(skill_data.name, "test-skill")
        self.assertEqual(skill_data.description, "A test skill")
        self.assertEqual(skill_data.license, "Apache 2.0")
        self.assertIn("# Test Skill", skill_data.markdown_body)
        self.assertTrue(skill_data.has_scripts)
        self.assertFalse(skill_data.has_references)
        self.assertFalse(skill_data.has_assets)
        self.assertTrue(skill_data.has_templates)
    
    def test_parse_skill_file_missing_name(self):
        """nameフィールドが欠けている場合にNoneを返すことをテスト"""
        skill_file = self.create_skill_file(
            "test-skill",
            "description: A test skill",
            "# Test Skill"
        )
        
        skill_data = self.analyzer.parse_skill_file(skill_file)
        
        self.assertIsNone(skill_data)
    
    def test_parse_skill_file_missing_description(self):
        """descriptionフィールドが欠けている場合にNoneを返すことをテスト"""
        skill_file = self.create_skill_file(
            "test-skill",
            "name: test-skill",
            "# Test Skill"
        )
        
        skill_data = self.analyzer.parse_skill_file(skill_file)
        
        self.assertIsNone(skill_data)
    
    def test_parse_skill_file_not_found(self):
        """存在しないファイルの解析でNoneを返すことをテスト"""
        non_existent_file = self.temp_dir / "non_existent" / "SKILL.md"
        
        skill_data = self.analyzer.parse_skill_file(non_existent_file)
        
        self.assertIsNone(skill_data)
    
    def test_parse_skill_file_invalid_yaml(self):
        """不正なYAMLの場合にNoneを返すことをテスト"""
        skill_dir = self.temp_dir / "test-skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        skill_file = skill_dir / "SKILL.md"
        content = """---
name: test-skill
description: [invalid yaml
---

# Test
"""
        skill_file.write_text(content, encoding='utf-8')
        
        skill_data = self.analyzer.parse_skill_file(skill_file)
        
        self.assertIsNone(skill_data)


if __name__ == '__main__':
    unittest.main()
