from __future__ import annotations

from io import BytesIO
from pathlib import Path


MAX_FILE_BYTES = 15 * 1024 * 1024
MAX_PDF_PAGES = 100
MAX_TEXT_CHARS = 200_000


def read_text_file(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def extract_text_from_bytes(filename: str, content: bytes) -> str:
    if not content:
        raise ValueError("文件为空，请上传包含正文的文件。")
    if len(content) > MAX_FILE_BYTES:
        raise ValueError("文件超过 15 MB，请上传更小的文件。")

    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md"}:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("文本文件不是 UTF-8 编码，请转换编码后重试。") from exc
    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("读取 PDF 需要安装 requirements.txt 中的依赖。") from exc
        reader = PdfReader(BytesIO(content))
        if len(reader.pages) > MAX_PDF_PAGES:
            raise ValueError("PDF 超过 100 页，请拆分后上传。")
        pages = [page.extract_text() or "" for page in reader.pages]
        if not any(page.strip() for page in pages):
            raise ValueError("未提取到 PDF 文本，可能是扫描件，请上传可复制文本的 PDF。")
        text = "\n".join(f"[第 {number} 页]\n{page}" for number, page in enumerate(pages, 1))
    else:
        raise ValueError("仅支持 PDF、TXT 和 MD 文件。")

    if not text.strip():
        raise ValueError("未读取到有效文本，请检查文件内容。")
    return text[:MAX_TEXT_CHARS]


def extract_text_from_upload(uploaded_file) -> str:
    return extract_text_from_bytes(uploaded_file.name, uploaded_file.getvalue())
