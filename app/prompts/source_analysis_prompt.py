from __future__ import annotations


JSON_SCHEMA_GUIDE = """
你必须只返回合法 JSON。
不要返回 Markdown。
不要使用 ```json 代码块。
不要输出解释文字。
不要输出注释。
所有字段必须符合指定 Schema。
如果信息不足，请设置 needs_user_review = true，并在 missing_information 中说明。

JSON Schema:
{
  "source_summary": "原始材料摘要",
  "domain": "AI",
  "knowledge_type": "方法型",
  "priority": "high",
  "needs_user_review": false,
  "missing_information": [],
  "review_method": "框架复述",
  "notes": [
    {
      "title": "标题",
      "domain": "AI",
      "knowledge_type": "方法型",
      "priority": "high",
      "review_method": "框架复述",
      "tags": ["AI", "RAG"],
      "one_sentence_summary": "一句话总结",
      "core_content": "结构化正文",
      "use_cases": ["适用场景"],
      "reusable_expressions": ["可复用表达"],
      "active_recall_questions": ["主动回忆问题"],
      "anki_required": true,
      "anki_cards": [
        {
          "front": "问题",
          "back": "答案",
          "tags": ["AI", "方法型"]
        }
      ],
      "related_notes": []
    }
  ]
}
"""


def build_source_analysis_prompt(source_markdown: str, domains: list[str], max_notes: int, max_cards: int) -> str:
    return f"""
你是一个知识管理系统架构师，目标是把原始材料加工成可长期复习、主动回忆、工作输出和表达调用的 Obsidian 知识资产。

领域只能从这些值中选择：{", ".join(domains)}
knowledge_type 只能从这些值中选择：事实型、概念型、方法型、案例型、表达型、输出型。
priority 只能是 high、medium、low。
review_method 只能从这些值中选择：主动回忆、框架复述、案例复述、话术复述、中英互译、时间线复述、因果链复述、输出任务。

生成要求：
1. 生成 1-{max_notes} 篇 Note。
2. 每篇 Note 最多生成 {max_cards} 张 Anki 卡。
3. 卡片必须服务真实调用场景，避免“总结全文”这类大问题。
4. 每张卡只考一个知识点，答案保持简洁，5-20 秒内可复习。
5. 如果材料更适合输出任务而不是记忆卡，可以减少卡片数量。

{JSON_SCHEMA_GUIDE}

原始 Source Markdown:
{source_markdown}
"""
