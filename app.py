from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from earnings_lens.parser import extract_text_from_upload, read_text_file
from earnings_lens.report import analyze_filing, format_metric_table


ROOT = Path(__file__).parent
SAMPLE_PATH = ROOT / "sample_data" / "sample_announcement.txt"


st.set_page_config(page_title="EarningsLens", page_icon="📊", layout="wide")

st.title("EarningsLens | 上市公司公告/财报 AI 分析助手")
st.caption("面向股票研究和财报速读：上传 PDF/TXT 公告，提取核心指标，并生成摘要、风险点和投研点评。")

with st.sidebar:
    st.header("输入文件")
    uploaded = st.file_uploader("上传财报或公告", type=["pdf", "txt", "md"])
    use_sample = st.button("使用示例公告")
    st.divider()
    st.markdown("**运行模式**")
    st.write("未配置 API Key 时自动使用 mock/demo 模式，适合课堂展示和面试演示。")
    st.caption("仅辅助信息整理，不构成买卖建议。")


def load_input_text() -> str:
    if uploaded is not None:
        return extract_text_from_upload(uploaded)
    if use_sample:
        return read_text_file(SAMPLE_PATH)
    return read_text_file(SAMPLE_PATH)


text = load_input_text()

left, right = st.columns([0.92, 1.08])

with left:
    st.subheader("原文预览")
    st.text_area("公告文本", value=text[:5000], height=460, label_visibility="collapsed")

with right:
    st.subheader("分析结果")
    if st.button("开始分析", type="primary") or use_sample or uploaded is not None:
        with st.spinner("正在提取指标并生成分析..."):
            result = analyze_filing(text)

        metrics = result["metrics"]
        if metrics:
            st.markdown("#### 核心财务指标")
            st.dataframe(pd.DataFrame(format_metric_table(metrics)), use_container_width=True, hide_index=True)
        else:
            st.warning("暂未识别到核心财务指标。可以尝试上传更完整的财报文本。")

        st.markdown("#### AI 分析")
        st.markdown(result["analysis"])

        st.download_button(
            "下载 JSON 结果",
            data=json.dumps(result, ensure_ascii=False, indent=2),
            file_name="earnings_lens_analysis.json",
            mime="application/json",
        )
    else:
        st.info("点击“开始分析”，或直接使用示例公告体验完整流程。")
