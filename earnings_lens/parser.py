from __future__ import annotations

from pathlib import Path


def read_text_file(path: str | Path) -> str:
    file_path = Path(path)
    return file_path.read_text(encoding="utf-8")


def read_pdf_file(path: str | Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required to read PDF files. Install requirements.txt first.") from exc

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def extract_text_from_upload(uploaded_file) -> str:
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix in {".txt", ".md"}:
        return uploaded_file.getvalue().decode("utf-8", errors="ignore")
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("pypdf is required to read PDF files. Install requirements.txt first.") from exc

        reader = PdfReader(uploaded_file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    raise ValueError("Only PDF, TXT and MD files are supported.")

