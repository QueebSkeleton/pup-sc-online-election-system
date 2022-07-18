
from django.urls import path

from . import views


app_name = 'elections'
urlpatterns = [
    path('', views.index, name='index'),
    path('vote/', views.vote, name='vote'),
]
