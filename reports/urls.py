from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path(
        'api/upload/',
        views.UploadReportView.as_view(),
        name='upload'
    ),
    path(
        'api/ask/<str:report_id>/',
        views.AskQuestionView.as_view(),
        name='ask'
    ),
]