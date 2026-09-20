import os
import sys
import types
import unittest
from unittest.mock import patch

from earnings_lens.llm import generate_analysis
from earnings_lens.parser import extract_text_from_bytes
from earnings_lens.thesis import build_investment_thesis


class ResilienceTest(unittest.TestCase):
    def test_empty_file_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "文件为空"):
            extract_text_from_bytes("empty.txt", b"")

    def test_llm_timeout_falls_back_to_rules(self):
        class BrokenOpenAI:
            def __init__(self, **_kwargs):
                raise TimeoutError("timed out")

        fake_module = types.SimpleNamespace(OpenAI=BrokenOpenAI)
        thesis = build_investment_thesis([], [], [])
        with patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "test"}), patch.dict(
            sys.modules, {"openai": fake_module}
        ):
            analysis, warning = generate_analysis("测试公告", [], [], [], thesis)

        self.assertIn("200字投研点评", analysis)
        self.assertIn("LLM 请求失败", warning)
