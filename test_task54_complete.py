"""
Task 5.4の完全テスト: 全体のワークフローをテスト
"""

from pathlib import Path
from qiita_skills_blog_generator.config import Config, SkillData
from qiita_skills_blog_generator.content_generator import ContentGenerator
from qiita_skills_blog_generator.skill_analyzer import SkillAnalyzer


def test_complete_workflow():
    """完全なワークフローをテスト"""
    print("=== Task 5.4 完全テスト ===\n")
    
    # 1. 設定を初期化
    config = Config.default()
    print(f"✓ 設定を初期化しました")
    print(f"  - 最大スキル説明文字数: {config.max_skill_description_length}")
    print(f"  - 対象読者: {config.target_audience}\n")
    
    # 2. コンポーネントを初期化
    analyzer = SkillAnalyzer()
    generator = ContentGenerator(config)
    print(f"✓ コンポーネントを初期化しました\n")
    
    # 3. スキルを解析
    skills_dir = Path("skills")
    if not skills_dir.exists():
        print("❌ skills/ディレクトリが見つかりません")
        return
    
    skill_paths = analyzer.scan_skills_directory(skills_dir)
    print(f"✓ {len(skill_paths)}個のSKILL.mdファイルを発見しました\n")
    
    # 4. スキルをパース
    skills = []
    for skill_path in skill_paths[:5]:  # 最初の5つのスキルをテスト
        skill = analyzer.parse_skill_file(skill_path)
        if skill:
            skills.append(skill)
    
    print(f"✓ {len(skills)}個のスキルを解析しました\n")
    
    # 5. スキルをカテゴリ分類
    categorized_skills = generator.categorize_skills(skills)
    print(f"✓ スキルをカテゴリ分類しました:")
    for category, skill_list in categorized_skills.items():
        print(f"  - {category}: {len(skill_list)}個")
    print()
    
    # 6. 各スキルの説明を生成（Task 5.4の機能）
    print("=== スキル説明の生成（Task 5.4） ===\n")
    for category, skill_list in categorized_skills.items():
        print(f"【{category}】")
        for skill in skill_list:
            description = generator.generate_skill_description(skill)
            print(f"\n  ◆ {skill.name}")
            print(f"    文字数: {len(description)}")
            print(f"    説明: {description[:100]}...")
        print()
    
    # 7. まとめセクションを生成（Task 5.4の機能）
    print("=== まとめセクションの生成（Task 5.4） ===\n")
    conclusion = generator.generate_conclusion()
    print(f"✓ まとめセクションを生成しました")
    print(f"  - 文字数: {len(conclusion)}")
    print(f"  - 最初の200文字:\n{conclusion[:200]}...\n")
    
    # 8. 他のセクションも生成して統合をテスト
    print("=== 他のセクションとの統合テスト ===\n")
    
    introduction = generator.generate_introduction()
    print(f"✓ はじめにセクション: {len(introduction)}文字")
    
    what_is = generator.generate_what_is_agent_skills()
    print(f"✓ Agent Skillsとはセクション: {len(what_is)}文字")
    
    safety = generator.generate_safety_section()
    print(f"✓ 安全性とリスクセクション: {len(safety)}文字")
    
    prerequisites = generator.generate_prerequisites_section()
    print(f"✓ 前提ソフトウェアセクション: {len(prerequisites)}文字")
    
    # 9. 全体の文字数を計算
    total_length = (
        len(introduction) +
        len(what_is) +
        len(safety) +
        len(prerequisites) +
        len(conclusion)
    )
    
    # スキル説明の文字数を追加
    for category, skill_list in categorized_skills.items():
        for skill in skill_list:
            description = generator.generate_skill_description(skill)
            total_length += len(description)
    
    print(f"\n✓ 全セクションの合計文字数: {total_length}文字")
    
    # 10. 品質チェック
    print("\n=== 品質チェック ===\n")
    
    # 文字数チェック
    min_length = 5000
    if total_length >= min_length:
        print(f"✓ 文字数チェック: OK（{total_length} >= {min_length}）")
    else:
        print(f"⚠ 文字数チェック: 不足（{total_length} < {min_length}）")
    
    # セクション存在チェック
    required_sections = [
        ("はじめに", introduction),
        ("Agent Skillsとは", what_is),
        ("安全性とリスク", safety),
        ("前提ソフトウェア", prerequisites),
        ("まとめ", conclusion)
    ]
    
    all_sections_ok = True
    for section_name, section_content in required_sections:
        if section_content and len(section_content) > 0:
            print(f"✓ {section_name}セクション: 存在")
        else:
            print(f"❌ {section_name}セクション: 欠落")
            all_sections_ok = False
    
    # 最終結果
    print("\n=== テスト結果 ===\n")
    if all_sections_ok and total_length >= min_length:
        print("✅ すべてのテストに合格しました！")
        print("   Task 5.4の実装は正常に動作しています。")
    else:
        print("⚠ 一部のテストに問題があります。")
    
    print("\n=== Task 5.4 完全テスト終了 ===")


if __name__ == "__main__":
    test_complete_workflow()
