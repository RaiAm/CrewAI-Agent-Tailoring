import fitz  # PyMuPDF
import importlib
from PIL import Image
import pytesseract
import os

docx = importlib.import_module("docx")

class ResumeParserTool:
    @staticmethod
    def parse_file(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".pdf":
            return ResumeParserTool._extract_pdf(file_path)
        elif ext in [".doc", ".docx"]:
            return ResumeParserTool._extract_docx(file_path)
        elif ext in [".png", ".jpg", ".jpeg"]:
            return ResumeParserTool._extract_ocr(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    def _extract_pdf(path: str) -> str:
        doc = fitz.open(path)
        text = ""
        for page in doc:
            page_text = page.get_text("text")
            if not page_text.strip():
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                page_text = pytesseract.image_to_string(img)
            text += page_text + "\n"
        return text

    @staticmethod
    def _extract_docx(path: str) -> str:
        doc = docx.Document(path)
        return "\n".join([p.text for p in doc.paragraphs if p.text])

    @staticmethod
    def _extract_ocr(path: str) -> str:
        image = Image.open(path)
        return pytesseract.image_to_string(image)