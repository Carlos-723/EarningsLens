import unittest

from earnings_lens.report import analyze_filing, format_metric_table


class ReportTest(unittest.TestCase):
    def test_analyze_filing_returns_expected_sections(self):
        text = "营业收入 20.5 亿元，同比增长 10%。净利润 2.1 亿元，同比下降 3%。公司关注研发和客户拓展。"
        result = analyze_filing(text)

        self.assertIn("metrics", result)
        self.assertIn("risks", result)
        self.assertIn("management_focus", result)
        self.assertIn("investment_thesis", result)
        self.assertIn("analysis", result)
        self.assertGreaterEqual(len(result["metrics"]), 1)
        self.assertIn(result["investment_thesis"]["stance"], {"偏正面", "中性观察", "偏谨慎"})

    def test_format_metric_table(self):
        rows = format_metric_table(
            [
                {
                    "name": "营业收入",
                    "value": "20.5",
                    "unit": "亿元",
                    "yoy": "10%",
                    "qoq": None,
                    "source": "营业收入 20.5 亿元，同比增长 10%。",
                }
            ]
        )

        self.assertEqual(rows[0]["指标"], "营业收入")
        self.assertEqual(rows[0]["数值"], "20.5亿元")
        self.assertEqual(rows[0]["同比"], "10%")
        self.assertEqual(rows[0]["环比"], "-")


if __name__ == "__main__":
    unittest.main()
