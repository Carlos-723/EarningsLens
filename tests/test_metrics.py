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


if __name__ == "__main__":
    unittest.main()

