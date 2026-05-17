"""
図表生成モジュール

Qiita記事に埋め込む図を生成します。

サポートする図の形式:
- **Mermaid**: フローチャート・処理シーケンス・カテゴリツリーなど
  Markdownコードブロック（```mermaid```）として埋め込む。Qiitaはネイティブサポート。
- **PlantUML**: 構造図・コンポーネント図など
  Markdownコードブロック（```plantuml```）として埋め込む。Qiitaはネイティブサポート。
- **SVG**: draw.io でも編集可能な標準SVGファイル。
  output/images/ にファイル保存し、Markdownでは ``![alt](images/xxx.svg)`` で参照する。

各ヘルパーは「Markdownに埋め込む文字列」を返します。SVGの場合は
副作用として ``images_dir`` 配下にファイルを書き出します。
"""

from __future__ import annotations

import logging
import re
from html import escape
from pathlib import Path
from typing import List, Optional, Tuple


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Mermaid helpers
# ------------------------------------------------------------------


def mermaid_block(code: str, caption: Optional[str] = None) -> str:
    """
    Mermaidコードブロックを生成する

    Args:
        code: Mermaid記法のコード本文
        caption: 図の下に添える短いキャプション（任意）

    Returns:
        Markdownに埋め込めるMermaidコードブロック文字列
    """
    body = code.strip()
    parts = ["```mermaid", body, "```"]
    if caption:
        parts.append("")
        parts.append(f"*図: {caption}*")
    parts.append("")
    return "\n".join(parts)


def plantuml_block(code: str, caption: Optional[str] = None) -> str:
    """
    PlantUMLコードブロックを生成する

    Args:
        code: PlantUML記法のコード本文（``@startuml``〜``@enduml``で囲まれていなくてもよい）
        caption: 図の下に添える短いキャプション（任意）

    Returns:
        Markdownに埋め込めるPlantUMLコードブロック文字列
    """
    body = code.strip()
    if not body.startswith("@startuml"):
        body = "@startuml\n" + body
    if not body.endswith("@enduml"):
        body = body + "\n@enduml"

    parts = ["```plantuml", body, "```"]
    if caption:
        parts.append("")
        parts.append(f"*図: {caption}*")
    parts.append("")
    return "\n".join(parts)


# ------------------------------------------------------------------
# SVG helpers
# ------------------------------------------------------------------


def _slugify_filename(name: str) -> str:
    """ファイル名として安全な英数字スラッグに変換する"""
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-").lower()
    return slug or "diagram"


def save_svg(
    svg_content: str,
    images_dir: Path,
    filename: str,
    images_url_prefix: str = "images",
    alt_text: str = "",
    caption: Optional[str] = None,
) -> str:
    """
    SVG画像をファイルに保存し、Markdownの画像参照を返す

    Args:
        svg_content: 完全なSVG XML文字列
        images_dir: 保存先ディレクトリ（``output/images/`` など）
        filename: 拡張子なしのファイル名
        images_url_prefix: Markdownから参照する際のURLプレフィックス
        alt_text: 代替テキスト（画像が表示されない場合の説明文）
        caption: 画像の下に添えるキャプション（任意）

    Returns:
        Markdownの画像参照文字列。例: ``![alt](images/foo.svg)``
    """
    images_dir.mkdir(parents=True, exist_ok=True)
    safe_name = _slugify_filename(filename)
    if not safe_name.endswith(".svg"):
        safe_name = safe_name + ".svg"
    file_path = images_dir / safe_name
    file_path.write_text(svg_content, encoding="utf-8")
    logger.debug("SVG画像を保存しました: %s", file_path)

    url = f"{images_url_prefix.rstrip('/')}/{safe_name}"
    parts = [f"![{alt_text or filename}]({url})"]
    if caption:
        parts.append("")
        parts.append(f"*図: {caption}*")
    parts.append("")
    return "\n".join(parts)


# ------------------------------------------------------------------
# Pre-built diagram constructors for the article
# ------------------------------------------------------------------


