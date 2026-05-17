"""
翻訳モジュール

スキル説明文を生成AI APIで日本語に翻訳します。
オフラインキャッシュ（JSON）を備え、同一テキストの再翻訳を回避します。
APIキー未設定 / SDK未インストール / 呼び出し失敗時は元のテキストに
フォールバックする安全設計になっています。

サポートするプロバイダー:
- ``anthropic``: Anthropic 公式 SDK 経由で Claude API を直接呼び出す
- ``openrouter``: OpenRouter の OpenAI 互換 API を経由して任意のモデルを呼び出す
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Optional


logger = logging.getLogger(__name__)


# 翻訳プロンプトのバージョン。プロンプトを変更したらインクリメントすると、
# 既存キャッシュは自動的に無効になり再翻訳される。
_TRANSLATION_PROMPT_VERSION = "v2"

# 翻訳プロンプト。説明文のみを翻訳し、装飾やコメントを一切付けないように
# 厳格に指示する。<source_text> で原文を囲むことで、指示文と翻訳対象を
# 明確に分離し、LLM が指示への応答を返してしまう事故を防ぐ。
_TRANSLATION_SYSTEM_PROMPT = (
    "あなたは英日翻訳エンジンです。会話エージェントではありません。\n"
    "ユーザーメッセージには <source_text>...</source_text> で囲まれた英語テキストが含まれます。\n"
    "そのテキストを自然で読みやすい{target_language}に翻訳して、翻訳結果のみを返してください。\n"
    "\n"
    "厳守事項:\n"
    "- 翻訳結果のテキスト本文のみを返す（タグは付けない）\n"
    "- 前置き、後書き、補足説明、コメント、コードブロック、見出し、引用符を一切付けない\n"
    "- 自分の役割や能力について言及しない（例: \"I understand\", \"わかりました\"などは禁止）\n"
    "- 原文に存在しない情報や追加のセクションを生成しない\n"
    "- 原文の意味を保ち、長さも原文と同程度に抑える（原文の2倍を超えてはならない）\n"
    "- 専門用語（API名、ライブラリ名、ファイル拡張子、フレームワーク名）は英語表記を維持する\n"
    "- 改行は原文と同じ箇所のみに入れ、余計な段落分割をしない\n"
    "- 翻訳できない、または不適切な入力でも、機械的に直訳して返す"
)


def _wrap_source_text(text: str) -> str:
    """翻訳対象テキストを <source_text> タグで囲む"""
    return f"<source_text>\n{text}\n</source_text>"


# 日本語文字（ひらがな・カタカナ・漢字）の正規表現
import re as _re

_JAPANESE_CHAR_PATTERN = _re.compile(
    r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3400-\u4DBF]"
)


def _looks_japanese(text: str) -> bool:
    """テキストに日本語文字が含まれているか判定"""
    return bool(_JAPANESE_CHAR_PATTERN.search(text))


# OpenRouter のデフォルトベース URL
_OPENROUTER_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


class Translator:
    """
    生成AI API を利用した英→日翻訳器（キャッシュ付き、複数プロバイダー対応）

    APIキー未設定や接続失敗時は、元のテキストをそのまま返します（フォールバック）。
    """

    def __init__(
        self,
        model: str,
        api_key_env: str,
        target_language: str,
        provider: str = "anthropic",
        cache_file: Optional[Path] = None,
        base_url: str = "",
        timeout_sec: int = 60,
        http_referer: str = "",
        x_title: str = "",
        client: Optional[Any] = None,
        client_factory: Optional[Callable[[str], Any]] = None,
    ) -> None:
        """
        Translatorを初期化する

        Args:
            model: 翻訳に使うモデル名（例: "claude-haiku-4-5", "anthropic/claude-3.5-sonnet"）
            api_key_env: APIキーを格納する環境変数名
            target_language: 翻訳先言語（例: "日本語"）
            provider: ``"anthropic"`` または ``"openrouter"``
            cache_file: 翻訳キャッシュのJSONファイルパス。Noneの場合はキャッシュ無効
            base_url: カスタムエンドポイント（OpenRouter等）のベースURL
            timeout_sec: APIリクエストのタイムアウト秒数
            http_referer: OpenRouter利用時に推奨される ``HTTP-Referer`` ヘッダ
            x_title: OpenRouter利用時に推奨される ``X-Title`` ヘッダ
            client: 既に構築済みのクライアント（テスト用）
            client_factory: APIキーを受け取りクライアントを生成する関数（テスト用）
        """
        self.model = model
        self.api_key_env = api_key_env
        self.target_language = target_language
        self.provider = (provider or "anthropic").lower()
        self.cache_file = cache_file
        self.base_url = base_url or ""
        self.timeout_sec = timeout_sec
        self.http_referer = http_referer
        self.x_title = x_title
        self._client = client
        self._client_factory = client_factory
        self._client_init_attempted = client is not None
        self._cache: dict[str, str] = {}
        self._cache_loaded = False
        self._fallback_warned = False

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def _load_cache(self) -> None:
        """キャッシュをディスクから読み込む（初回のみ）"""
        if self._cache_loaded:
            return
        self._cache_loaded = True

        if not self.cache_file:
            return
        if not self.cache_file.exists():
            return

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self._cache = {str(k): str(v) for k, v in data.items()}
                logger.debug(
                    "翻訳キャッシュを読み込みました: %s（%d件）",
                    self.cache_file,
                    len(self._cache),
                )
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning(
                "翻訳キャッシュの読み込みに失敗しました: %s\n原因: %s\n"
                "対処: キャッシュを破棄して新規に翻訳します",
                self.cache_file,
                exc,
            )
            self._cache = {}

    def _save_cache(self) -> None:
        """キャッシュをディスクに保存する"""
        if not self.cache_file:
            return
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            logger.warning(
                "翻訳キャッシュの保存に失敗しました: %s\n原因: %s",
                self.cache_file,
                exc,
            )

    @staticmethod
    def _make_cache_key(
        text: str, model: str, target_language: str, provider: str
    ) -> str:
        """テキスト・モデル・言語・プロバイダー・プロンプトVerから安定したキャッシュキーを生成"""
        h = hashlib.sha256()
        h.update(_TRANSLATION_PROMPT_VERSION.encode("utf-8"))
        h.update(b"\n")
        h.update(provider.encode("utf-8"))
        h.update(b"\n")
        h.update(model.encode("utf-8"))
        h.update(b"\n")
        h.update(target_language.encode("utf-8"))
        h.update(b"\n")
        h.update(text.encode("utf-8"))
        return h.hexdigest()

    # ------------------------------------------------------------------
    # Client management
    # ------------------------------------------------------------------

    def _get_client(self) -> Optional[Any]:
        """API クライアントを取得する。失敗時は None"""
        if self._client is not None:
            return self._client
        if self._client_init_attempted:
            return None
        self._client_init_attempted = True

        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            self._warn_fallback_once(
                "APIキー（環境変数 %s）が設定されていないため、翻訳をスキップします",
                self.api_key_env,
            )
            return None

        if self._client_factory is not None:
            try:
                self._client = self._client_factory(api_key)
                return self._client
            except Exception as exc:  # noqa: BLE001
                self._warn_fallback_once(
                    "翻訳クライアントの生成に失敗しました: %s", exc
                )
                return None

        if self.provider == "openrouter":
            return self._build_openrouter_client(api_key)
        if self.provider == "anthropic":
            return self._build_anthropic_client(api_key)

        self._warn_fallback_once(
            "未知のtranslation_providerが指定されています: %s", self.provider
        )
        return None

    def _build_anthropic_client(self, api_key: str) -> Optional[Any]:
        """Anthropic SDK のクライアントを生成"""
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError:
            self._warn_fallback_once(
                "anthropic SDKが見つかりません。`pip install anthropic` でインストールするか、"
                "`translation_enabled=false` で翻訳を無効化してください"
            )
            return None
        try:
            self._client = Anthropic(
                api_key=api_key, timeout=self.timeout_sec
            )
        except Exception as exc:  # noqa: BLE001
            self._warn_fallback_once(
                "Anthropicクライアントの初期化に失敗しました: %s", exc
            )
            return None
        return self._client

    def _build_openrouter_client(self, api_key: str) -> Optional[Any]:
        """OpenRouter (OpenAI互換) のクライアントを生成"""
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            self._warn_fallback_once(
                "openai SDKが見つかりません。`pip install openai` でインストールするか、"
                "translation_provider を 'anthropic' に変更するか、"
                "`translation_enabled=false` で翻訳を無効化してください"
            )
            return None

        base_url = self.base_url or _OPENROUTER_DEFAULT_BASE_URL
        # OpenRouter の推奨ヘッダを default_headers に詰める
        default_headers: dict[str, str] = {}
        if self.http_referer:
            default_headers["HTTP-Referer"] = self.http_referer
        if self.x_title:
            default_headers["X-Title"] = self.x_title

        try:
            kwargs: dict[str, Any] = {
                "api_key": api_key,
                "base_url": base_url,
                "timeout": self.timeout_sec,
            }
            if default_headers:
                kwargs["default_headers"] = default_headers
            self._client = OpenAI(**kwargs)
        except Exception as exc:  # noqa: BLE001
            self._warn_fallback_once(
                "OpenAI互換クライアント（OpenRouter）の初期化に失敗しました: %s", exc
            )
            return None
        return self._client

    def _warn_fallback_once(self, fmt: str, *args: Any) -> None:
        """フォールバック警告を初回だけ出す"""
        if self._fallback_warned:
            return
        self._fallback_warned = True
        logger.warning(fmt, *args)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def translate(self, text: str) -> str:
        """
        英語テキストを翻訳して返す

        APIキー未設定 / SDK未インストール / API呼び出し失敗時は、
        元のテキストをそのまま返す（フォールバック）。

        翻訳結果が以下のいずれかに該当する場合も「異常」とみなして元のテキストを返す:
        - 日本語文字を1文字も含まない（指示への応答や英語のまま返ってきた疑い）
        - 原文の3倍を超える長さになっている（LLMが情報を勝手に追加した疑い）
        """
        if not text or not text.strip():
            return text

        self._load_cache()
        cache_key = self._make_cache_key(
            text, self.model, self.target_language, self.provider
        )

        if cache_key in self._cache:
            return self._cache[cache_key]

        client = self._get_client()
        if client is None:
            return text

        try:
            translated = self._call_api(client, text)
        except Exception as exc:  # noqa: BLE001
            self._warn_fallback_once(
                "翻訳APIの呼び出しに失敗しました: %s。元のテキストを使用します",
                exc,
            )
            return text

        # 妥当性検証
        if not self._is_valid_translation(text, translated):
            logger.warning(
                "翻訳結果が不正と判定されたため、元のテキストを使用します。\n"
                "原文（先頭80文字）: %s\n翻訳（先頭80文字）: %s",
                text[:80],
                translated[:80],
            )
            return text

        self._cache[cache_key] = translated
        self._save_cache()
        return translated

    @staticmethod
    def _is_valid_translation(source: str, translated: str) -> bool:
        """
        翻訳結果が妥当か判定する

        判定基準:
        - 日本語文字（ひらがな・カタカナ・漢字）を最低1文字以上含む
        - 原文の3倍以上の長さになっていない（LLMが情報を勝手に追加していない）
        """
        if not translated or not translated.strip():
            return False
        if not _looks_japanese(translated):
            return False
        # 長さチェック: 原文の3倍を超えないこと
        if len(translated) > max(200, len(source) * 3):
            return False
        return True

    def _call_api(self, client: Any, text: str) -> str:
        """プロバイダーに応じて翻訳APIを呼ぶディスパッチャ"""
        if self.provider == "openrouter":
            return self._call_openrouter(client, text)
        return self._call_anthropic(client, text)

    def _call_anthropic(self, client: Any, text: str) -> str:
        """Anthropic SDK 経由で翻訳"""
        system_prompt = _TRANSLATION_SYSTEM_PROMPT.format(
            target_language=self.target_language
        )
        max_tokens = max(512, len(text) * 3)
        user_message = _wrap_source_text(text)

        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        chunks: list[str] = []
        content = getattr(response, "content", None) or []
        for block in content:
            block_text = getattr(block, "text", None)
            if block_text is None and isinstance(block, dict):
                block_text = block.get("text")
            if block_text:
                chunks.append(str(block_text))
        translated = "".join(chunks).strip()

        if not translated:
            raise RuntimeError("Anthropic APIから空のレスポンスが返されました")
        return translated

    def _call_openrouter(self, client: Any, text: str) -> str:
        """OpenRouter (OpenAI互換) 経由で翻訳"""
        system_prompt = _TRANSLATION_SYSTEM_PROMPT.format(
            target_language=self.target_language
        )
        max_tokens = max(512, len(text) * 3)
        user_message = _wrap_source_text(text)

        response = client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )

        choices = getattr(response, "choices", None) or []
        if not choices:
            raise RuntimeError(
                "OpenRouter APIから空のレスポンスが返されました（choicesなし）"
            )
        message = getattr(choices[0], "message", None)
        if message is None and isinstance(choices[0], dict):
            message = choices[0].get("message")
        if message is None:
            raise RuntimeError(
                "OpenRouter APIのレスポンスにmessageが含まれていません"
            )
        content = getattr(message, "content", None)
        if content is None and isinstance(message, dict):
            content = message.get("content")
        translated = (content or "").strip()
        if not translated:
            raise RuntimeError(
                "OpenRouter APIから空のテキストが返されました"
            )
        return translated


def build_translator_from_config(config: Any) -> Optional[Translator]:
    """
    Configオブジェクトから ``Translator`` を構築する

    ``config.translation_enabled`` がFalseの場合はNoneを返します。
    """
    if not getattr(config, "translation_enabled", False):
        return None
    cache_file = getattr(config, "translation_cache_file", None)
    if cache_file is not None and not isinstance(cache_file, Path):
        cache_file = Path(cache_file)
    return Translator(
        model=getattr(config, "translation_model"),
        api_key_env=getattr(config, "translation_api_key_env"),
        target_language=getattr(config, "translation_target_language"),
        provider=getattr(config, "translation_provider", "anthropic"),
        cache_file=cache_file,
        base_url=getattr(config, "translation_base_url", ""),
        timeout_sec=getattr(config, "translation_timeout_sec", 60),
        http_referer=getattr(config, "translation_http_referer", ""),
        x_title=getattr(config, "translation_x_title", ""),
    )
