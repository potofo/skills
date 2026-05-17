"""
スキル解析モジュール

SKILL.mdファイルを解析し、構造化データを抽出します。
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import re
import logging

try:
    import yaml
except ImportError:
    raise ImportError(
        "PyYAMLがインストールされていません。以下のコマンドでインストールしてください:\n"
        "pip install pyyaml"
    )

from .config import SkillData


class SkillAnalyzer:
    """
    スキル解析クラス
    
    SKILL.mdファイルを読み込み、YAMLフロントマターとMarkdown本文を解析します。
    """
    
    def __init__(self):
        """SkillAnalyzerを初期化"""
        self.logger = logging.getLogger(__name__)
    
    def scan_skills_directory(self, skills_path: Path) -> List[Path]:
        """
        skills/ディレクトリを走査し、SKILL.mdファイルのパスリストを返す
        
        Args:
            skills_path: スキルディレクトリのパス
            
        Returns:
            SKILL.mdファイルのパスリスト
            
        Raises:
            FileNotFoundError: スキルディレクトリが存在しない場合
        """
        if not skills_path.exists():
            raise FileNotFoundError(f"スキルディレクトリが存在しません: {skills_path}")
        
        if not skills_path.is_dir():
            raise NotADirectoryError(f"パスがディレクトリではありません: {skills_path}")
        
        skill_files = []
        
        # skills/ディレクトリ配下のすべてのサブディレクトリを走査
        for skill_dir in skills_path.iterdir():
            if not skill_dir.is_dir():
                continue
            
            # SKILL.mdファイルを探す
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists() and skill_file.is_file():
                skill_files.append(skill_file)
                self.logger.debug(f"SKILL.mdファイルを発見: {skill_file}")
        
        self.logger.info(f"{len(skill_files)}個のSKILL.mdファイルを発見しました")
        return skill_files
    
    def parse_skill_file(self, skill_path: Path) -> Optional[SkillData]:
        """
        SKILL.mdファイルを解析し、SkillDataオブジェクトを返す
        
        要件7.1〜7.3に対応するため、エラーをフェーズごとに切り分けて
        ログを記録します:
            - フェーズ1: ファイル読み込み（要件7.1: ERROR ログ）
            - フェーズ2: YAMLフロントマター解析（要件7.2: ERROR ログ）
            - フェーズ3: 必須フィールド検証（要件7.3: WARNING ログ）
            - フェーズ4: Markdown本文抽出と SkillData 構築
        
        Args:
            skill_path: SKILL.mdファイルのパス
            
        Returns:
            SkillDataオブジェクト、解析に失敗した場合はNone
        
        要件: 7.1, 7.2, 7.3
        """
        # フェーズ1: ファイル読み込み（要件7.1）
        try:
            with open(skill_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            self.logger.error(
                f"SKILL.mdファイルが存在しません: {skill_path}\n"
                f"対処: ファイルパスとディレクトリ構造を確認してください"
            )
            return None
        except PermissionError:
            self.logger.error(
                f"SKILL.mdファイルの読み込み権限がありません: {skill_path}\n"
                f"対処: ファイルのパーミッションを確認してください"
            )
            return None
        except UnicodeDecodeError as e:
            self.logger.error(
                f"SKILL.mdファイルのエンコーディングエラー: {skill_path}\n"
                f"原因: {str(e)}\n"
                f"対処: SKILL.mdをUTF-8で保存し直してください"
            )
            return None
        except OSError as e:
            self.logger.error(
                f"SKILL.mdファイルの読み込みに失敗しました: {skill_path}\n"
                f"原因: {type(e).__name__}: {str(e)}"
            )
            return None
        
        # フェーズ2: YAMLフロントマター解析（要件7.2）
        try:
            frontmatter = self.extract_yaml_frontmatter(content)
        except ValueError as e:
            self.logger.error(
                f"YAMLフロントマターの解析に失敗しました: {skill_path}\n"
                f"原因: {str(e)}\n"
                f"対処: SKILL.md冒頭の'---'で囲まれたYAMLブロックを確認してください"
            )
            return None
        
        # フェーズ3: 必須フィールド検証（要件7.3）
        # 'name'/'description' が欠けている、または空・None の場合は警告ログを残してスキップ
        name = frontmatter.get('name')
        description = frontmatter.get('description')
        if not name:
            self.logger.warning(
                f"必須フィールド'name'が欠けているか空です: {skill_path}\n"
                f"対処: SKILL.mdのYAMLフロントマターに'name'を追加してください"
            )
            return None
        if not description:
            self.logger.warning(
                f"必須フィールド'description'が欠けているか空です: {skill_path}\n"
                f"対処: SKILL.mdのYAMLフロントマターに'description'を追加してください"
            )
            return None
        
        # フェーズ4: Markdown本文抽出とSkillData構築
        try:
            markdown_body = self.extract_markdown_body(content)
            skill_dir = skill_path.parent
            bundled_resources = self.check_bundled_resources(skill_dir)
            skill_data = SkillData(
                name=name,
                description=description,
                license=frontmatter.get('license'),
                directory_path=skill_dir,
                markdown_body=markdown_body,
                has_scripts=bundled_resources['scripts'],
                has_references=bundled_resources['references'],
                has_assets=bundled_resources['assets'],
                has_templates=bundled_resources['templates']
            )
        except ValueError as e:
            # SkillData.__post_init__ の検証失敗など
            self.logger.error(
                f"SkillDataの作成に失敗しました: {skill_path}\n"
                f"原因: {str(e)}"
            )
            return None
        except Exception as e:
            self.logger.error(
                f"スキルファイルの解析中に予期しないエラーが発生しました: {skill_path}\n"
                f"原因: {type(e).__name__}: {str(e)}"
            )
            return None
        
        self.logger.info(f"スキルを解析しました: {skill_data.name}")
        return skill_data
    
    def extract_yaml_frontmatter(self, content: str) -> Dict[str, Any]:
        """
        YAMLフロントマターを抽出してパースする
        
        Args:
            content: SKILL.mdファイルの内容
            
        Returns:
            パースされたYAMLデータの辞書
            
        Raises:
            ValueError: YAMLフロントマターが見つからない、または不正な場合
        """
        # YAMLフロントマターのパターン: ---で囲まれた部分
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, content, re.DOTALL)
        
        if not match:
            raise ValueError("YAMLフロントマターが見つかりません")
        
        yaml_content = match.group(1)
        
        try:
            # YAMLをパース
            frontmatter = yaml.safe_load(yaml_content)
            
            if frontmatter is None:
                raise ValueError("YAMLフロントマターが空です")
            
            if not isinstance(frontmatter, dict):
                raise ValueError("YAMLフロントマターが辞書形式ではありません")
            
            return frontmatter
            
        except yaml.YAMLError as e:
            raise ValueError(f"YAMLのパースに失敗しました: {str(e)}")
    
    def extract_markdown_body(self, content: str) -> str:
        """
        Markdown本文を抽出する
        
        Args:
            content: SKILL.mdファイルの内容
            
        Returns:
            Markdown本文（YAMLフロントマターを除いた部分）
        """
        # YAMLフロントマターのパターン: ---で囲まれた部分
        pattern = r'^---\s*\n.*?\n---\s*\n'
        
        # YAMLフロントマターを削除
        markdown_body = re.sub(pattern, '', content, count=1, flags=re.DOTALL)
        
        # 前後の空白を削除
        markdown_body = markdown_body.strip()
        
        return markdown_body
    
    def check_bundled_resources(self, skill_dir: Path) -> Dict[str, bool]:
        """
        バンドルリソースディレクトリの存在を確認する
        
        Args:
            skill_dir: スキルディレクトリのパス
            
        Returns:
            各リソースディレクトリの存在を示す辞書
            {
                'scripts': bool,
                'references': bool,
                'assets': bool,
                'templates': bool
            }
        """
        resource_dirs = ['scripts', 'references', 'assets', 'templates']
        
        result = {}
        for dir_name in resource_dirs:
            dir_path = skill_dir / dir_name
            result[dir_name] = dir_path.exists() and dir_path.is_dir()
        
        return result
