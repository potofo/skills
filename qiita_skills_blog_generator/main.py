"""
エントリーポイント

コマンドラインからQiita Skills Blog Generatorを実行するための
エントリーポイントです。

使用例:
    # デフォルト設定で実行
    python -m qiita_skills_blog_generator.main

    # カスタム設定ファイルで実行
    python -m qiita_skills_blog_generator.main --config config.json

    # 既存ファイルを確認なしで上書き
    python -m qiita_skills_blog_generator.main --force

    # ヘルプを表示
    python -m qiita_skills_blog_generator.main --help

要件: 9.1, 9.2, 9.3, 9.4
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .controller import MainController


# プログラム名と説明（--help 表示時に利用される）
PROG_NAME = "qiita_skills_blog_generator"
PROG_DESCRIPTION = (
    "Claude用Agent Skillsリポジトリのスキルを解析し、"
    "初学者向けQiita技術ブログ記事を自動生成します。"
)
PROG_EPILOG = (
    "設定ファイルを指定しない場合はデフォルト設定で実行します。"
)


def build_arg_parser() -> argparse.ArgumentParser:
    """
    コマンドライン引数パーサを構築する

    Returns:
        構築済みの ``argparse.ArgumentParser``。

    要件:
        9.1: 設定ファイル（JSON形式）から設定を読み込む（``--config``）
        9.2: 設定ファイルが存在しない場合はデフォルト設定を使用する
    """
    parser = argparse.ArgumentParser(
        prog=PROG_NAME,
        description=PROG_DESCRIPTION,
        epilog=PROG_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "設定ファイル（JSON形式）のパス。"
            "指定しない場合はデフォルト設定を使用します。"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "既存の出力ファイルを確認なしで上書きします（非対話実行向け）。"
        ),
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """
    エントリーポイント

    コマンドライン引数をパースし、 ``MainController`` を実行します。

    Args:
        argv: コマンドライン引数のリスト（テスト用）。
            ``None`` の場合は ``sys.argv[1:]`` を使用します。

    Returns:
        終了コード。 0=成功、 1=エラー。

    要件:
        9.1: 設定ファイルから設定を読み込む
        9.2: 設定ファイルが存在しない場合はデフォルト設定を使用する
        9.3: 設定ファイルが不正な場合はデフォルト設定を使用する
        9.4: 使用した設定内容をログに記録する
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        controller = MainController(config_path=args.config)
        result = controller.run(force=args.force)
    except KeyboardInterrupt:
        # ユーザーによる中断
        print("処理が中断されました", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        # 予期しないエラーは標準エラー出力に出して終了コード1で終了する
        print(
            f"予期しないエラーが発生しました: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    # ProcessingResult.has_errors（error_count > 0）でエラーの有無を判定
    if result.has_errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
