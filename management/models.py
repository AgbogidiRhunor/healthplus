from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('pharmacist', 'Pharmacist'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    is_approved = models.BooleanField(default=False)

    # Patient profile fields
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)

    # Doctor/Pharmacist profile fields
    specialization = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def can_login(self):
        if self.role == 'patient':
            return True
        return self.is_approved

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
