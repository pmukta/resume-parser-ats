from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path("", lambda request: redirect("resumes/")),
    path("admin/", admin.site.urls),
    path("resumes/", include("resumes.urls")),
]