def progressive_disclosure_mermaid() -> str:
    """段階的開示の3レベル読み込みをMermaidで表す"""
    code = """flowchart TD
    Q[\"ユーザーの依頼\"] --> L1
    subgraph L1[\"レベル1: メタデータ（常時ロード・約100語）\"]
        N1[\"スキル名 + description\"]
    end
    L1 -->|\"スキルがマッチ\"| L2
    subgraph L2[\"レベル2: SKILL.md 本文（オンデマンド・~500行）\"]
        N2[\"指示・ガイドライン\\n使用例\"]
    end
    L2 -->|\"必要に応じて\"| L3
    subgraph L3[\"レベル3: バンドルリソース（必要時のみ・無制限）\"]
        N3a[\"scripts/\"]
        N3b[\"references/\"]
        N3c[\"assets/\"]
        N3d[\"templates/\"]
    end
    classDef load fill:#fff7d6,stroke:#c9a227;
    classDef ond fill:#e6f4ff,stroke:#2c7be5;
    classDef opt fill:#eef9ee,stroke:#39a05c;
    class L1 load;
    class L2 ond;
    class L3 opt;
"""
    return mermaid_block(
        code,
        caption="Agent Skillsの段階的開示（Progressive Disclosure）。"
        "AIエージェントは必要な情報だけを段階的に読み込みます。",
    )


def skill_structure_mermaid() -> str:
    """スキルディレクトリ構造をMermaidツリーで表す"""
    code = """flowchart LR
    Skill[\"my-skill/\"] --> SM[\"SKILL.md（必須）\\nYAMLフロントマター + 本文\"]
    Skill --> S[\"scripts/（任意）\\n決定論的タスク用\"]
    Skill --> R[\"references/（任意）\\n詳細ドキュメント\"]
    Skill --> A[\"assets/（任意）\\nテンプレ・フォント・画像\"]
    Skill --> T[\"templates/（任意）\\nファイルテンプレート\"]
    Skill --> L[\"LICENSE.txt\"]
    classDef must fill:#ffe4e1,stroke:#c0392b;
    classDef opt  fill:#eef9ee,stroke:#39a05c;
    class SM must;
    class S,R,A,T opt;
"""
    return mermaid_block(
        code,
        caption="スキルのディレクトリ構造。SKILL.mdのみ必須で、"
        "他のディレクトリはオプションです。",
    )


def safety_comparison_svg(
    images_dir: Path, images_url_prefix: str = "images"
) -> str:
    """
    3種類のスキルの安全性を比較するSVG図（横幅を厳密に揃える）

    Mermaidは内部テキスト長で幅が決まりレンダラー間で揺れるため、
    幅を厳密に揃える必要があるこの図だけはSVGで描画する。
    """
    title = "Agent Skillsの提供元による信頼性比較"
    # 3行 × 3列のグリッド構成、すべて同じ幅
    card_w = 820
    card_h = 110
    inner_w = 360
    inner_h = 50
    inner_y = 35
    margin_x = 30
    gap_y = 30
    canvas_h = 30 + (card_h + gap_y) * 3
    svg = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 {card_w + 60} {canvas_h}\" width=\"{card_w + 60}\" height=\"{canvas_h}\" font-family=\"Helvetica, Arial, sans-serif\">
  <title>{escape(title)}</title>
"""

    rows = [
        {
            "title": "公式 Agent Skills  ★★★★★",
            "left": "Anthropic / OpenAI / Google",
            "right": "監査済み・継続メンテ",
            "fill": "#eef9ee",
            "stroke": "#39a05c",
            "title_color": "#1f6b3a",
        },
        {
            "title": "ベンダー提供 Agent Skills  ★★★★",
            "left": "Microsoft / AWS など",
            "right": "製品公式・依存に注意",
            "fill": "#fff7d6",
            "stroke": "#c9a227",
            "title_color": "#7a5a00",
        },
        {
            "title": "野良 Agent Skills  ★",
            "left": "個人・非公式",
            "right": "監査なし・要検証",
            "fill": "#ffe4e1",
            "stroke": "#c0392b",
            "title_color": "#7a1f1f",
        },
    ]

    for i, row in enumerate(rows):
        y = 20 + i * (card_h + gap_y)
        title_y = y + 22
        inner_left_x = margin_x + 30
        inner_right_x = margin_x + 30 + inner_w + 40
        ty_y = y + inner_y + (inner_h / 2) + 4
        svg += f"""  <g>
    <rect x=\"{margin_x}\" y=\"{y}\" width=\"{card_w}\" height=\"{card_h}\" rx=\"12\" ry=\"12\" fill=\"{row['fill']}\" stroke=\"{row['stroke']}\" stroke-width=\"2\"/>
    <text x=\"{margin_x + card_w / 2}\" y=\"{title_y}\" font-size=\"15\" font-weight=\"bold\" text-anchor=\"middle\" fill=\"{row['title_color']}\">{escape(row['title'])}</text>
    <rect x=\"{inner_left_x}\" y=\"{y + inner_y}\" width=\"{inner_w}\" height=\"{inner_h}\" rx=\"8\" ry=\"8\" fill=\"#ffffff\" stroke=\"{row['stroke']}\"/>
    <text x=\"{inner_left_x + inner_w / 2}\" y=\"{ty_y}\" font-size=\"14\" text-anchor=\"middle\" fill=\"#222222\">{escape(row['left'])}</text>
    <rect x=\"{inner_right_x}\" y=\"{y + inner_y}\" width=\"{inner_w}\" height=\"{inner_h}\" rx=\"8\" ry=\"8\" fill=\"#ffffff\" stroke=\"{row['stroke']}\"/>
    <text x=\"{inner_right_x + inner_w / 2}\" y=\"{ty_y}\" font-size=\"14\" text-anchor=\"middle\" fill=\"#222222\">{escape(row['right'])}</text>
  </g>
