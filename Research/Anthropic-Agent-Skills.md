Agent Skillsの概念提唱日と公開日について調べます。

# Anthropic Agent Skills 関連の日付まとめ

ご質問の「後悔した」は文脈上「公開した」と解釈してまとめます。

## 1. Agent Skills の概念提唱日
- **2025年10月16日（米国時間）** — Anthropic が「Agent Skills」を Claude 向け機能として初めて発表しました。
- ファイルシステムとコード実行ツールを持つエージェントが必要に応じて指示・スクリプト・リソースを動的に読み込む「Progressive Disclosure（段階的開示）」を中核設計とする概念です。

## 2. Anthropic 推奨 Agent Skills の公開日
Anthropic 自身による公式の推奨スキルは複数のタイミングで公開されています。

- **2025年10月16日前後** — 公式 GitHub リポジトリ [`anthropics/skills`](https://github.com/anthropics/skills) が公開され、Anthropic 製の推奨スキル群（`docx` / `xlsx` / `pdf` / `pptx` / `skill-creator` / `mcp-builder` / `frontend-design` など）が利用可能になりました。これらのうち4つのドキュメント系スキル（DOCX / XLSX / PDF / PPTX）は Claude.ai のドキュメント作成機能の基盤として組み込まれています。
- **2025年12月18日** — Agent Skills を **オープン標準（open standard）** として公開し、同時に Claude のコネクタ・ディレクトリ（claude.com/connectors）で Atlassian、Canva、Cloudflare、Figma、Notion、Ramp、Sentry、Zapier、Stripe、Vercel などのパートナー製スキルを提供開始しました。
- **2026年4月7日時点** — `anthropics/skills` 公式リポジトリには Anthropic 提供の 17 個のトップレベル Skills が公開されています。

## 情報ソース

- [Equipping agents for the real world with Agent Skills — Anthropic Engineering Blog](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Agent Skills — Claude API Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [anthropics/skills（公式 GitHub リポジトリ）](https://github.com/anthropics/skills)
- [Anthropic launches enterprise 'Agent Skills' and opens the standard — VentureBeat](https://venturebeat.com/technology/anthropic-launches-enterprise-agent-skills-and-opens-the-standard)
- [Agent Skills: Anthropic's Next Bid to Define AI Standards — The New Stack](https://thenewstack.io/agent-skills-anthropics-next-bid-to-define-ai-standards/)
- [Anthropic publishes Agent Skills as an open standard — The Decoder](https://the-decoder.com/anthropic-publishes-agent-skills-as-an-open-standard-for-ai-platforms/)
- [Anthropic makes agent Skills an open standard — SiliconANGLE（2025/12/18）](https://siliconangle.com/2025/12/18/anthropic-makes-agent-skills-open-standard/)
- [Anthropic Official Skills Repository: 17 Skills Walkthrough — claudecn.com](https://claudecn.com/en/blog/claude-official-skills-walkthrough/)

> 注：「Agent Skills」自体は段階的に展開されており、（1）2025年10月の初公開（Claude 向け機能 + 公式スキルリポジトリ）と、（2）2025年12月18日のオープン標準化＋パートナー製スキル提供開始、の2つの大きな節目があります。