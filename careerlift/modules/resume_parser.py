"""
CareerLift AI — Resume Parser Module
Extracts text from PDF and DOCX resumes for analysis.
"""

import os
import re
from typing import Dict, Any

# PDF parsing
try:
    from pdfminer.high_level import extract_text as pdf_extract_text
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# DOCX parsing
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


ALLOWED_EXTENSIONS = {"pdf", "docx", "doc"}

# Common section headers to detect
SECTION_PATTERNS = {
    "summary":       r"(professional\s+summary|objective|about\s+me|profile|summary)",
    "experience":    r"(work\s+experience|experience|employment|career|professional\s+experience)",
    "education":     r"(education|academic|qualifications|degrees?)",
    "skills":        r"(skills|technical\s+skills|core\s+competencies|expertise|technologies)",
    "projects":      r"(projects|personal\s+projects|key\s+projects|portfolio)",
    "certifications":r"(certifications?|certificates?|credentials|licenses?)",
    "achievements":  r"(achievements?|awards?|honors?|accomplishments?|recognitions?)",
    "contact":       r"(contact|email|phone|linkedin|github|address)",
}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(filepath: str) -> str:
    if not PDF_AVAILABLE:
        return "[PDF parsing unavailable — install pdfminer.six]"
    try:
        text = pdf_extract_text(filepath)
        return text.strip() if text else ""
    except Exception as exc:
        return f"[PDF parsing error: {exc}]"


def extract_text_from_docx(filepath: str) -> str:
    if not DOCX_AVAILABLE:
        return "[DOCX parsing unavailable — install python-docx]"
    try:
        doc = Document(filepath)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as exc:
        return f"[DOCX parsing error: {exc}]"


def extract_resume_text(filepath: str) -> str:
    """Extract raw text from a resume file."""
    ext = filepath.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        return extract_text_from_pdf(filepath)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(filepath)
    return "[Unsupported file format]"


def extract_contact_info(text: str) -> Dict[str, str]:
    """Extract basic contact details from resume text."""
    info = {}
    # Email
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        info["email"] = email_match.group()
    # Phone
    phone_match = re.search(r"(\+?\d[\d\s\-().]{7,15}\d)", text)
    if phone_match:
        info["phone"] = phone_match.group().strip()
    # LinkedIn
    linkedin_match = re.search(r"linkedin\.com/in/[\w\-]+", text, re.IGNORECASE)
    if linkedin_match:
        info["linkedin"] = linkedin_match.group()
    # GitHub
    github_match = re.search(r"github\.com/[\w\-]+", text, re.IGNORECASE)
    if github_match:
        info["github"] = github_match.group()
    # Name (heuristic: first non-empty line)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if lines:
        info["name"] = lines[0]
    return info


def detect_sections(text: str) -> Dict[str, bool]:
    """Detect which resume sections are present."""
    text_lower = text.lower()
    return {
        section: bool(re.search(pattern, text_lower))
        for section, pattern in SECTION_PATTERNS.items()
    }


def extract_skills(text: str) -> list:
    """Extract likely skills from resume text."""
    tech_keywords = [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "react", "angular", "vue", "node.js", "django", "flask", "fastapi", "spring",
        "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
        "git", "github", "ci/cd", "linux", "bash", "rest", "graphql", "grpc",
        "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
        "pandas", "numpy", "spark", "hadoop", "kafka", "airflow",
        "agile", "scrum", "jira", "figma", "photoshop",
    ]
    text_lower = text.lower()
    return [skill for skill in tech_keywords if skill in text_lower]


def parse_resume(filepath: str) -> Dict[str, Any]:
    """Full resume parse — returns structured data."""
    text = extract_resume_text(filepath)
    if text.startswith("["):
        return {"error": text, "raw_text": ""}

    contact  = extract_contact_info(text)
    sections = detect_sections(text)
    skills   = extract_skills(text)
    word_count = len(text.split())

    # Simple quality heuristics
    quality_flags = []
    if word_count < 200:
        quality_flags.append("Resume seems too short (< 200 words)")
    if not sections.get("summary"):
        quality_flags.append("Missing professional summary/objective section")
    if not sections.get("experience"):
        quality_flags.append("Work experience section not clearly detected")
    if not skills:
        quality_flags.append("No recognisable technical skills found")
    if not contact.get("email"):
        quality_flags.append("Email address not found")

    return {
        "raw_text":     text,
        "contact":      contact,
        "sections":     sections,
        "skills":       skills,
        "word_count":   word_count,
        "quality_flags": quality_flags,
        "sections_present": sum(1 for v in sections.values() if v),
        "total_sections":   len(sections),
    }
