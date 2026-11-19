"""Thai text normalization and shared UTF-8 CSV validation."""

import csv
from functools import lru_cache
import io
import os
from pathlib import Path
import re
import unicodedata
import tempfile

# newmm uses PyThaiNLP's bundled dictionary. Keep its runtime directory local.
data_dir = Path(tempfile.gettempdir()) / "pythainlp-data"
os.environ.setdefault("PYTHAINLP_DATA_DIR", str(data_dir))
from pythainlp.tokenize import word_tokenize

LABELS = ("positive", "negative", "neutral")
URL_PATTERN = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)


def normalize_text(text):
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u200b", " ").replace("\ufeff", "")
    return " ".join(text.split())


def clean_thai_text(text):
    text = URL_PATTERN.sub(" ", text)
    text = "".join(
        char if not unicodedata.category(char).startswith("C") or char == "\u200d"
        else " "
        for char in text
    )
    return normalize_text(text.lower())


@lru_cache(maxsize=50_000)
def tokenize_thai_text(text):
    tokens = word_tokenize(text, engine="newmm", keep_whitespace=False)
    return tuple(
        token for token in tokens
        if any(char.isalnum() or unicodedata.category(char) in {"So", "Sk"}
               for char in token)
    )


def read_csv_rows(data, required_columns):
    """Read without coercing number-like strings, NA values, or quoted newlines."""
    try:
        decoded = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("ไฟล์ต้องใช้รหัสอักขระ UTF-8 หรือ UTF-8-SIG") from exc
    if "\x00" in decoded:
        raise ValueError("ไฟล์ CSV มีอักขระที่ไม่รองรับ")

    reader = csv.reader(io.StringIO(decoded, newline=""), strict=True)
    try:
        header = next(reader, [])
        if not header:
            raise ValueError("ไฟล์ CSV ว่างเปล่า กรุณาใส่หัวตารางและข้อมูล")
        if len(set(header)) != len(header):
            raise ValueError("หัวตาราง CSV มีชื่อคอลัมน์ซ้ำกัน")
        missing = [column for column in required_columns if column not in header]
        if missing:
            raise ValueError(f"ไฟล์ CSV ขาดคอลัมน์ {', '.join(missing)}")
        indices = [header.index(column) for column in required_columns]
        rows = []
        for row in reader:
            if not row:
                rows.append(tuple("" for _ in indices))
            elif len(row) != len(header):
                raise ValueError(f"จำนวนช่อง CSV ไม่ตรงกับหัวตารางใกล้บรรทัด {reader.line_num}")
            else:
                rows.append(tuple(row[index] for index in indices))
        return rows
    except csv.Error as exc:
        raise ValueError(f"รูปแบบ CSV ไม่ถูกต้องใกล้บรรทัด {reader.line_num}") from exc
