from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Metric:
    name: str
    value: str
    unit: str
    yoy: str | None = None
    qoq: str | None = None
    source: str | None = None


METRIC_ALIASES = {
    "revenue": ["营业收入", "营收", "收入", "revenue"],
    "net_profit": ["归母净利润", "净利润", "net profit"],
    "gross_margin": ["毛利率", "gross margin"],
    "operating_cash_flow": ["经营活动现金流量净额", "经营性现金流", "operating cash flow"],
    "eps": ["基本每股收益", "每股收益", "eps"],
}

DISPLAY_NAMES = {
    "revenue": "营业收入",
    "net_profit": "归母净利润",
    "gross_margin": "毛利率",
    "operating_cash_flow": "经营活动现金流量净额",
    "eps": "基本每股收益",
}

VALUE_PATTERN = re.compile(
    r"(?P<value>-?\d+(?:,\d{3})*(?:\.\d+)?)\s*(?P<unit>亿元|万元|元|%|百分比|million|billion|bn|m)?",
    flags=re.IGNORECASE,
)
YOY_PATTERN = re.compile(r"(同比|year[-\s]?over[-\s]?year|YoY)[^\d\-+]{0,8}(?P<value>[+\-]?\d+(?:\.\d+)?)\s*%?", re.IGNORECASE)
QOQ_PATTERN = re.compile(r"(环比|quarter[-\s]?over[-\s]?quarter|QoQ)[^\d\-+]{0,8}(?P<value>[+\-]?\d+(?:\.\d+)?)\s*%?", re.IGNORECASE)


def normalize_text(text: str) -> str:
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。；;!?])\s*|\n+", normalize_text(text))
    return [part.strip() for part in parts if part.strip()]


def _find_value_after_alias(sentence: str, alias: str) -> tuple[str, str] | None:
    idx = sentence.lower().find(alias.lower())
    if idx < 0:
        return None
    snippet = sentence[idx : idx + 80]
    match = VALUE_PATTERN.search(snippet)
    if not match:
        return None
    return match.group("value"), match.group("unit") or ""


def _find_change(pattern: re.Pattern[str], sentence: str) -> str | None:
    match = pattern.search(sentence)
    if not match:
        return None
    raw = match.group("value")
    if raw.startswith(("+", "-")):
        return f"{raw}%"
    return f"{raw}%"


def extract_metrics(text: str) -> list[Metric]:
    """Extract common financial indicators with simple explainable rules."""
    sentences = split_sentences(text)
    results: dict[str, Metric] = {}

    for sentence in sentences:
        lower = sentence.lower()
        for key, aliases in METRIC_ALIASES.items():
            if key in results:
                continue
            for alias in aliases:
                if alias.lower() not in lower:
                    continue
                value_unit = _find_value_after_alias(sentence, alias)
                if not value_unit:
                    continue
                value, unit = value_unit
                results[key] = Metric(
                    name=DISPLAY_NAMES[key],
                    value=value,
                    unit=unit,
                    yoy=_find_change(YOY_PATTERN, sentence),
                    qoq=_find_change(QOQ_PATTERN, sentence),
                    source=sentence[:180],
                )
                break

    return list(results.values())


def detect_risk_points(text: str) -> list[str]:
    risk_keywords = {
        "收入承压": ["下滑", "下降", "减少", "低于预期", "承压"],
        "盈利能力波动": ["亏损", "毛利率下降", "净利润下降", "减值"],
        "现金流压力": ["现金流为负", "经营性现金流下降", "回款放缓"],
        "外部不确定性": ["竞争加剧", "需求疲软", "政策变化", "汇率波动"],
    }
    found = []
    for label, keywords in risk_keywords.items():
        if any(keyword in text for keyword in keywords):
            found.append(label)
    return found or ["未在文本中识别到明显风险关键词，建议结合完整公告进一步核验。"]


def detect_management_focus(text: str) -> list[str]:
    focus_keywords = {
        "研发投入与产品迭代": ["研发", "产品", "创新", "技术"],
        "降本增效": ["降本", "费用控制", "效率", "成本"],
        "市场拓展": ["客户", "渠道", "海外", "市场拓展"],
        "现金流与回款": ["现金流", "回款", "应收账款"],
    }
    found = []
    for label, keywords in focus_keywords.items():
        if any(keyword in text for keyword in keywords):
            found.append(label)
    return found or ["管理层关注点不足，建议上传更完整的管理层讨论与分析章节。"]
