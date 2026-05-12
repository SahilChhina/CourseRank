"""
Extracts raw text from a PDF syllabus using pdfplumber.
Returns page-level text and detected tables.
"""
import io
import pdfplumber
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ParsedSyllabus:
    full_text: str
    pages: List[str]
    tables: List[List[List[Optional[str]]]]  # [page][row][cell]


def parse_pdf(file_bytes: bytes) -> ParsedSyllabus:
    pages_text: List[str] = []
    all_tables: List[List[List[Optional[str]]]] = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text)

            for table in page.extract_tables() or []:
                all_tables.append(table)

    full_text = "\n".join(pages_text)
    return ParsedSyllabus(full_text=full_text, pages=pages_text, tables=all_tables)


def parse_pdf_path(path: str) -> ParsedSyllabus:
    with open(path, "rb") as f:
        return parse_pdf(f.read())
