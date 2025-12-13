from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q

from .models import Resume
from .utils.llm_parser import (
    extract_text_from_uploaded_file,
    parse_resume_with_llm
)
from .utils.ats import calculate_ats_score


# =========================
# RESUME LIST + SEARCH
# =========================
def resume_list(request):
    query = request.GET.get("q", "").strip()

    resumes = Resume.objects.all()

    if query:
        resumes = resumes.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(skills__icontains=query)
        )

    resumes = resumes.order_by("-created_at")

    return render(request, "resume_list.html", {
        "resumes": resumes,
        "query": query
    })


# =========================
# UPLOAD RESUME
# =========================
def upload_resume(request):
    if request.method == "POST":
        uploaded = request.FILES.get("resume_file")

        if not uploaded:
            messages.error(request, "Please upload a valid resume file.")
            return render(request, "upload.html")

        # Extract text
        resume_text = extract_text_from_uploaded_file(uploaded)

        if not resume_text:
            messages.error(request, "Unable to extract text from file.")
            return render(request, "upload.html")

        # Parse using LLM / logic
        data = parse_resume_with_llm(resume_text)

        # Create resume object
        resume = Resume.objects.create(
            name=data.get("name", ""),
            email=data.get("email", ""),
            mobile=data.get("mobile", ""),
            skills=", ".join(data.get("skills", [])),
            experience=data.get("experience", ""),
            education=data.get("education", ""),
            summary=data.get("professional_summary", ""),
        )

        # Calculate ATS score
        resume.ats_score = calculate_ats_score(resume)
        resume.save()

        messages.success(request, "Resume uploaded successfully.")

        return redirect("resumes:view_resume", resume_id=resume.id)

    return render(request, "upload.html")


# =========================
# VIEW RESUME
# =========================
def view_resume(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id)
    from .utils.ats import ats_breakdown

    breakdown, suggestions = ats_breakdown(resume)

    return render(request, "view_resume.html", {
        "resume": resume,
        "breakdown": breakdown,
        "suggestions": suggestions
    })


# =========================
# EDIT RESUME
# =========================
def edit_resume(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id)

    if request.method == "POST":
        resume.name = request.POST.get("name", "")
        resume.email = request.POST.get("email", "")
        resume.mobile = request.POST.get("mobile", "")
        resume.skills = request.POST.get("skills", "")
        resume.experience = request.POST.get("experience", "")
        resume.education = request.POST.get("education", "")

        # Recalculate ATS score after edit
        resume.ats_score = calculate_ats_score(resume)
        resume.save()

        messages.success(request, "Resume updated successfully.")
        return redirect("resumes:view_resume", resume_id=resume.id)

    return render(request, "edit_resume.html", {"resume": resume})


# =========================
# DELETE RESUME
# =========================
def delete_resume(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id)

    if request.method == "POST":
        resume.delete()
        messages.success(request, "Resume deleted successfully.")

    return redirect("resumes:resume_list")
