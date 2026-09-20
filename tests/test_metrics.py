import unittest

from earnings_lens.metrics import detect_management_focus, detect_risk_points, extract_metrics


class MetricExtractionTest(unittest.TestCase):
    def test_extracts_metrics_and_changes(self):
        text = "公司实现营业收入 128.45 亿元，同比增长 18.6%，环比增长 5.2%。归母净利润 14.32 亿元，同比下降 2.1%。"
        metrics = extract_metrics(text)
        names = {item.name: item for item in metrics}

        self.assertIn("营业收入", names)
        self.assertEqual(names["营业收入"].value, "128.45")
        self.assertEqual(names["营业收入"].unit, "亿元")
        self.assertEqual(names["营业收入"].yoy, "18.6%")
        self.assertEqual(names["营业收入"].qoq, "5.2%")
        self.assertIn("归母净利润", names)

    def test_detects_risk_and_focus(self):
        text = "市场竞争加剧，经营性现金流下降。公司继续加大研发投入并拓展海外客户。"

        self.assertIn("现金流压力", detect_risk_points(text))
        self.assertIn("研发投入与产品迭代", detect_management_focus(text))
        self.assertIn("市场拓展", detect_management_focus(text))

    def test_negative_change_words_are_signed(self):
        text = "归母净利润 14.32 亿元，同比下降 2.1%。经营活动现金流量净额 9.85 亿元，同比减少 12.3%。"
        metrics = extract_metrics(text)
        names = {item.name: item for item in metrics}

        self.assertEqual(names["归母净利润"].yoy, "-2.1%")
        self.assertEqual(names["经营活动现金流量净额"].yoy, "-12.3%")

    def test_does_not_treat_growth_rate_as_metric_value(self):
        metrics = extract_metrics("营业收入同比增长 18.6%，实际金额另见财务报表。")
        self.assertEqual(metrics, [])

    def test_multiple_metrics_in_one_sentence_keep_their_own_changes(self):
        text = "2025年营业收入 128.45 亿元，同比增长 18.6%，归母净利润 -2.30 亿元，同比下降 12.3%。"
        metrics = extract_metrics(text)

        self.assertEqual(len(metrics), 2)
        self.assertEqual(metrics[0].yoy, "18.6%")
        self.assertEqual(metrics[1].value, "-2.30")
        self.assertEqual(metrics[1].yoy, "-12.3%")
        self.assertEqual(metrics[0].period, "2025年")

    def test_keeps_multiple_periods_and_percentage_points(self):
        text = "2025年毛利率 35%，同比提升 2.5 个百分点。2024年毛利率 32.5%。"
        metrics = extract_metrics(text)

        self.assertEqual(len(metrics), 2)
        self.assertEqual(metrics[0].percentage_point_change, "2.5个百分点")
        self.assertEqual([item.period for item in metrics], ["2025年", "2024年"])


if __name__ == "__main__":
    unittest.main()
