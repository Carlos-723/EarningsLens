from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pandas as pd
import streamlit as st

from earnings_lens.parser import MAX_TEXT_CHARS, extract_text_from_bytes, read_text_file
from earnings_lens.report import analyze_filing, format_metric_table


ROOT = Path(__file__).parent
SAMPLE_PATH = ROOT / "sample_data" / "sample_announcement.txt"


st.set_page_config(page_title="EarningsLens", page_icon="📊", layout="wide")

st.title("EarningsLens | 上市公司公告/财报 AI 分析助手")
st.caption("面向股票研究和财报速读：上传 PDF/TXT 公告，提取核心指标，并生成摘要、风险点和投研点评。")

with st.sidebar:
    st.header("输入文件")
    uploaded = st.file_uploader("上传财报或公告", type=["pdf", "txt", "md"])
    st.caption("未上传文件时自动使用示例公告。")
    st.divider()
    st.markdown("**运行模式**")
    st.write("未配置 API Key 时自动使用 mock/demo 模式，适合课堂展示和面试演示。")
    st.caption("仅辅助信息整理，不构成买卖建议。")


@st.cache_data(show_spinner=False)
def parse_upload(filename: str, content: bytes) -> str:
    return extract_text_from_bytes(filename, content)


def load_input_text() -> str:
    if uploaded is not None:
        return parse_upload(uploaded.name, uploaded.getvalue())
    return read_text_file(SAMPLE_PATH)


try:
    text = load_input_text()
except (ValueError, RuntimeError) as exc:
    st.error(str(exc))
    st.stop()

if len(text) >= MAX_TEXT_CHARS:
    st.warning(f"文本较长，当前仅分析前 {MAX_TEXT_CHARS:,} 个字符。")

input_key = "v2:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
if st.session_state.get("analysis_input_key") != input_key:
    st.session_state.pop("analysis_result", None)
    st.session_state["analysis_input_key"] = input_key

left, right = st.columns([0.92, 1.08])

with left:
    st.subheader("原文预览")
    st.text_area("公告文本", value=text[:5000], height=460, label_visibility="collapsed")

with right:
    st.subheader("分析结果")
    if st.button("开始分析", type="primary"):
        with st.spinner("正在提取指标并生成分析..."):
            st.session_state["analysis_result"] = analyze_filing(text)

    result = st.session_state.get("analysis_result")
    if result:
        metrics = result["metrics"]
        thesis = result["investment_thesis"]
        st.markdown("#### 股票研究观察")
        c1, c2, c3 = st.columns(3)
        c1.metric("初步观点", thesis["stance"])
        c2.metric("规则信号分", thesis["score"])
        c3.metric("数据完整度", f'{thesis["data_completeness"]}%')
        st.caption(f'分析置信度：{thesis["confidence"]}。{thesis["one_line_view"]}')

        with st.expander("查看规则信号分说明"):
            st.write("分数范围为 -10 至 10，仅汇总收入、利润、现金流等公开信号；缺失数据降低完整度，不按负面计分。它不是正式投资评级。")

        bull_col, bear_col = st.columns(2)
        with bull_col:
            st.markdown("##### 看多因素")
            for point in thesis["bullish_points"]:
                st.markdown(f"- {point}")
        with bear_col:
            st.markdown("##### 看空因素")
            for point in thesis["bearish_points"]:
                st.markdown(f"- {point}")

        with st.expander("下一步应该查什么"):
            for question in thesis["follow_up_questions"]:
                st.markdown(f"- {question}")

        if metrics:
            st.markdown("#### 核心财务指标")
            st.dataframe(pd.DataFrame(format_metric_table(metrics)), width="stretch", hide_index=True)
        else:
            st.warning("暂未识别到核心财务指标。可以尝试上传更完整的财报文本。")

        st.markdown("#### AI 分析")
        if result.get("analysis_warning"):
            st.warning(result["analysis_warning"])
        st.markdown(result["analysis"])

        st.download_button(
            "下载 JSON 结果",
            data=json.dumps(result, ensure_ascii=False, indent=2),
            file_name="earnings_lens_analysis.json",
            mime="application/json",
        )
    else:
        st.info("点击“开始分析”生成结果。上传新文件后，旧结果会自动清空。")
