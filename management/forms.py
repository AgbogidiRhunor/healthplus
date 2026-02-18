from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class SignupForm(UserCreationForm):
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('pharmacist', 'Pharmacist'),
    ]

    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)

    # Patient fields
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    gender = forms.ChoiceField(choices=[('', '-- Select --'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other')], required=False)
    blood_group = forms.ChoiceField(choices=[('', '-- Select --'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')], required=False)
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    allergies = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    medical_conditions = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)

    # Doctor/Pharmacist fields
    specialization = forms.CharField(max_length=100, required=False)
    license_number = forms.CharField(max_length=50, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'role',
                  'date_of_birth', 'gender', 'blood_group', 'phone', 'address', 'allergies',
                  'medical_conditions', 'specialization', 'license_number']
