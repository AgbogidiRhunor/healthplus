from django.urls import path
from . import views

urlpatterns = [
    path('drug/add/', views.add_drug, name='add_drug'),
    path('drug/<int:drug_id>/edit/', views.edit_drug, name='edit_drug'),
    path('drug/<int:drug_id>/delete/', views.delete_drug, name='delete_drug'),
    path('session/<int:session_id>/status/', views.update_session_status, name='update_session_status'),
    path('api/drugs/', views.drug_search_api, name='drug_search_api'),
]
