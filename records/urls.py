from django.urls import path
from . import views

urlpatterns = [
    path('api/patient-search/', views.patient_search_api, name='patient_search_api'),
    path('api/all-patients/', views.all_patients_api, name='all_patients_api'),
    path('api/patient/<int:patient_id>/records/', views.patient_records_api, name='patient_records_api'),
    path('administer/', views.administer_drug, name='administer_drug'),
    path('download/', views.download_medical_record, name='download_medical_record'),
]