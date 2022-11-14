
from django.urls import path

from . import views


app_name = 'elections'
urlpatterns = [
    path('', views.index, name='index'),
    path('step-1', views.vote_step_first, name='vote_step_first'),
    path('step-2', views.vote_step_second, name='vote_step_second'),
]
