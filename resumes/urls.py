from django.urls import path
from . import views

app_name = "resumes"

urlpatterns = [
    path("", views.resume_list, name="resume_list"),
    path("upload/", views.upload_resume, name="upload_resume"),
    path("delete/<int:resume_id>/", views.delete_resume, name="delete_resume"),
    path("view/<int:resume_id>/", views.view_resume, name="view_resume"),
    path("edit/<int:resume_id>/", views.edit_resume, name="edit_resume"),

]
