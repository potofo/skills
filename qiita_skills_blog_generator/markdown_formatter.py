"""
Markdown整形モジュール

Qiita形式のMarkdownを生成します。
"""

from typing import Dict, List
from .constants import CATEGORY_ORDER


class MarkdownFormatter:
    """
    Markdown整形クラス
    
    コンテンツセクションをQiita Markdown形式に整形します。
    """
    
    def __init__(self):
        """MarkdownFormatterを初期化"""
        pass
    
    def format_article(self, content_sections: Dict[str, str]) -> str:
        """
        全セクションを統合してQiita Markdown形式の記事を生成
        
        Args:
            content_sections: セクション名をキー、コンテンツを値とする辞書
                期待されるキー:
                - 'title': 記事タイトル
                - 'introduction': はじめにセクション
                - 'what_is_agent_skills': Agent Skillsとはセクション
                - 'safety': 安全性とリスクセクション
                - 'prerequisites': 前提ソフトウェアセクション
                - 'skills': スキル一覧セクション
                - 'conclusion': まとめセクション
                
        Returns:
            Qiita Markdown形式の完全な記事
        """
        article_parts = []
        
        # タイトル（H1）
        if 'title' in content_sections:
            article_parts.append(self.format_heading(content_sections['title'], 1))
            article_parts.append("")  # 空行
        
        # 目次を生成
        toc_sections = []
        if 'introduction' in content_sections:
            toc_sections.append("はじめに")
        if 'what_is_agent_skills' in content_sections:
            toc_sections.append("Agent Skillsとは")
        if 'history' in content_sections:
            toc_sections.append("Agent Skillsの歴史と公式ロードマップ")
        if 'safety' in content_sections:
            toc_sections.append("Agent Skillsの安全性とリスク")
        if 'prerequisites' in content_sections:
            toc_sections.append("Agent Skillsを利用・開発するための前提ソフトウェア")
        if 'skills' in content_sections:
            toc_sections.append("スキル一覧")
        if 'conclusion' in content_sections:
            toc_sections.append("まとめ")
        
        if toc_sections:
            toc = self.generate_table_of_contents(toc_sections)
            article_parts.append(toc)
            article_parts.append("")  # 空行
        
        # はじめに
        if 'introduction' in content_sections:
            article_parts.append(content_sections['introduction'])
            article_parts.append("")  # 空行
        
        # Agent Skillsとは
        if 'what_is_agent_skills' in content_sections:
            article_parts.append(content_sections['what_is_agent_skills'])
            article_parts.append("")  # 空行

        # Agent Skillsの歴史と公式ロードマップ
        if 'history' in content_sections:
            article_parts.append(content_sections['history'])
            article_parts.append("")  # 空行

        # 安全性とリスク
        if 'safety' in content_sections:
            article_parts.append(content_sections['safety'])
            article_parts.append("")  # 空行
        
        # 前提ソフトウェア
        if 'prerequisites' in content_sections:
            article_parts.append(content_sections['prerequisites'])
            article_parts.append("")  # 空行
        
        # スキル一覧
        if 'skills' in content_sections:
            article_parts.append(content_sections['skills'])
            article_parts.append("")  # 空行
        
        # まとめ
        if 'conclusion' in content_sections:
            article_parts.append(content_sections['conclusion'])
            article_parts.append("")  # 空行
        
        # 記事全体を結合
        article = "\n".join(article_parts)
        
        return article
    
    def generate_table_of_contents(self, sections: List[str]) -> str:
        """
        目次を自動生成
        
        Args:
            sections: セクション名のリスト
            
        Returns:
            目次のMarkdownテキスト
        """
        toc_parts = ["## 目次", ""]
        
        for i, section in enumerate(sections, start=1):
            toc_parts.append(f"{i}. [{section}](#{self._section_to_anchor(section)})")
        
        return "\n".join(toc_parts)
    
    def _section_to_anchor(self, section: str) -> str:
        """
        セクション名をアンカーリンクに変換
        
        Qiitaでは、見出しから自動的にアンカーが生成されます。
        日本語の見出しは、そのままURLエンコードされた形式になります。
        
        Args:
            section: セクション名
            
        Returns:
            アンカーリンク（簡易版）
        """
        # Qiitaでは日本語見出しがそのままアンカーになるため、
        # 簡易的に小文字化とスペース除去を行う
        anchor = section.lower().replace(" ", "-")
        return anchor
    
    def format_heading(self, text: str, level: int) -> str:
        """
        見出しを初学者向けの表現に整形
        
        Args:
            text: 見出しテキスト
            level: 見出しレベル（1-6）
            
        Returns:
            Markdown形式の見出し
        """
        if level < 1 or level > 6:
            raise ValueError(f"見出しレベルは1-6の範囲である必要があります: {level}")
        
        heading_prefix = "#" * level
        return f"{heading_prefix} {text}"
    
    def format_code_block(self, code: str, language: str = "") -> str:
        """
        コードブロックを整形
        
        Args:
            code: コード内容
            language: プログラミング言語（オプション）
            
        Returns:
            Markdown形式のコードブロック
        """
        if language:
            return f"```{language}\n{code}\n```"
        else:
            return f"```\n{code}\n```"
    
    def format_list(self, items: List[str], ordered: bool = False) -> str:
        """
        リストを整形
        
        Args:
            items: リスト項目のリスト
            ordered: True の場合は番号付きリスト、False の場合は箇条書き
            
        Returns:
            Markdown形式のリスト
        """
        if not items:
            return ""
        
        list_parts = []
        
        if ordered:
            # 番号付きリスト
            for i, item in enumerate(items, start=1):
                list_parts.append(f"{i}. {item}")
        else:
            # 箇条書き
            for item in items:
                list_parts.append(f"- {item}")
        
        return "\n".join(list_parts)
