from __future__ import annotations

from dataclasses import asdict

from .llm import generate_analysis
from .metrics import Metric, detect_management_focus, detect_risk_evidence, extract_metrics
from .thesis import build_investment_thesis, thesis_to_dict


def analyze_filing(text: str) -> dict:
    metrics = extract_metrics(text)
    risk_evidence = detect_risk_evidence(text)
    risks = [item["label"] for item in risk_evidence] or ["未在文本中识别到明显风险关键词，建议结合完整公告进一步核验。"]
    focus = detect_management_focus(text)
    thesis = build_investment_thesis(metrics, risks, focus)
    analysis, analysis_warning = generate_analysis(text, metrics, risks, focus, thesis)

    return {
        "metrics": [asdict(metric) for metric in metrics],
        "risks": risks,
        "risk_evidence": risk_evidence,
        "management_focus": focus,
        "investment_thesis": thesis_to_dict(thesis),
        "analysis": analysis,
        "analysis_warning": analysis_warning,
    }


def format_metric_table(metrics: list[Metric] | list[dict]) -> list[dict]:
    rows = []
    for metric in metrics:
        item = metric if isinstance(metric, dict) else asdict(metric)
        rows.append(
            {
                "指标": item["name"],
                "数值": f'{item["value"]}{item["unit"]}',
                "同比": item.get("yoy") or "-",
                "环比": item.get("qoq") or "-",
                "百分点变化": item.get("percentage_point_change") or "-",
                "期间": item.get("period") or "-",
                "页码": item.get("page") or "-",
                "来源句": item.get("source") or "-",
            }
        )
    return rows
