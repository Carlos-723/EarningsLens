import unittest

from earnings_lens.metrics import Metric
from earnings_lens.thesis import build_investment_thesis


class InvestmentThesisTest(unittest.TestCase):
    def test_positive_growth_creates_bullish_points(self):
        thesis = build_investment_thesis(
            [
                Metric("营业收入", "100", "亿元", yoy="20%"),
                Metric("归母净利润", "15", "亿元", yoy="18%"),
                Metric("经营活动现金流量净额", "12", "亿元", yoy="16%"),
            ],
            risks=[],
            focus=["研发投入与产品迭代"],
        )

        self.assertEqual(thesis.stance, "偏正面")
        self.assertGreaterEqual(thesis.score, 3)
        self.assertTrue(any("收入同比增长" in item for item in thesis.bullish_points))

    def test_profit_decline_and_cash_flow_pressure_create_cautious_view(self):
        thesis = build_investment_thesis(
            [
                Metric("营业收入", "100", "亿元", yoy="18%"),
                Metric("归母净利润", "5", "亿元", yoy="-12%"),
                Metric("经营活动现金流量净额", "2", "亿元", yoy="-20%"),
            ],
            risks=["现金流压力", "外部不确定性"],
            focus=[],
        )

        self.assertEqual(thesis.stance, "偏谨慎")
        self.assertTrue(any("收入增长但利润下滑" in item for item in thesis.bearish_points))


if __name__ == "__main__":
    unittest.main()
