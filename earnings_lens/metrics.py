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
    period: str | None = None
    percentage_point_change: str | None = None
    source_position: int | None = None
    page: int | None = None
    section: str | None = None
    confidence: float = 0.95


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
ALIAS_TO_KEY = {alias.lower(): key for key, aliases in METRIC_ALIASES.items() for alias in aliases}
METRIC_PATTERN = re.compile(
    "|".join(re.escape(alias) for alias in sorted(ALIAS_TO_KEY, key=len, reverse=True)),
    re.IGNORECASE,
)
VALUE_AFTER_ALIAS_PATTERN = re.compile(
    r"^\s*(?:为|达|达到|实现|录得|合计|was|were|reached|人民币|RMB|CNY|[:：,，])*\s*"
    r"(?P<value>-?\d+(?:,\d{3})*(?:\.\d+)?)\s*"
    r"(?P<unit>亿元|万元|元|%|百分比|million|billion|bn|m)",
    re.IGNORECASE,
)
YOY_PATTERN = re.compile(r"(同比|year[-\s]?over[-\s]?year|YoY)[^\d\-+]{0,8}(?P<value>[+\-]?\d+(?:\.\d+)?)\s*%", re.IGNORECASE)
QOQ_PATTERN = re.compile(r"(环比|quarter[-\s]?over[-\s]?quarter|QoQ)[^\d\-+]{0,8}(?P<value>[+\-]?\d+(?:\.\d+)?)\s*%", re.IGNORECASE)
PP_PATTERN = re.compile(r"(?:同比|环比)?[^\d\-+]{0,8}(?P<value>[+\-]?\d+(?:\.\d+)?)\s*(?:个)?百分点", re.IGNORECASE)
PERIOD_PATTERN = re.compile(r"(?:20\d{2}年(?:第?[一二三四1-4]季度|上半年|下半年|年度)?|本报告期|本期|上期)")
PAGE_PATTERN = re.compile(r"\[第\s*(\d+)\s*页\]")


def normalize_text(text: str) -> str:
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    return [sentence for sentence, _ in _sentences_with_positions(normalize_text(text))]


def _sentences_with_positions(text: str) -> list[tuple[str, int]]:
    results = []
    start = 0
    for match in re.finditer(r"(?<=[。；;!?])\s*|\n+", text):
        raw = text[start : match.start()]
        sentence = raw.strip()
        if sentence:
            results.append((sentence, start + len(raw) - len(raw.lstrip())))
        start = match.end()
    raw = text[start:]
    sentence = raw.strip()
    if sentence:
        results.append((sentence, start + len(raw) - len(raw.lstrip())))
    return results


def _find_value_after_alias(segment: str, alias: str) -> tuple[str, str] | None:
    match = VALUE_AFTER_ALIAS_PATTERN.match(segment[len(alias) :])
    if not match:
        return None
    return match.group("value"), match.group("unit")


def _find_change(pattern: re.Pattern[str], segment: str, suffix: str = "%") -> str | None:
    match = pattern.search(segment)
    if not match:
        return None
    value = _signed_change_value(match.group("value"), match.group(0))
    return f"{value:g}{suffix}"


def _signed_change_value(raw_value: str, context: str) -> float:
    value = float(raw_value.replace("+", ""))
    lower_context = context.lower()
    if raw_value.startswith("-"):
        return value
    if any(word in lower_context for word in ["下降", "下滑", "减少", "降低", "decline", "decrease", "down"]):
        return -abs(value)
    if any(word in lower_context for word in ["增长", "增加", "提升", "上升", "increase", "grow", "up"]):
        return abs(value)
    return value


def _last_match(pattern: re.Pattern[str], text: str):
    matches = list(pattern.finditer(text))
    return matches[-1] if matches else None


def extract_metrics(text: str) -> list[Metric]:
    """Extract indicators only when a value and unit directly follow the name."""
    normalized = normalize_text(text)
    results: list[Metric] = []
    seen: set[tuple[str, str, str, str | None]] = set()

    for sentence, sentence_start in _sentences_with_positions(normalized):
        matches = list(METRIC_PATTERN.finditer(sentence))
        for index, match in enumerate(matches):
            alias = match.group(0)
            key = ALIAS_TO_KEY[alias.lower()]
            end = matches[index + 1].start() if index + 1 < len(matches) else len(sentence)
            segment = sentence[match.start() : end]
            value_unit = _find_value_after_alias(segment, alias)
            if not value_unit:
                continue
            value, unit = value_unit
            prefix = normalized[: sentence_start + match.start()]
            # ponytail: nearby period heuristic; use table parsing when table fidelity becomes required.
            period_match = _last_match(PERIOD_PATTERN, sentence[: match.start()]) or _last_match(PERIOD_PATTERN, prefix[-120:])
            page_match = _last_match(PAGE_PATTERN, prefix)
            period = period_match.group(0) if period_match else None
            identity = (key, value, unit, period)
            if identity in seen:
                continue
            seen.add(identity)
            results.append(
                Metric(
                    name=DISPLAY_NAMES[key],
                    value=value,
                    unit=unit,
                    yoy=_find_change(YOY_PATTERN, segment),
                    qoq=_find_change(QOQ_PATTERN, segment),
                    percentage_point_change=_find_change(PP_PATTERN, segment, "个百分点"),
                    period=period,
                    source=segment[:180],
                    source_position=sentence_start + match.start(),
                    page=int(page_match.group(1)) if page_match else None,
                )
            )
    return results


RISK_KEYWORDS = {
    "收入承压": ["下滑", "下降", "减少", "低于预期", "承压"],
    "盈利能力波动": ["亏损", "毛利率下降", "净利润下降", "减值"],
    "现金流压力": ["现金流为负", "经营性现金流下降", "回款放缓"],
    "外部不确定性": ["竞争加剧", "需求疲软", "政策变化", "汇率波动"],
}


def detect_risk_evidence(text: str) -> list[dict]:
    normalized = normalize_text(text)
    evidence = []
    for sentence, position in _sentences_with_positions(normalized):
        for label, keywords in RISK_KEYWORDS.items():
            if any(keyword in sentence for keyword in keywords) and not any(item["label"] == label for item in evidence):
                page_match = _last_match(PAGE_PATTERN, normalized[:position])
                evidence.append(
                    {
                        "label": label,
                        "source_text": sentence[:180],
                        "source_position": position,
                        "page": int(page_match.group(1)) if page_match else None,
                        "section": None,
                        "confidence": 0.8,
                    }
                )
    return evidence


def detect_risk_points(text: str) -> list[str]:
    found = [item["label"] for item in detect_risk_evidence(text)]
    return found or ["未在文本中识别到明显风险关键词，建议结合完整公告进一步核验。"]


def detect_management_focus(text: str) -> list[str]:
    focus_keywords = {
        "研发投入与产品迭代": ["研发", "产品", "创新", "技术"],
        "降本增效": ["降本", "费用控制", "效率", "成本"],
        "市场拓展": ["客户", "渠道", "海外", "市场拓展"],
        "现金流与回款": ["现金流", "回款", "应收账款"],
    }
    found = [label for label, keywords in focus_keywords.items() if any(keyword in text for keyword in keywords)]
    return found or ["管理层关注点不足，建议上传更完整的管理层讨论与分析章节。"]
