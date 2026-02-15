# /Users/vaibhavithakur/veripura-system/backend/app/ml/parser.py

import io
import re
from pathlib import Path

import fitz  # PyMuPDF
import pandas as pd
import pytesseract
from PIL import Image

from app.config import get_settings
from app.logger import logger
from app.schemas.upload import DocumentType


class ParserError(Exception):
    """Raised when document parsing fails"""

    pass


class DocumentParser:
    """
    Extracts text content from various document formats.
    Offline, no external APIs.
    """

    def __init__(self):
        self.settings = get_settings()
        # Configure Tesseract path
        if self.settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.settings.tesseract_cmd

    def parse(self, file_path: Path, doc_type: DocumentType) -> str:
        """
        Main parsing dispatcher.

        Args:
            file_path: Path to document
            doc_type: Document type (PDF, IMAGE, CSV)

        Returns:
            Extracted text content

        Raises:
            ParserError: If parsing fails
        """
        try:
            if doc_type == DocumentType.PDF:
                return self._parse_pdf(file_path)
            elif doc_type == DocumentType.IMAGE:
                return self._parse_image(file_path)
            elif doc_type == DocumentType.CSV:
                return self._parse_csv(file_path)
            else:
                raise ParserError(f"Unsupported document type: {doc_type}")

        except Exception as e:
            logger.error(f"Parser error for {file_path}: {str(e)}")
            raise ParserError(f"Failed to parse {doc_type.value}: {str(e)}") from e

    def _parse_pdf(self, file_path: Path) -> str:
        """
        Extract text from PDF using PyMuPDF.
        Fast, works for digital PDFs with embedded text.
        """
        text_parts = []

        with fitz.open(file_path) as doc:
            if len(doc) == 0:
                raise ParserError("PDF has no pages")

            for page_num, page in enumerate(doc, start=1):
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)

                # Limit pages processed (prevent DoS)
                if page_num >= 50:
                    logger.warning("PDF too long, processing first 50 pages only")
                    break

        combined_text = "\n".join(text_parts)

        # If no text extracted, might be scanned PDF (image-based)
        if len(combined_text.strip()) < 10:
            logger.info("PDF has no extractable text, attempting OCR")
            return self._ocr_pdf(file_path)

        return combined_text

    def _ocr_pdf(self, file_path: Path) -> str:
        """
        OCR for scanned PDFs (images embedded in PDF).
        Slower, but necessary for image-based PDFs.
        """
        text_parts = []

        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc, start=1):
                
                if page_num > 1:
                    logger.warning("OCR limited to first page (free tier optimization)")
                    break
            
                # Render page to image
                pix = page.get_pixmap(dpi=72)
                img_bytes = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_bytes))
                
                # 🔥 Convert to grayscale (faster + better OCR)
                if img.mode != "L":
                    img = img.convert("L")

                # OCR the image
                text = pytesseract.image_to_string(img, lang="eng", config="--oem 1 --psm 6")
                
                if text.strip():
                    text_parts.append(text)

                if page_num >= 10:  # OCR is expensive, limit pages
                    logger.warning("Scanned PDF too long, processing first 10 pages")
                    break

        return "\n".join(text_parts)

    def _parse_image(self, file_path: Path) -> str:
        """
        Extract text from image using Tesseract OCR.
        """
        img = Image.open(file_path)

        # Preprocess: convert to grayscale for better OCR
        if img.mode != "L":
            img = img.convert("L")

        # OCR
        text = pytesseract.image_to_string(img, lang="eng")

        if not text.strip():
            raise ParserError("No text detected in image")

        return text

    def _parse_csv(self, file_path: Path) -> str:
        """
        Parse CSV as structured text.
        Converts tabular data to text representation.
        """
        try:
            df = pd.read_csv(file_path, nrows=1000)  # Limit rows

            # Convert to text summary
            text_parts = [
                f"CSV with {len(df)} rows and {len(df.columns)} columns",
                f"Columns: {', '.join(df.columns.tolist())}",
                "\nSample data:\n",
                df.head(10).to_string(index=False),
            ]

            return "\n".join(text_parts)

        except Exception as e:
            raise ParserError(f"Invalid CSV format: {str(e)}") from e

    @staticmethod
    def extract_numbers(text: str) -> list[float]:
        """
        Extract all numeric values from text.
        Useful for amount/price analysis.
        """
        # Match numbers with optional decimals and thousands separators
        pattern = r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b"
        matches = re.findall(pattern, text)
        numbers = [float(m.replace(",", "")) for m in matches]
        return numbers

    @staticmethod
    def extract_dates(text: str) -> list[str]:
        """
        Extract date patterns from text.
        Supports common formats: YYYY-MM-DD, DD/MM/YYYY, MM-DD-YYYY
        """
        patterns = [
            r"\b\d{4}-\d{2}-\d{2}\b",  # ISO format
            r"\b\d{2}/\d{2}/\d{4}\b",  # DD/MM/YYYY
            r"\b\d{2}-\d{2}-\d{4}\b",  # MM-DD-YYYY
        ]
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, text))
        return dates
