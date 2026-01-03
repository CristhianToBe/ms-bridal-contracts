from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("run-word/", views.run_word_view, name="run_word"),
    path("run-excel/", views.run_excel_view, name="run_excel"),
    path("upload-template/", views.upload_template_view, name="upload_template"),
    path("create-json/", views.create_json_view, name="create_json"),
    path("get-json-template/", views.get_json_template_view, name="get_json_template"),
    path("create-mapping/", views.create_mapping_view, name="create_mapping"), 
]