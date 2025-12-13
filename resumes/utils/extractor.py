# resumes/utils/extractor.py
import io
import docx
from PIL import Image
import pytesseract
from pdfminer.high_level import extract_text as pdf_extract

def extract_text(file_obj):
    """
    Detect type by name and extract text. Accepts Django InMemoryUploadedFile/File.
    Returns cleaned text (string).
    """
    name = getattr(file_obj, "name", "").lower()

    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_obj)

    if name.endswith(".docx"):
        return extract_text_from_docx(file_obj)

    if name.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif")):
        return extract_text_from_image(file_obj)

    # fallback: try reading as bytes and decode
    try:
        raw = file_obj.read()
        if isinstance(raw, bytes):
            try:
                return raw.decode("utf-8", errors="ignore")
            finally:
                file_obj.seek(0)
    except Exception:
        pass

    return ""


def extract_text_from_pdf(file_obj):
    try:
        # pdfminer accepts a file-like object via fileobj parameter
        # ensure we pass BytesIO
        raw = file_obj.read()
        file_bytes = io.BytesIO(raw)
        text = pdf_extract(file_bytes)
        file_obj.seek(0)
        return clean_text(text)
    except Exception as e:
        print("PDF extraction error:", e)
        try:
            file_obj.seek(0)
        except:
            pass
        return ""


def extract_text_from_docx(file_obj):
    try:
        # python-docx accepts a file-like object
        file_obj.seek(0)
        doc = docx.Document(file_obj)
        text = "\n".join([p.text for p in doc.paragraphs])
        file_obj.seek(0)
        return clean_text(text)
    except Exception as e:
        print("DOCX extraction error:", e)
        try:
            file_obj.seek(0)
        except:
            pass
        return ""


def extract_text_from_image(file_obj):
    try:
        file_obj.seek(0)
        image = Image.open(file_obj)
        text = pytesseract.image_to_string(image)
        file_obj.seek(0)
        return clean_text(text)
    except Exception as e:
        print("Image extraction error:", e)
        try:
            file_obj.seek(0)
        except:
            pass
        return ""


def clean_text(text):
    if not text:
        return ""
    text = text.replace("\t", " ")
    text = text.replace("\r", "\n")
    text = text.replace("•", "\n- ")
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)
