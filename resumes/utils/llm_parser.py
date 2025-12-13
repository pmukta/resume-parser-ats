# resumes/utils/llm_parser.py
import os
import io
import re
import json
import logging
from typing import Dict, Any, List

from groq import Groq
from PyPDF2 import PdfReader
import docx
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)

# Optional Tesseract path
TESSERACT_CMD = os.environ.get("TESSERACT_CMD")
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Groq client
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("⚠ GROQ_API_KEY not set. LLM extraction will fallback to local parser.")
    client = None
else:
    client = Groq(api_key=GROQ_API_KEY)

# Models list (use in fallback order)
GROQ_MODELS = [
    "llama-3.3-70b-specdec",
    "llama-3.3-70b-versatile",
    "llama-3.2-90b-text-preview",
]

# -----------------------------
# FILE TEXT EXTRACTION
# -----------------------------
def extract_text_from_uploaded_file(uploaded_file) -> str:
    filename = getattr(uploaded_file, "name", "").lower()
    file_bytes = uploaded_file.read()

    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    if filename.endswith(".pdf"):
        return extract_text_from_pdf_bytes(file_bytes)

    if filename.endswith(".docx"):
        return extract_text_from_docx_bytes(file_bytes)

    if filename.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif")):
        return extract_text_from_image_bytes(file_bytes)

    return ""


def extract_text_from_pdf_bytes(b: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(b))
        pages = []
        for p in reader.pages:
            try:
                pages.append(p.extract_text() or "")
            except Exception:
                continue
        return clean_text("\n".join(pages))
    except Exception as e:
        logger.exception("PDF extraction error: %s", e)
        return ""


def extract_text_from_docx_bytes(b: bytes) -> str:
    try:
        doc = docx.Document(io.BytesIO(b))
        lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return clean_text("\n".join(lines))
    except Exception as e:
        logger.exception("DOCX extraction error: %s", e)
        return ""


def extract_text_from_image_bytes(b: bytes) -> str:
    try:
        img = Image.open(io.BytesIO(b))
        text = pytesseract.image_to_string(img)
        return clean_text(text)
    except Exception as e:
        logger.exception("OCR error: %s", e)
        return ""


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r", "\n").replace("\t", " ")
    text = text.replace("•", "\n- ")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)

# -----------------------------
# LOCAL FALLBACK PARSER
# -----------------------------

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\-\s]{6,}\d)")

def quick_local_parse(resume_text: str) -> Dict[str, Any]:

    data = {
        "name": "",
        "email": "",
        "mobile": "",
        "skills": [],
        "experience": "",          # ✅ ADD
        "education": "",           # ✅ ADD
        "professional_summary": "",
        "ats_score": 0,
        "ats_improvement_tips": [],
        "strengths": [],
        "weaknesses": [],
        "skill_gaps": [],
    }


    if not resume_text:
        return data

    # EMAIL
    e = EMAIL_RE.search(resume_text)
    if e:
        data["email"] = e.group(0)

    # PHONE
    p = PHONE_RE.search(resume_text)
    if p:
        data["mobile"] = re.sub(r"\s+", " ", p.group(0))

    # SKILLS
    lower = resume_text.lower()
    if "skills" in lower:
        idx = lower.find("skills")
        snippet = resume_text[idx:idx + 350]
        words = re.findall(r"[A-Za-z+#\.\-]{3,}", snippet)
        data["skills"] = list(dict.fromkeys(words))[:20]

    # EXPERIENCE TIMELINE
    ranges = re.findall(r"(\b(?:19|20)\d{2}\b)[^\d]{0,5}(\b(?:19|20)\d{2}\b)", resume_text)
    for s, e in ranges:
        data["experience_timeline"].append({
            "company": "",
            "designation": "",
            "start": s,
            "end": e,
        })

    # Simple ATS score
    def calculate_ats_score(resume):
        score = 0
        total = 6

        if resume.name:
            score += 1
        if resume.email:
            score += 1
        if resume.mobile:
            score += 1
        if resume.skills:
            score += 1
        if resume.experience:
            score += 1
        if resume.education:
            score += 1

        return int((score / total) * 100)

    if data["ats_score"] < 50:
        data["ats_improvement_tips"] = [
            "Add clear skills section.",
            "Add structured work experience with dates.",
            "Include contact details clearly."
        ]
    else:
        data["ats_improvement_tips"] = [
            "Improve formatting and add measurable achievements."
        ]

    return data

# -----------------------------
# LLM CALL + FALLBACK LOGIC
# -----------------------------

def call_model_with_fallback(prompt: str, models: List[str]) -> str:
    if client is None:
        raise RuntimeError("GROQ_API_KEY missing; cannot call LLM.")

    last_error = None

    for model in models:
        try:
            logger.info(f"Trying Groq model: {model}")
            res = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            if hasattr(res, "choices") and res.choices:
                content = res.choices[0].message.content.strip()
                if content:
                    return content
        except Exception as e:
            logger.error(f"Model {model} failed: {e}")
            last_error = e
            continue

    raise last_error if last_error else RuntimeError("No model succeeded.")

def parse_resume_with_llm(resume_text: str) -> Dict[str, Any]:

    if not resume_text.strip():
        return quick_local_parse(resume_text)

    prompt = f"""
Extract structured information from this resume.

Return ONLY valid JSON with keys:

{{
  "name": "",
  "email": "",
  "mobile": "",
  "years_of_experience": "",
  "highest_qualification": "",
  "recent_employer": "",
  "recent_designation": "",
  "current_location": "",
  "skills": [],
  "experience_timeline": [{{"company": "", "designation": "", "start": "", "end": ""}}],
  "experience": "",
  "education": "",

  "professional_summary": "",
  "ats_score": 0,
  "ats_improvement_tips": [],
  "strengths": [],
  "weaknesses": [],
  "skill_gaps": []
}}

RULES:
- Do not invent details not in resume.
- Missing fields → empty strings/lists.
- ats_score must be an integer 0–100.
- JSON only.

Resume text:
\"\"\"{resume_text}\"\"\""""

    try:
        raw = call_model_with_fallback(prompt, GROQ_MODELS)

        try:
            parsed = json.loads(raw)
        except Exception:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            parsed = json.loads(match.group(0)) if match else {}

        defaults = quick_local_parse("")
        if not isinstance(parsed, dict):
            parsed = {}

        for k, v in defaults.items():
            parsed.setdefault(k, v)

        if not isinstance(parsed.get("skills"), list):
            parsed["skills"] = []

        if not isinstance(parsed.get("experience_timeline"), list):
            parsed["experience_timeline"] = []

        try:
            parsed["ats_score"] = int(parsed.get("ats_score") or 0)
        except:
            parsed["ats_score"] = 0

        return parsed

    except Exception as e:
        logger.error("LLM failed. Using local parser. Error: %s", e)
        return quick_local_parse(resume_text)
