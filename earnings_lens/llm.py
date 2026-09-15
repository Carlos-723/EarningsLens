from __future__ import annotations

import os
from textwrap import shorten

from dotenv import load_dotenv

from .metrics import Metric
from .thesis import InvestmentThesis


def _metrics_text(metrics: list[Metric]) -> str:
    if not metrics:
        return "未提取到核心财务指标。"
    lines = []
    for item in metrics:
        change = []
        if item.yoy:
            change.append(f"同比 {item.yoy}")
        if item.qoq:
            change.append(f"环比 {item.qoq}")
        suffix = f"（{'; '.join(change)}）" if change else ""
        lines.append(f"- {item.name}: {item.value}{item.unit}{suffix}")
    return "\n".join(lines)


def _list_text(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _thesis_text(thesis: InvestmentThesis) -> str:
    return f"""
初步观点：{thesis.stance}（评分 {thesis.score}）
一句话判断：{thesis.one_line_view}
看多因素：
{_list_text(thesis.bullish_points)}
看空因素：
{_list_text(thesis.bearish_points)}
后续验证问题：
{_list_text(thesis.follow_up_questions)}
""".strip()


def build_prompt(text: str, metrics: list[Metric], risks: list[str], focus: list[str], thesis: InvestmentThesis) -> str:
    return f"""
你是一名面向本科生投资研究实习场景的 AI 财报分析助手。请基于给定公告内容输出中文结构化分析。

已提取指标：
{_metrics_text(metrics)}

规则识别风险点：{", ".join(risks)}
规则识别管理层关注点：{", ".join(focus)}

规则生成的股票研究观察：
{_thesis_text(thesis)}

公告节选：
{shorten(text, width=2500, placeholder="...")}

请输出：
1. 初步观点：偏正面 / 中性观察 / 偏谨慎，并说明依据
2. 看多因素：3条以内
3. 看空因素：3条以内
4. 后续跟踪：3条以内，写清楚下一步应该查什么数据
5. 200字以内投研点评：要有判断，但不要给买入、卖出、目标价，也不要捏造未出现的数据
""".strip()


def mock_completion(metrics: list[Metric], risks: list[str], focus: list[str], thesis: InvestmentThesis) -> str:
    metric_summary = _metrics_text(metrics)
    return f"""
### 初步观点：{thesis.stance}
{thesis.one_line_view}

### 核心数据
{metric_summary}

### 看多因素
{_list_text(thesis.bullish_points[:3])}

### 看空因素
{_list_text(thesis.bearish_points[:3])}

### 管理层关注点
{chr(10).join(f"- {item}" for item in focus[:3])}

### 后续跟踪
{_list_text(thesis.follow_up_questions[:3])}

### 200字投研点评
当前结论为“{thesis.stance}”。判断重点不只看收入或利润单点变化，而是看增长、盈利质量、现金流和风险提示是否互相印证。若正面信号能在后续季度继续体现，同时估值没有过度透支，研究价值会提高；若利润、毛利率或现金流继续走弱，则应降低预期。以上仅用于股票研究和信息整理，不构成买卖建议。
""".strip()


def generate_analysis(text: str, metrics: list[Metric], risks: list[str], focus: list[str], thesis: InvestmentThesis) -> str:
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    api_key = os.getenv("OPENAI_API_KEY")

    if provider != "openai" or not api_key:
        return mock_completion(metrics, risks, focus, thesis)

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": "你是谨慎、结构化的中文财报和公告分析助手。"},
            {"role": "user", "content": build_prompt(text, metrics, risks, focus, thesis)},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""
