from __future__ import annotations

from dataclasses import dataclass, asdict

from .metrics import Metric


@dataclass(frozen=True)
class InvestmentThesis:
    stance: str
    score: int
    data_completeness: int
    confidence: str
    one_line_view: str
    bullish_points: list[str]
    bearish_points: list[str]
    follow_up_questions: list[str]


def _to_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value.replace("%", "").replace("+", "").replace(",", ""))
    except ValueError:
        return None


def _metric_map(metrics: list[Metric]) -> dict[str, Metric]:
    result = {}
    for metric in metrics:
        if metric.name not in result or metric.confidence > result[metric.name].confidence:
            result[metric.name] = metric
    return result


def _yoy(metric: Metric | None) -> float | None:
    if metric is None:
        return None
    return _to_float(metric.yoy)


def build_investment_thesis(metrics: list[Metric], risks: list[str], focus: list[str]) -> InvestmentThesis:
    metric_by_name = _metric_map(metrics)
    revenue_yoy = _yoy(metric_by_name.get("营业收入"))
    profit_yoy = _yoy(metric_by_name.get("归母净利润"))
    cash_flow_yoy = _yoy(metric_by_name.get("经营活动现金流量净额"))
    gross_margin_yoy = _yoy(metric_by_name.get("毛利率"))

    score = 0
    bullish: list[str] = []
    bearish: list[str] = []
    questions: list[str] = []

    if revenue_yoy is not None:
        if revenue_yoy >= 15:
            score += 2
            bullish.append(f"收入同比增长 {revenue_yoy:g}%，说明需求或交付规模仍在扩张。")
        elif revenue_yoy > 0:
            score += 1
            bullish.append(f"收入同比增长 {revenue_yoy:g}%，经营仍保持正增长。")
        else:
            score -= 2
            bearish.append(f"收入同比 {revenue_yoy:g}%，主业增长承压，需要判断是周期因素还是竞争力下降。")
    else:
        questions.append("补充收入同比数据，判断公司增长是否来自主业扩张。")

    if profit_yoy is not None:
        if profit_yoy >= 10:
            score += 2
            bullish.append(f"归母净利润同比增长 {profit_yoy:g}%，盈利释放较明确。")
        elif profit_yoy >= 0:
            score += 1
            bullish.append(f"归母净利润同比为正，说明利润端暂未明显恶化。")
        else:
            score -= 2
            bearish.append(f"归母净利润同比 {profit_yoy:g}%，收入增长能否转化为利润需要继续验证。")
    else:
        questions.append("补充归母净利润变化，判断增长质量和利润弹性。")

    if revenue_yoy is not None and profit_yoy is not None:
        if revenue_yoy > 10 and profit_yoy < 0:
            score -= 2
            bearish.append("收入增长但利润下滑，可能存在价格战、成本上升或费用投放压力。")
        elif profit_yoy > revenue_yoy and revenue_yoy > 0:
            score += 1
            bullish.append("利润增速高于收入增速，经营杠杆或费用控制可能正在改善。")

    if cash_flow_yoy is not None:
        if cash_flow_yoy < 0:
            score -= 1
            bearish.append(f"经营现金流同比 {cash_flow_yoy:g}%，利润质量和回款节奏需要重点跟踪。")
        elif cash_flow_yoy >= 10:
            score += 1
            bullish.append(f"经营现金流同比增长 {cash_flow_yoy:g}%，回款和利润含金量表现较好。")
    else:
        questions.append("查看经营现金流和应收账款，避免只看利润不看回款。")

    if gross_margin_yoy is not None and gross_margin_yoy < 0:
        score -= 1
        bearish.append("毛利率出现同比压力，需验证是否由竞争加剧、成本上升或产品结构变化导致。")

    if "研发投入与产品迭代" in focus:
        bullish.append("管理层强调研发和产品迭代，后续可跟踪新产品能否带来订单或毛利改善。")
    if "市场拓展" in focus:
        bullish.append("管理层强调客户或海外拓展，后续重点看订单、客户集中度和收入兑现。")
    if "现金流压力" in risks:
        bearish.append("文本已触发现金流风险关键词，短线研究中应优先核对回款和应收账款变化。")
    if "外部不确定性" in risks:
        bearish.append("公告提示竞争、需求或汇率等外部变量，估值上不宜只按乐观增长情景外推。")

    questions.extend(
        [
            "当前估值分位处于历史高位还是低位？业绩变化是否已被股价提前反映？",
            "与同行相比，公司收入增速、毛利率和现金流是否更强？",
            "下一期最该跟踪的领先指标是什么：订单、价格、费用率、库存还是回款？",
        ]
    )

    bullish = _dedupe(bullish)[:4]
    bearish = _dedupe(bearish)[:4]
    questions = _dedupe(questions)[:4]

    score = max(-10, min(10, score))
    required = ["营业收入", "归母净利润", "经营活动现金流量净额"]
    data_completeness = round(sum(name in metric_by_name for name in required) / len(required) * 100)
    confidence = "高" if data_completeness == 100 else "中" if data_completeness >= 67 else "低"

    if score >= 3:
        stance = "偏正面"
        view = "基本面信号偏积极，但仍需要结合估值和同行表现确认股价是否已经反映。"
    elif score <= -2:
        stance = "偏谨慎"
        view = "公告中风险信号多于正面信号，短期更适合先做跟踪清单而不是直接下结论。"
    else:
        stance = "中性观察"
        view = "信息呈现多空交织，适合继续补充历史数据、估值和同行对比后再判断。"

    return InvestmentThesis(
        stance=stance,
        score=score,
        data_completeness=data_completeness,
        confidence=confidence,
        one_line_view=view,
        bullish_points=bullish or ["暂未识别到足够明确的正面信号。"],
        bearish_points=bearish or ["暂未识别到足够明确的负面信号，但仍需结合完整财报核验。"],
        follow_up_questions=questions,
    )


def thesis_to_dict(thesis: InvestmentThesis) -> dict:
    return asdict(thesis)


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
