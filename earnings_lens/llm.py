from __future__ import annotations

import os
from textwrap import shorten

from dotenv import load_dotenv

from .metrics import Metric


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


def build_prompt(text: str, metrics: list[Metric], risks: list[str], focus: list[str]) -> str:
    return f"""
你是一名面向本科生投资研究实习场景的 AI 财报分析助手。请基于给定公告内容输出中文结构化分析。

已提取指标：
{_metrics_text(metrics)}

规则识别风险点：{", ".join(risks)}
规则识别管理层关注点：{", ".join(focus)}

公告节选：
{shorten(text, width=2500, placeholder="...")}

请输出：
1. 结构化摘要：3条以内
2. 风险点：3条以内
3. 管理层关注点：3条以内
4. 200字以内投研点评：不要捏造未出现的数据
""".strip()


def mock_completion(metrics: list[Metric], risks: list[str], focus: list[str]) -> str:
    metric_summary = _metrics_text(metrics)
    return f"""
### 结构化摘要
- 公司公告中可识别的核心指标如下：
{metric_summary}
- 从关键词看，文本涉及经营表现、盈利能力和后续业务安排，适合作为进一步投研拆解的入口。
- 当前分析来自规则抽取与示例模型，不构成投资建议。

### 风险点
{chr(10).join(f"- {risk}" for risk in risks[:3])}

### 管理层关注点
{chr(10).join(f"- {item}" for item in focus[:3])}

### 200字投研点评
从已披露信息看，公司经营变化需要同时观察收入增速、利润质量和现金流匹配度。若收入增长但利润或经营现金流走弱，说明增长质量仍需验证；若管理层强调研发、客户拓展或降本增效，则后续应跟踪相关投入能否转化为订单、毛利率改善和费用率下降。建议继续补充历史财报与同行公司数据，形成更完整的横向和纵向比较。
""".strip()


def generate_analysis(text: str, metrics: list[Metric], risks: list[str], focus: list[str]) -> str:
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    api_key = os.getenv("OPENAI_API_KEY")

    if provider != "openai" or not api_key:
        return mock_completion(metrics, risks, focus)

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": "你是谨慎、结构化的中文财报和公告分析助手。"},
            {"role": "user", "content": build_prompt(text, metrics, risks, focus)},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""

