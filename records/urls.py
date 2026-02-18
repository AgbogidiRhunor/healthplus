from django.urls import path
from . import views

urlpatterns = [
    path('api/patient-search/', views.patient_search_api, name='patient_search_api'),
    path('api/all-patients/', views.all_patients_api, name='all_patients_api'),
    path('administer/', views.administer_drug, name='administer_drug'),
]
