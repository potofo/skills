"""
定数定義

カテゴリマッピングやその他の定数を定義します。
"""

from typing import Dict, List

# プロプライエタリライセンスを持つドキュメントスキル
# これらのスキルはソース公開だがプロプライエタリで、参照・学習用に提供されている
DOCUMENT_SKILLS: List[str] = [
    "docx",
    "pdf",
    "pptx",
    "xlsx",
]

# スキルのカテゴリマッピング
CATEGORY_MAPPING: Dict[str, List[str]] = {
    "クリエイティブ&デザイン": [
        "algorithmic-art",
        "canvas-design",
        "frontend-design",
        "theme-factory"
    ],
    "開発&技術": [
        "claude-api",
        "mcp-builder",
        "webapp-testing",
        "web-artifacts-builder"
    ],
    "ドキュメント処理": [
        "docx",
        "pdf",
        "pptx",
        "xlsx"
    ],
    "エンタープライズ&コミュニケーション": [
        "brand-guidelines",
        "doc-coauthoring",
        "internal-comms",
        "slack-gif-creator"
    ],
    "メタスキル": [
        "skill-creator"
    ]
}

# カテゴリの順序（記事での表示順）
CATEGORY_ORDER: List[str] = [
    "クリエイティブ&デザイン",
    "開発&技術",
    "ドキュメント処理",
    "エンタープライズ&コミュニケーション",
    "メタスキル"
]

# デフォルト設定値
DEFAULT_SKILLS_DIRECTORY = "skills"
DEFAULT_OUTPUT_DIRECTORY = "output"
DEFAULT_ARTICLE_TITLE = "Claude Agent Skills完全ガイド：初学者のための実践的スキル解説"
DEFAULT_TARGET_AUDIENCE = "初学者"
DEFAULT_MAX_SKILL_DESCRIPTION_LENGTH = 400
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FILE = "logs/qiita_generator.log"

# 翻訳機能のデフォルト設定
# 各スキルの説明文をClaude APIで日本語に翻訳します。
# APIキーが未設定の場合は翻訳をスキップして元の英語をそのまま使用します。
DEFAULT_TRANSLATION_ENABLED = True
DEFAULT_TRANSLATION_PROVIDER = "anthropic"  # "anthropic" または "openrouter"
DEFAULT_TRANSLATION_MODEL = "claude-haiku-4-5"  # 軽量で安価なモデルを既定とする
DEFAULT_TRANSLATION_CACHE_FILE = ".cache/translations.json"
DEFAULT_TRANSLATION_TARGET_LANGUAGE = "日本語"
DEFAULT_TRANSLATION_API_KEY_ENV = "ANTHROPIC_API_KEY"
DEFAULT_TRANSLATION_BASE_URL = ""  # OpenRouter等のカスタムエンドポイントを使う場合に指定
DEFAULT_TRANSLATION_TIMEOUT_SEC = 60
# OpenRouter利用時の推奨ヘッダ（公開推奨。任意）
DEFAULT_TRANSLATION_HTTP_REFERER = ""
DEFAULT_TRANSLATION_X_TITLE = ""

# 図表生成のデフォルト設定
DEFAULT_DIAGRAMS_ENABLED = True
# 画像はoutput_directory配下のこのサブディレクトリに保存される（例: output/images/）
DEFAULT_IMAGES_SUBDIR = "images"

# 品質検証基準
MIN_ARTICLE_LENGTH = 5000  # 最小文字数
REQUIRED_SECTIONS = [
    "はじめに",
    "Agent Skillsとは",
    "Agent Skillsの安全性とリスク",
    "Agent Skillsを利用・開発するための前提ソフトウェア",
    "スキル一覧",
    "まとめ"
]
