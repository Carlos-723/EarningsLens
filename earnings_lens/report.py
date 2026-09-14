from __future__ import annotations

from dataclasses import asdict

from .llm import generate_analysis
from .metrics import Metric, detect_management_focus, detect_risk_points, extract_metrics


def analyze_filing(text: str) -> dict:
    metrics = extract_metrics(text)
    risks = detect_risk_points(text)
    focus = detect_management_focus(text)
    analysis = generate_analysis(text, metrics, risks, focus)

    return {
        "metrics": [asdict(metric) for metric in metrics],
        "risks": risks,
        "management_focus": focus,
        "analysis": analysis,
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
                "来源句": item.get("source") or "-",
            }
        )
    return rows

