"""
ユーティリティ関数

共通で使用される補助関数を定義します。
"""

from pathlib import Path
from typing import Optional
import re


def sanitize_filename(filename: str) -> str:
    """
    ファイル名として安全な文字列に変換する
    
    Args:
        filename: 元のファイル名
        
    Returns:
        サニタイズされたファイル名
    """
    # 危険な文字を削除または置換
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 連続するスペースを1つに
    filename = re.sub(r'\s+', ' ', filename)
    # 前後の空白を削除
    filename = filename.strip()
    return filename


def ensure_directory_exists(directory: Path) -> None:
    """
    ディレクトリが存在しない場合は作成する
    
    Args:
        directory: 作成するディレクトリのパス
    """
    directory.mkdir(parents=True, exist_ok=True)


def is_valid_skill_directory(directory: Path) -> bool:
    """
    有効なスキルディレクトリかどうかを判定する
    
    Args:
        directory: 検証するディレクトリのパス
        
    Returns:
        SKILL.mdファイルが存在する場合True
    """
    if not directory.is_dir():
        return False
    
    skill_file = directory / "SKILL.md"
    return skill_file.exists() and skill_file.is_file()


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    テキストを指定された最大長に切り詰める
    
    Args:
        text: 元のテキスト
        max_length: 最大文字数
        suffix: 切り詰められた場合に追加する接尾辞
        
    Returns:
        切り詰められたテキスト
    """
    if len(text) <= max_length:
        return text
    
    # suffixの長さを考慮して切り詰め
    truncate_at = max_length - len(suffix)
    return text[:truncate_at] + suffix


def count_japanese_characters(text: str) -> int:
    """
    日本語文字を含むテキストの文字数をカウントする
    
    Args:
        text: カウントするテキスト
        
    Returns:
        文字数
    """
    # 改行や空白を除外してカウント
    text_without_whitespace = re.sub(r'\s', '', text)
    return len(text_without_whitespace)
