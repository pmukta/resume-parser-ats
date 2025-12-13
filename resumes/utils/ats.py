import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\-\s]{6,}\d)")

def calculate_ats_score(resume):
    score = 0

    # Name
    if resume.name and len(resume.name.strip()) >= 3:
        score += 10

    # Email
    if resume.email and EMAIL_RE.search(resume.email):
        score += 10

    # Mobile
    if resume.mobile and PHONE_RE.search(resume.mobile):
        score += 10

    # Skills
    skills = [s.strip() for s in (resume.skills or "").split(",") if s.strip()]
    if len(skills) >= 5:
        score += 25
    elif len(skills) >= 3:
        score += 15
    elif len(skills) >= 1:
        score += 8

    # Experience
    if resume.experience:
        length = len(resume.experience.strip())
        if length >= 150:
            score += 25
        elif length >= 75:
            score += 15
        elif length >= 30:
            score += 8

    # Education
    if resume.education:
        length = len(resume.education.strip())
        if length >= 80:
            score += 20
        elif length >= 40:
            score += 12
        elif length >= 20:
            score += 6

    return min(score, 100)

def ats_breakdown(resume):
    breakdown = []
    suggestions = []

    # Name
    if resume.name and len(resume.name.strip()) >= 3:
        breakdown.append(("Name", "ok"))
    else:
        breakdown.append(("Name", "missing"))
        suggestions.append("Add your full name.")

    # Email
    if resume.email:
        breakdown.append(("Email", "ok"))
    else:
        breakdown.append(("Email", "missing"))
        suggestions.append("Add a professional email address.")

    # Mobile
    if resume.mobile:
        breakdown.append(("Phone", "ok"))
    else:
        breakdown.append(("Phone", "missing"))
        suggestions.append("Add a contact phone number.")

    # Skills
    skills = [s.strip() for s in (resume.skills or "").split(",") if s.strip()]
    if len(skills) >= 5:
        breakdown.append(("Skills", "ok"))
    else:
        breakdown.append(("Skills", "weak"))
        suggestions.append("Add at least 5 relevant skills.")

    # Experience
    if resume.experience and len(resume.experience.strip()) >= 75:
        breakdown.append(("Experience", "ok"))
    else:
        breakdown.append(("Experience", "weak"))
        suggestions.append("Add detailed work experience with responsibilities.")

    # Education
    if resume.education and len(resume.education.strip()) >= 40:
        breakdown.append(("Education", "ok"))
    else:
        breakdown.append(("Education", "weak"))
        suggestions.append("Add your education details clearly.")

    return breakdown, suggestions
