"""
設定とデータモデル

Config、SkillData、ProcessingResultのデータクラスを定義します。
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

from .constants import (
    DEFAULT_SKILLS_DIRECTORY,
    DEFAULT_OUTPUT_DIRECTORY,
    DEFAULT_ARTICLE_TITLE,
    DEFAULT_TARGET_AUDIENCE,
    DEFAULT_MAX_SKILL_DESCRIPTION_LENGTH,
    DEFAULT_LOG_LEVEL,
    DEFAULT_LOG_FILE,
    DEFAULT_TRANSLATION_ENABLED,
    DEFAULT_TRANSLATION_PROVIDER,
    DEFAULT_TRANSLATION_MODEL,
    DEFAULT_TRANSLATION_CACHE_FILE,
    DEFAULT_TRANSLATION_TARGET_LANGUAGE,
    DEFAULT_TRANSLATION_API_KEY_ENV,
    DEFAULT_TRANSLATION_BASE_URL,
    DEFAULT_TRANSLATION_TIMEOUT_SEC,
    DEFAULT_TRANSLATION_HTTP_REFERER,
    DEFAULT_TRANSLATION_X_TITLE,
    DEFAULT_DIAGRAMS_ENABLED,
    DEFAULT_IMAGES_SUBDIR,
    CATEGORY_ORDER
)


@dataclass
class SkillData:
    """
    スキルの構造化データ
    
    SKILL.mdファイルから解析された情報を保持します。
    """
    name: str                           # スキル名（必須）
    description: str                    # 説明（必須）
    license: Optional[str] = None       # ライセンス情報
    directory_path: Optional[Path] = None  # スキルディレクトリのパス
    markdown_body: str = ""             # Markdown本文
    has_scripts: bool = False           # scripts/ディレクトリの有無
    has_references: bool = False        # references/ディレクトリの有無
    has_assets: bool = False            # assets/ディレクトリの有無
    has_templates: bool = False         # templates/ディレクトリの有無
    
    def __post_init__(self):
        """データクラス初期化後の検証"""
        if not self.name:
            raise ValueError("スキル名（name）は必須です")
        if not self.description:
            raise ValueError("説明（description）は必須です")


@dataclass
class ProcessingResult:
    """
    処理結果の統計情報
    
    スキル処理の成功/失敗/スキップ数を記録します。
    """
    success_count: int = 0              # 成功したスキル数
    skip_count: int = 0                 # スキップしたスキル数
    error_count: int = 0                # エラーが発生したスキル数
    skipped_skills: List[str] = field(default_factory=list)  # スキップしたスキル名のリスト
    error_messages: List[str] = field(default_factory=list)  # エラーメッセージのリスト
    
    def add_success(self) -> None:
        """成功カウントを増やす"""
        self.success_count += 1
    
    def add_skip(self, skill_name: str) -> None:
        """スキップカウントを増やし、スキル名を記録"""
        self.skip_count += 1
        self.skipped_skills.append(skill_name)
    
    def add_error(self, skill_name: str, error_message: str) -> None:
        """エラーカウントを増やし、エラー情報を記録"""
        self.error_count += 1
        self.error_messages.append(f"{skill_name}: {error_message}")
    
    @property
    def total_processed(self) -> int:
        """処理したスキルの総数"""
        return self.success_count + self.skip_count + self.error_count
    
    @property
    def has_errors(self) -> bool:
        """エラーが発生したかどうか"""
        return self.error_count > 0


@dataclass
class Config:
    """
    システム設定
    
    JSONファイルから読み込むか、デフォルト値を使用します。
    """
    # 入出力パス
    skills_directory: Path = field(default_factory=lambda: Path(DEFAULT_SKILLS_DIRECTORY))
    output_directory: Path = field(default_factory=lambda: Path(DEFAULT_OUTPUT_DIRECTORY))
    
    # 記事設定
    article_title: str = DEFAULT_ARTICLE_TITLE
    target_audience: str = DEFAULT_TARGET_AUDIENCE  # 初学者、中級者、上級者
    max_skill_description_length: int = DEFAULT_MAX_SKILL_DESCRIPTION_LENGTH
    
    # カテゴリ設定
    included_categories: List[str] = field(default_factory=lambda: CATEGORY_ORDER.copy())
    
    # ログ設定
    log_level: str = DEFAULT_LOG_LEVEL  # DEBUG, INFO, WARNING, ERROR
    log_file: Path = field(default_factory=lambda: Path(DEFAULT_LOG_FILE))

    # 翻訳設定（各スキル説明をClaude APIで日本語化する）
    translation_enabled: bool = DEFAULT_TRANSLATION_ENABLED
    translation_provider: str = DEFAULT_TRANSLATION_PROVIDER  # "anthropic" / "openrouter"
    translation_model: str = DEFAULT_TRANSLATION_MODEL
    translation_target_language: str = DEFAULT_TRANSLATION_TARGET_LANGUAGE
    translation_api_key_env: str = DEFAULT_TRANSLATION_API_KEY_ENV
    translation_cache_file: Path = field(
        default_factory=lambda: Path(DEFAULT_TRANSLATION_CACHE_FILE)
    )
    # OpenRouter等のOpenAI互換エンドポイントを使う場合に指定
    translation_base_url: str = DEFAULT_TRANSLATION_BASE_URL
    translation_timeout_sec: int = DEFAULT_TRANSLATION_TIMEOUT_SEC
    translation_http_referer: str = DEFAULT_TRANSLATION_HTTP_REFERER
    translation_x_title: str = DEFAULT_TRANSLATION_X_TITLE

    # 図表設定（記事に図を埋め込む）
    diagrams_enabled: bool = DEFAULT_DIAGRAMS_ENABLED
    images_subdir: str = DEFAULT_IMAGES_SUBDIR  # output_directory 配下の画像保存サブディレクトリ名
    
    @classmethod
    def from_json(cls, json_path: Path) -> 'Config':
        """
        JSONファイルから設定を読み込む
        
        Args:
            json_path: 設定ファイルのパス
            
        Returns:
            Configインスタンス
            
        Raises:
            FileNotFoundError: ファイルが存在しない場合
            json.JSONDecodeError: JSON形式が不正な場合
            ValueError: 設定値が不正な場合
        """
        if not json_path.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Pathオブジェクトに変換
        if 'skills_directory' in data:
            data['skills_directory'] = Path(data['skills_directory'])
        if 'output_directory' in data:
            data['output_directory'] = Path(data['output_directory'])
        if 'log_file' in data:
            data['log_file'] = Path(data['log_file'])
        if 'translation_cache_file' in data:
            data['translation_cache_file'] = Path(data['translation_cache_file'])

        return cls(**data)
    
    @classmethod
    def default(cls) -> 'Config':
        """
        デフォルト設定を返す
        
        Returns:
            デフォルト値を持つConfigインスタンス
        """
        return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        設定を辞書形式に変換する
        
        Returns:
            設定の辞書表現
        """
        return {
            'skills_directory': str(self.skills_directory),
            'output_directory': str(self.output_directory),
            'article_title': self.article_title,
            'target_audience': self.target_audience,
            'max_skill_description_length': self.max_skill_description_length,
            'included_categories': self.included_categories,
            'log_level': self.log_level,
            'log_file': str(self.log_file),
            'translation_enabled': self.translation_enabled,
            'translation_provider': self.translation_provider,
            'translation_model': self.translation_model,
            'translation_target_language': self.translation_target_language,
            'translation_api_key_env': self.translation_api_key_env,
            'translation_cache_file': str(self.translation_cache_file),
            'translation_base_url': self.translation_base_url,
            'translation_timeout_sec': self.translation_timeout_sec,
            'translation_http_referer': self.translation_http_referer,
            'translation_x_title': self.translation_x_title,
            'diagrams_enabled': self.diagrams_enabled,
            'images_subdir': self.images_subdir,
        }
    
    def validate(self) -> List[str]:
        """
        設定の妥当性を検証する
        
        Returns:
            検証エラーメッセージのリスト（空の場合は問題なし）
        """
        errors = []
        
        # ログレベルの検証
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level not in valid_log_levels:
            errors.append(f"不正なログレベル: {self.log_level}。有効な値: {', '.join(valid_log_levels)}")
        
        # 対象読者の検証
        valid_audiences = ['初学者', '中級者', '上級者']
        if self.target_audience not in valid_audiences:
            errors.append(f"不正な対象読者: {self.target_audience}。有効な値: {', '.join(valid_audiences)}")
        
        # 最大文字数の検証
        if self.max_skill_description_length < 100:
            errors.append(f"max_skill_description_lengthが小さすぎます: {self.max_skill_description_length}（最小100）")
        
        # スキルディレクトリの存在確認
        if not self.skills_directory.exists():
            errors.append(f"スキルディレクトリが存在しません: {self.skills_directory}")
        
        return errors