"""
    svg += "</svg>\n"

    return save_svg(
        svg_content=svg,
        images_dir=images_dir,
        filename="agent-skills-safety-comparison",
        images_url_prefix=images_url_prefix,
        alt_text=title,
        caption="Agent Skillsの提供元による信頼性の比較。"
        "本記事で扱うAnthropic公式は最も推奨度が高い区分です。",
    )


def safety_comparison_mermaid() -> str:
    """3種類のスキルの安全性を可視化（互換のため残置、SVG版を推奨）"""
    code = """flowchart LR
    subgraph Off["公式 Agent Skills ★★★★★"]
        O1["Anthropic / OpenAI / Google"]
        O2["監査済み・継続メンテ"]
    end
    subgraph Vend["ベンダー提供 Agent Skills ★★★★"]
        V1["Microsoft / AWS など"]
        V2["製品公式・依存に注意"]
    end
    subgraph Wild["野良 Agent Skills ★"]
        W1["個人・非公式"]
        W2["監査なし・要検証"]
    end
    classDef ok   fill:#eef9ee,stroke:#39a05c;
    classDef warn fill:#fff7d6,stroke:#c9a227;
    classDef bad  fill:#ffe4e1,stroke:#c0392b;
    class Off ok;
    class Vend warn;
    class Wild bad;
"""
    return mermaid_block(
        code,
        caption="Agent Skillsの提供元による信頼性の比較。"
        "本記事で扱うAnthropic公式は最も推奨度が高い区分です。",
    )


def category_tree_mermaid(
    categorized_skills: dict[str, List[str]]
) -> str:
    """
    カテゴリ→スキルのMermaidツリー（非推奨）

    スキル数が多いと縦に大きく伸びて読みにくいため、現在は
    ``category_table()`` で生成する表組みを推奨します。互換のため残しています。
    """
    lines = ["flowchart LR", '    Root["Anthropic公式 Agent Skills"]']
    for cat_idx, (category, skills) in enumerate(
        categorized_skills.items(), start=1
    ):
        cat_id = f"C{cat_idx}"
        lines.append(f'    Root --> {cat_id}["{category}"]')
        for sk_idx, skill_name in enumerate(skills, start=1):
            sk_id = f"{cat_id}S{sk_idx}"
            lines.append(f'    {cat_id} --> {sk_id}["{skill_name}"]')
    code = "\n".join(lines)
    return mermaid_block(
        code,
        caption="本記事で扱うAnthropic公式Agent Skillsのカテゴリ分類。",
    )


# ------------------------------------------------------------------
# Markdown table helpers
# ------------------------------------------------------------------


def _escape_table_cell(value: str) -> str:
    """表セルに入れる際にパイプと改行をエスケープする"""
    if value is None:
        return ""
    s = str(value)
    s = s.replace("|", "\\|")
    s = s.replace("\n", "<br>")
    return s


def markdown_table(
    headers: List[str],
    rows: List[List[str]],
    caption: Optional[str] = None,
) -> str:
    """
    Markdownの表を生成する

    Args:
        headers: 列見出しのリスト
        rows: 行のリスト（各行は列数と同じ長さのリスト）
        caption: 表の下に添える短いキャプション（任意）

    Returns:
        Markdownに埋め込める表組み文字列
    """
    if not headers:
        return ""

    parts: List[str] = []
    parts.append("| " + " | ".join(_escape_table_cell(h) for h in headers) + " |")
    parts.append("|" + "|".join(["---"] * len(headers)) + "|")
    for row in rows:
        # 列数が足りない場合は空セルで補う
        cells = list(row) + [""] * (len(headers) - len(row))
        cells = cells[: len(headers)]
        parts.append(
            "| "
            + " | ".join(_escape_table_cell(c) for c in cells)
            + " |"
        )
    if caption:
        parts.append("")
        parts.append(f"*表: {caption}*")
    parts.append("")
    return "\n".join(parts)


def category_table(
    categorized_skills: dict[str, List[str]]
) -> str:
    """
    カテゴリ→スキル一覧を表で表す

    各行が1カテゴリ。スキル名はカンマ区切りでまとめる。
    """
    rows: List[List[str]] = []
    for category, skills in categorized_skills.items():
        rows.append([
            category,
            str(len(skills)),
            ", ".join(skills) if skills else "—",
        ])
    return markdown_table(
        headers=["カテゴリ", "スキル数", "含まれるスキル"],
        rows=rows,
        caption="本記事で扱うAnthropic公式Agent Skillsのカテゴリ別一覧。",
    )


def usage_sequence_mermaid() -> str:
    """ユーザー依頼→Claude→スキル選択→実行のシーケンス図"""
    code = """sequenceDiagram
    participant User as ユーザー
    participant Claude as AIエージェント\\n(Claude)
    participant Meta as Lv1 メタデータ
    participant Skill as Lv2 SKILL.md\\n本文
    participant Bundle as Lv3 バンドル\\nリソース

    User->>Claude: 「Word文書を作成して」
    Claude->>Meta: 全スキルの説明文を参照
    Meta-->>Claude: docx スキルを選択
    Claude->>Skill: docx/SKILL.md を読み込み
    Skill-->>Claude: 指示・ガイドラインを取得
    Claude->>Bundle: scripts/templates/ を必要に応じて取得
    Bundle-->>Claude: テンプレート・スクリプト
    Claude->>User: 完成した .docx ファイルを返す
