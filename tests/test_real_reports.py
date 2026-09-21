import unittest
from pathlib import Path

from earnings_lens.metrics import extract_metrics
from earnings_lens.thesis import build_investment_thesis


FIXTURES = Path(__file__).parent / "fixtures" / "real_reports"
EXPECTED = {
    "000001_PingAnBank_2025Q1.txt": {
        "营业收入": ("33,709", "百万元", "-13.1%"),
        "归母净利润": ("14,096", "百万元", "-5.6%"),
        "经营活动现金流量净额": ("162,946", "百万元", None),
        "基本每股收益": ("0.62", "元/股", "-6.1%"),
    },
    "000900_XDTZ_2025Q1.txt": {
        "营业收入": ("1,752,071,588.10", "元", "32.11%"),
        "归母净利润": ("176,221,364.38", "元", "-7.11%"),
        "经营活动现金流量净额": ("802,476,676.92", "元", "8.59%"),
        "基本每股收益": ("0.1161", "元/股", "-7.12%"),
    },
    "002555_37Games_2025Q1.txt": {
        "营业收入": ("4,243,286,846.87", "元", "-10.67%"),
        "归母净利润": ("549,180,610.69", "元", "-10.87%"),
        "经营活动现金流量净额": ("582,696,083.65", "元", "-50.20%"),
        "基本每股收益": ("0.25", "元/股", "-10.71%"),
    },
    "002594_BYD_2025Q1.txt": {
        "营业收入": ("170,360,448,000.00", "元", "36.35%"),
        "归母净利润": ("9,154,985,000.00", "元", "100.38%"),
        "经营活动现金流量净额": ("8,580,961,000.00", "元", "-16.10%"),
        "基本每股收益": ("3.12", "元/股", "98.73%"),
    },
    "300750_CATL_2025Q1.txt": {
        "营业收入": ("84,704,589", "千元", "6.18%"),
        "归母净利润": ("13,962,558", "千元", "32.85%"),
        "经营活动现金流量净额": ("32,868,257", "千元", "15.91%"),
        "基本每股收益": ("3.18", "元/股", "33.05%"),
    },
}


class RealReportRegressionTest(unittest.TestCase):
    def test_five_reports_extract_all_core_metrics(self):
        for filename, expected in EXPECTED.items():
            with self.subTest(filename=filename):
                text = (FIXTURES / filename).read_text(encoding="utf-8")
                metrics = extract_metrics(text)
                by_name = {metric.name: metric for metric in metrics}

                for name, values in expected.items():
                    actual = by_name[name]
                    self.assertEqual((actual.value, actual.unit, actual.yoy), values)
                    self.assertEqual(actual.section, "主要会计数据和财务指标")
                    self.assertIsNotNone(actual.page)

                thesis = build_investment_thesis(metrics, [], [])
                self.assertEqual(thesis.data_completeness, 100)


if __name__ == "__main__":
    unittest.main()
