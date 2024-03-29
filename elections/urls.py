
from django.urls import path

from . import views


app_name = 'elections'
urlpatterns = [
    path('', views.index, name='index'),
    path('step-1/', views.vote_step_first, name='vote_step_first'),
    path('step-2/', views.vote_step_second, name='vote_step_second'),
    path('confirm-candidates/', views.confirm_selected_candidates,
         name='confirm_selected_candidates'),
    path('ballot/<int:id>/', views.ballot_pdf_receipt,
         name='ballot_pdf_receipt'),
]