"""
    return mermaid_block(
        code,
        caption="ユーザーの依頼からAgent Skillが選ばれて実行されるまでの流れ。",
    )


def system_overview_svg(
    images_dir: Path, images_url_prefix: str = "images"
) -> str:
    """
    本記事の対象範囲を1枚で示す概念図（SVG）。

    draw.io でも開ける標準 SVG として ``output/images/`` に保存します。
    """
    # シンプルなボックス＆矢印で「ユーザー → Claude → Skills → 出力」を表す
    title = "Anthropic 公式 Agent Skills の概念図"
    svg = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 900 360\" width=\"900\" height=\"360\" font-family=\"Helvetica, Arial, sans-serif\">
  <title>{escape(title)}</title>
  <defs>
    <marker id=\"arrow\" viewBox=\"0 0 10 10\" refX=\"9\" refY=\"5\" markerWidth=\"8\" markerHeight=\"8\" orient=\"auto-start-reverse\">
      <path d=\"M 0 0 L 10 5 L 0 10 z\" fill=\"#374151\"/>
    </marker>
  </defs>
  <rect x=\"0\" y=\"0\" width=\"900\" height=\"360\" fill=\"#fafafa\" stroke=\"#e5e7eb\"/>

  <!-- User -->
  <g>
    <rect x=\"30\" y=\"140\" width=\"140\" height=\"70\" rx=\"10\" ry=\"10\" fill=\"#e6f4ff\" stroke=\"#2c7be5\"/>
    <text x=\"100\" y=\"180\" font-size=\"16\" text-anchor=\"middle\" fill=\"#1f4f8f\">ユーザー</text>
  </g>

  <!-- Claude -->
  <g>
    <rect x=\"230\" y=\"110\" width=\"180\" height=\"130\" rx=\"12\" ry=\"12\" fill=\"#fff7d6\" stroke=\"#c9a227\"/>
    <text x=\"320\" y=\"150\" font-size=\"16\" text-anchor=\"middle\" fill=\"#7a5a00\">Claude</text>
    <text x=\"320\" y=\"175\" font-size=\"13\" text-anchor=\"middle\" fill=\"#7a5a00\">（AIエージェント）</text>
    <text x=\"320\" y=\"205\" font-size=\"12\" text-anchor=\"middle\" fill=\"#7a5a00\">スキルを動的に読み込む</text>
  </g>

  <!-- Skills repo -->
  <g>
    <rect x=\"480\" y=\"40\" width=\"380\" height=\"280\" rx=\"12\" ry=\"12\" fill=\"#eef9ee\" stroke=\"#39a05c\"/>
    <text x=\"670\" y=\"70\" font-size=\"15\" text-anchor=\"middle\" fill=\"#1f6b3a\">Anthropic 公式 Agent Skills（17種類）</text>

    <!-- Category boxes -->
    <g>
      <rect x=\"500\" y=\"90\" width=\"170\" height=\"60\" rx=\"8\" fill=\"#ffffff\" stroke=\"#39a05c\"/>
      <text x=\"585\" y=\"115\" font-size=\"13\" text-anchor=\"middle\" fill=\"#1f6b3a\">クリエイティブ&amp;</text>
      <text x=\"585\" y=\"132\" font-size=\"13\" text-anchor=\"middle\" fill=\"#1f6b3a\">デザイン</text>
    </g>
    <g>
      <rect x=\"680\" y=\"90\" width=\"170\" height=\"60\" rx=\"8\" fill=\"#ffffff\" stroke=\"#39a05c\"/>
      <text x=\"765\" y=\"125\" font-size=\"13\" text-anchor=\"middle\" fill=\"#1f6b3a\">開発&amp;技術</text>
    </g>
    <g>
      <rect x=\"500\" y=\"160\" width=\"170\" height=\"60\" rx=\"8\" fill=\"#ffffff\" stroke=\"#39a05c\"/>
      <text x=\"585\" y=\"195\" font-size=\"13\" text-anchor=\"middle\" fill=\"#1f6b3a\">ドキュメント処理</text>
    </g>
    <g>
      <rect x=\"680\" y=\"160\" width=\"170\" height=\"60\" rx=\"8\" fill=\"#ffffff\" stroke=\"#39a05c\"/>
      <text x=\"765\" y=\"185\" font-size=\"13\" text-anchor=\"middle\" fill=\"#1f6b3a\">エンタープライズ&amp;</text>
      <text x=\"765\" y=\"203\" font-size=\"13\" text-anchor=\"middle\" fill=\"#1f6b3a\">コミュニケーション</text>
    </g>
    <g>
      <rect x=\"590\" y=\"230\" width=\"170\" height=\"60\" rx=\"8\" fill=\"#ffffff\" stroke=\"#39a05c\"/>
      <text x=\"675\" y=\"265\" font-size=\"13\" text-anchor=\"middle\" fill=\"#1f6b3a\">メタスキル</text>
    </g>
  </g>

  <!-- Arrows -->
  <line x1=\"170\" y1=\"175\" x2=\"230\" y2=\"175\" stroke=\"#374151\" stroke-width=\"2\" marker-end=\"url(#arrow)\"/>
  <line x1=\"410\" y1=\"175\" x2=\"480\" y2=\"175\" stroke=\"#374151\" stroke-width=\"2\" marker-end=\"url(#arrow)\"/>
  <text x=\"195\" y=\"165\" font-size=\"11\" text-anchor=\"middle\" fill=\"#374151\">依頼</text>
  <text x=\"445\" y=\"165\" font-size=\"11\" text-anchor=\"middle\" fill=\"#374151\">読込</text>
</svg>
"""
    return save_svg(
        svg_content=svg,
        images_dir=images_dir,
        filename="agent-skills-overview",
        images_url_prefix=images_url_prefix,
        alt_text=title,
        caption="ユーザーの依頼を受けて Claude が必要な Agent Skill を読み込み、"
        "出力に反映する全体像。",
    )


