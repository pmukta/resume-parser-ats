from django.db import models

class Resume(models.Model):
    name = models.CharField(max_length=255, blank=True)
    email = models.CharField(max_length=255, blank=True)
    mobile = models.CharField(max_length=50, blank=True)

    skills = models.TextField(blank=True)
    experience = models.TextField(blank=True)   # ✅ ADDED
    education = models.TextField(blank=True)    # ✅ ADDED
    summary = models.TextField(blank=True)

    ats_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def skill_list(self):
        if self.skills:
            return [s.strip() for s in self.skills.split(",") if s.strip()]
        return []

    def __str__(self):
        return self.name or "Unnamed Resume"
