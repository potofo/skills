"""
Task 5.4の統合テスト: 実際のスキルデータを使用したテスト
"""

from pathlib import Path
from qiita_skills_blog_generator.config import Config, SkillData
from qiita_skills_blog_generator.content_generator import ContentGenerator
from qiita_skills_blog_generator.skill_analyzer import SkillAnalyzer


def test_with_real_skills():
    """実際のスキルデータを使用してメソッドをテスト"""
    config = Config.default()
    analyzer = SkillAnalyzer()
    generator = ContentGenerator(config)
    
    # skills/ディレクトリからいくつかのスキルを読み込む
    skills_dir = Path("skills")
    if not skills_dir.exists():
        print("skills/ディレクトリが見つかりません")
        return
    
    # algorithmic-artスキルをテスト
    algorithmic_art_path = skills_dir / "algorithmic-art" / "SKILL.md"
    if algorithmic_art_path.exists():
        print("=== algorithmic-art スキルのテスト ===")
        skill = analyzer.parse_skill_file(algorithmic_art_path)
        if skill:
            description = generator.generate_skill_description(skill)
            print(f"スキル名: {skill.name}")
            print(f"説明文字数: {len(description)}")
            print(f"説明:\n{description}\n")
    
    # docxスキルをテスト
    docx_path = skills_dir / "docx" / "SKILL.md"
    if docx_path.exists():
        print("=== docx スキルのテスト ===")
        skill = analyzer.parse_skill_file(docx_path)
        if skill:
            description = generator.generate_skill_description(skill)
            print(f"スキル名: {skill.name}")
            print(f"説明文字数: {len(description)}")
            print(f"説明:\n{description}\n")
    
    # まとめセクションをテスト
    print("=== まとめセクションのテスト ===")
    conclusion = generator.generate_conclusion()
    print(f"まとめ文字数: {len(conclusion)}")
    print(f"まとめ（最初の500文字）:\n{conclusion[:500]}...\n")
    
    print("✅ すべてのテストが完了しました")


if __name__ == "__main__":
    test_with_real_skills()