def safety_decision_plantuml() -> str:
    """企業内利用の安全性判断フローをPlantUMLで描く"""
    code = """skinparam shadowing false
skinparam ArrowColor #374151
skinparam DefaultFontName Helvetica
skinparam ActivityBackgroundColor<<official>> #DDF6E0
skinparam ActivityBorderColor<<official>>     #1F6B3A
skinparam ActivityBackgroundColor<<vendor>>   #FFF7D6
skinparam ActivityBorderColor<<vendor>>       #C9A227
skinparam ActivityBackgroundColor<<wild>>     #FFE4E1
skinparam ActivityBorderColor<<wild>>         #C0392B

start
:Agent Skill を導入したい;
if (提供元は誰か?) then (Anthropic/OpenAI/Google など公式)
  :公式 Agent Skill\\n（推奨 ★★★★★）<<official>>;
  :ライセンス・データ取扱を社内規程と照合;
elseif (Microsoft/AWS など) then (プロダクトベンダー)
  :ベンダー提供 Agent Skill\\n（推奨 ★★★★）<<vendor>>;
  :製品依存・更新ポリシーを確認;
else (個人/非公式)
  :野良 Agent Skill\\n（要検証 ★）<<wild>>;
  :ソースを必ずレビュー\\n＋脆弱性スキャン;
endif
:情報セキュリティ部門の承認;
stop
"""
    return plantuml_block(
        code,
        caption="企業内でAgent Skillを採用する際の安全性判断フロー。",
    )
