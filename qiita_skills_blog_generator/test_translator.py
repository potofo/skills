"""
Translator のユニットテスト

Claude API の呼び出しは行わず、すべてモックで検証します。
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from qiita_skills_blog_generator.config import Config
from qiita_skills_blog_generator.translator import (
    Translator,
    build_translator_from_config,
)


def _make_response(text: str) -> SimpleNamespace:
    """Anthropic SDK の messages.create レスポンスを模したオブジェクトを返す"""
    return SimpleNamespace(content=[SimpleNamespace(text=text)])


def _make_openai_response(text: str) -> SimpleNamespace:
    """OpenAI互換 API の chat.completions.create レスポンスを模したオブジェクト"""
    return SimpleNamespace(
        choices=[
            SimpleNamespace(message=SimpleNamespace(content=text))
        ]
    )


class TranslatorBasicBehaviorTests(unittest.TestCase):
    """正常系・APIモック差し替えで動作を検証する"""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.cache_file = Path(self.tempdir.name) / "translations.json"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_translate_uses_injected_client(self) -> None:
        """注入したクライアントが呼ばれ、翻訳テキストが返ること"""
        client = MagicMock()
        client.messages.create.return_value = _make_response("こんにちは")

        translator = Translator(
            model="claude-haiku-4-5",
            api_key_env="DUMMY_KEY",
            target_language="日本語",
            cache_file=self.cache_file,
            client=client,
        )

        result = translator.translate("Hello")

        self.assertEqual(result, "こんにちは")
        client.messages.create.assert_called_once()
        kwargs = client.messages.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "claude-haiku-4-5")
        # ユーザーメッセージは <source_text> でラップされて渡される
        self.assertEqual(len(kwargs["messages"]), 1)
        self.assertEqual(kwargs["messages"][0]["role"], "user")
        self.assertIn("<source_text>", kwargs["messages"][0]["content"])
        self.assertIn("Hello", kwargs["messages"][0]["content"])
        self.assertIn("</source_text>", kwargs["messages"][0]["content"])
        self.assertIn("日本語", kwargs["system"])

    def test_translate_caches_results(self) -> None:
        """同じ入力は2回目以降キャッシュから返されAPIが再呼び出しされない"""
        client = MagicMock()
        client.messages.create.return_value = _make_response("テスト")

        translator = Translator(
            model="claude-haiku-4-5",
            api_key_env="DUMMY_KEY",
            target_language="日本語",
            cache_file=self.cache_file,
            client=client,
        )

        first = translator.translate("Test")
        second = translator.translate("Test")

        self.assertEqual(first, "テスト")
        self.assertEqual(second, "テスト")
        client.messages.create.assert_called_once()
        # キャッシュファイルが永続化されている
        self.assertTrue(self.cache_file.exists())
        cache_data = json.loads(self.cache_file.read_text(encoding="utf-8"))
        self.assertEqual(len(cache_data), 1)

    def test_translate_loads_cache_from_disk(self) -> None:
        """ディスクに保存されたキャッシュが起動時に読み込まれる"""
        client = MagicMock()
        # 事前にキャッシュファイルを作成（同じキー算出ロジックを利用）
        existing_translator = Translator(
            model="claude-haiku-4-5",
            api_key_env="DUMMY_KEY",
            target_language="日本語",
            cache_file=self.cache_file,
            client=MagicMock(messages=MagicMock(
                create=MagicMock(return_value=_make_response("永続翻訳"))
            )),
        )
        existing_translator.translate("Persisted")
        self.assertTrue(self.cache_file.exists())

        # 別インスタンスで同じテキストを翻訳 → APIは呼ばれない
        new_translator = Translator(
            model="claude-haiku-4-5",
            api_key_env="DUMMY_KEY",
            target_language="日本語",
            cache_file=self.cache_file,
            client=client,
        )
        result = new_translator.translate("Persisted")

        self.assertEqual(result, "永続翻訳")
        client.messages.create.assert_not_called()

    def test_translate_strips_whitespace_from_response(self) -> None:
        """APIレスポンスの前後の空白は取り除かれる"""
        client = MagicMock()
        client.messages.create.return_value = _make_response(
            "\n  翻訳結果  \n"
        )

        translator = Translator(
            model="claude-haiku-4-5",
            api_key_env="DUMMY_KEY",
            target_language="日本語",
            cache_file=None,
            client=client,
        )

        self.assertEqual(translator.translate("Hello"), "翻訳結果")

    def test_translate_returns_empty_input_unchanged(self) -> None:
        """空文字列はAPIを呼び出さずそのまま返す"""
        client = MagicMock()
        translator = Translator(
            model="m",
            api_key_env="DUMMY_KEY",
            target_language="日本語",
            cache_file=None,
            client=client,
        )

        self.assertEqual(translator.translate(""), "")
        self.assertEqual(translator.translate("   "), "   ")
        client.messages.create.assert_not_called()


class TranslatorFallbackTests(unittest.TestCase):
    """APIキー未設定 / SDK未インストール / API失敗時のフォールバック挙動"""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.cache_file = Path(self.tempdir.name) / "translations.json"
        # 環境変数を退避してテスト中は確実に未設定にする
        self._saved_env = os.environ.pop("TEST_TRANSLATOR_KEY", None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()
        if self._saved_env is not None:
            os.environ["TEST_TRANSLATOR_KEY"] = self._saved_env

    def test_returns_original_when_api_key_missing(self) -> None:
        """APIキーが未設定なら元のテキストをそのまま返す"""
        translator = Translator(
            model="claude-haiku-4-5",
            api_key_env="TEST_TRANSLATOR_KEY",  # 未設定の環境変数
            target_language="日本語",
            cache_file=self.cache_file,
        )

        result = translator.translate("Hello world")

        self.assertEqual(result, "Hello world")
        self.assertFalse(self.cache_file.exists())

    def test_returns_original_when_client_factory_fails(self) -> None:
        """クライアント生成が例外を投げても元のテキストを返す"""

        def failing_factory(api_key: str) -> object:
            raise RuntimeError("client init failed")

        translator = Translator(
            model="claude-haiku-4-5",
            api_key_env="TEST_TRANSLATOR_KEY",
            target_language="日本語",
            cache_file=None,
            client_factory=failing_factory,
        )

        with patch.dict(
            os.environ, {"TEST_TRANSLATOR_KEY": "fake-key"}, clear=False
        ):
            result = translator.translate("Hello")

        self.assertEqual(result, "Hello")

    def test_returns_original_when_api_call_raises(self) -> None:
        """API呼び出しが例外を投げたら元のテキストを返す"""
        client = MagicMock()
        client.messages.create.side_effect = RuntimeError("network error")

        translator = Translator(
            model="claude-haiku-4-5",
            api_key_env="DUMMY_KEY",
            target_language="日本語",
            cache_file=None,
            client=client,
        )

        result = translator.translate("Hello")

        self.assertEqual(result, "Hello")
        client.messages.create.assert_called_once()

    def test_returns_original_when_response_is_empty(self) -> None:
        """API が空のレスポンスを返した場合は元のテキストを返す"""
        client = MagicMock()
        client.messages.create.return_value = _make_response("")

        translator = Translator(
            model="claude-haiku-4-5",
            api_key_env="DUMMY_KEY",
            target_language="日本語",
            cache_file=None,
            client=client,
        )

        self.assertEqual(translator.translate("Hello"), "Hello")


class BuildTranslatorFromConfigTests(unittest.TestCase):
    """build_translator_from_config の組み立てロジックを検証"""

    def test_returns_none_when_translation_disabled(self) -> None:
        config = Config.default()
        config.translation_enabled = False

        translator = build_translator_from_config(config)

        self.assertIsNone(translator)

    def test_returns_translator_with_config_values(self) -> None:
        config = Config.default()
        config.translation_enabled = True
        config.translation_model = "claude-haiku-4-5"
        config.translation_api_key_env = "ANTHROPIC_API_KEY"
        config.translation_target_language = "日本語"
        config.translation_cache_file = Path(".cache/test.json")

        translator = build_translator_from_config(config)

        self.assertIsInstance(translator, Translator)
        self.assertEqual(translator.model, "claude-haiku-4-5")
        self.assertEqual(translator.api_key_env, "ANTHROPIC_API_KEY")
        self.assertEqual(translator.target_language, "日本語")
        self.assertEqual(translator.cache_file, Path(".cache/test.json"))


if __name__ == "__main__":
    unittest.main()


class TranslatorOpenRouterTests(unittest.TestCase):
    """OpenRouter（OpenAI互換）プロバイダーの動作を検証する"""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.cache_file = Path(self.tempdir.name) / "translations.json"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_openrouter_uses_chat_completions(self) -> None:
        """OpenRouterプロバイダーでは chat.completions.create が呼ばれる"""
        client = MagicMock()
        client.chat.completions.create.return_value = _make_openai_response(
            "翻訳結果"
        )

        translator = Translator(
            model="anthropic/claude-3.5-sonnet",
            api_key_env="DUMMY_KEY",
            target_language="日本語",
            provider="openrouter",
            cache_file=self.cache_file,
            client=client,
        )

        result = translator.translate("Hello")

        self.assertEqual(result, "翻訳結果")
        client.chat.completions.create.assert_called_once()
        kwargs = client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "anthropic/claude-3.5-sonnet")
        # system + user の2メッセージ構成
        self.assertEqual(len(kwargs["messages"]), 2)
        self.assertEqual(kwargs["messages"][0]["role"], "system")
        self.assertEqual(kwargs["messages"][1]["role"], "user")
        # ユーザーメッセージは <source_text> でラップされて渡される
        self.assertIn("<source_text>", kwargs["messages"][1]["content"])
        self.assertIn("Hello", kwargs["messages"][1]["content"])
        self.assertIn("</source_text>", kwargs["messages"][1]["content"])

    def test_openrouter_caches_separately_from_anthropic(self) -> None:
        """同じテキストでもプロバイダーが違えばキャッシュキーが分かれる"""
        anth_client = MagicMock()
        anth_client.messages.create.return_value = _make_response(
            "Anthropic翻訳"
        )

        or_client = MagicMock()
        or_client.chat.completions.create.return_value = (
            _make_openai_response("OpenRouter翻訳")
        )

        cache_file = self.cache_file
        anth = Translator(
            model="claude-haiku-4-5",
            api_key_env="K",
            target_language="日本語",
            provider="anthropic",
            cache_file=cache_file,
            client=anth_client,
        )
        or_t = Translator(
            model="claude-haiku-4-5",
            api_key_env="K",
            target_language="日本語",
            provider="openrouter",
            cache_file=cache_file,
            client=or_client,
        )

        self.assertEqual(anth.translate("Hello"), "Anthropic翻訳")
        self.assertEqual(or_t.translate("Hello"), "OpenRouter翻訳")

        cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
        self.assertEqual(len(cache_data), 2)

    def test_openrouter_returns_original_when_response_empty(self) -> None:
        """OpenRouterレスポンスのcontentが空ならフォールバック"""
        client = MagicMock()
        client.chat.completions.create.return_value = _make_openai_response(
            ""
        )

        translator = Translator(
            model="anthropic/claude-3.5-sonnet",
            api_key_env="K",
            target_language="日本語",
            provider="openrouter",
            cache_file=None,
            client=client,
        )

        self.assertEqual(translator.translate("Hello"), "Hello")


class TranslatorValidationTests(unittest.TestCase):
    """翻訳結果の妥当性検証（フォールバック動作）を検証する"""

    def test_returns_original_when_translation_has_no_japanese(self) -> None:
        """翻訳結果に日本語文字がなければ元のテキストを返す"""
        client = MagicMock()
        # LLMが指示への英語応答を返した想定
        client.messages.create.return_value = _make_response(
            "I understand. I'm ready to help."
        )

        translator = Translator(
            model="m",
            api_key_env="K",
            target_language="日本語",
            cache_file=None,
            client=client,
        )

        original = "Create distinctive frontend interfaces."
        result = translator.translate(original)

        self.assertEqual(result, original)
        # 不正と判定されたのでキャッシュには保存されない（再試行可能）
        # （cache_file=None なので副作用は出ない）

    def test_returns_original_when_translation_too_long(self) -> None:
        """翻訳結果が原文の3倍を超えたら元のテキストを返す"""
        client = MagicMock()
        # LLMが大幅に情報を追加した想定
        very_long_jp = "日本語の翻訳結果。" * 200  # ~1800 chars
        client.messages.create.return_value = _make_response(very_long_jp)

        translator = Translator(
            model="m",
            api_key_env="K",
            target_language="日本語",
            cache_file=None,
            client=client,
        )

        # 原文は短い (~50 chars)
        original = "Short original text for testing the length cap."
        result = translator.translate(original)

        self.assertEqual(result, original)

    def test_accepts_normal_japanese_translation(self) -> None:
        """正常な日本語翻訳はそのまま採用される"""
        client = MagicMock()
        client.messages.create.return_value = _make_response(
            "正常な日本語の翻訳結果です。"
        )

        translator = Translator(
            model="m",
            api_key_env="K",
            target_language="日本語",
            cache_file=None,
            client=client,
        )

        result = translator.translate("Normal English text.")
        self.assertEqual(result, "正常な日本語の翻訳結果です。")
