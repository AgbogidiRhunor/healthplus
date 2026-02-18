from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from management.models import User
from pharmacy.models import Drug
from .models import AdministrationSession, SessionDrug


def doctor_required(func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'doctor':
            messages.error(request, 'Access denied.')
            return redirect('login')
        return func(request, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


def patient_search_api(request):
    if not request.user.is_authenticated or request.user.role != 'doctor':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    query = request.GET.get('q', '').strip()
    patients = User.objects.filter(role='patient')
    if query:
        from django.db.models import Q
        patients = patients.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    patients = patients.order_by('first_name', 'last_name', 'username').distinct()[:20]
    data = [{'id': p.id, 'username': p.username, 'name': p.full_name, 'display': f"{p.full_name} (@{p.username})"} for p in patients]
    return JsonResponse({'patients': data})


def all_patients_api(request):
    """Return all patients alphabetically for the dropdown list."""
    if not request.user.is_authenticated or request.user.role != 'doctor':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    patients = User.objects.filter(role='patient').order_by('first_name', 'last_name', 'username')
    data = [{'id': p.id, 'username': p.username, 'name': p.full_name, 'display': f"{p.full_name} (@{p.username})"} for p in patients]
    return JsonResponse({'patients': data})


@doctor_required
def administer_drug(request):
    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        drug_ids = request.POST.getlist('drug_ids')
        dosages = request.POST.getlist('dosages')
        doctor_note = request.POST.get('doctor_note', '')

        if not patient_id or not drug_ids:
            messages.error(request, 'Please select a patient and at least one drug.')
            return redirect('doctor_dashboard')

        patient = get_object_or_404(User, id=patient_id, role='patient')

        # Create one session for this entire prescription
        session = AdministrationSession.objects.create(
            patient=patient,
            doctor=request.user,
            doctor_note=doctor_note,
            status='pending'
        )

        created_count = 0
        for i, drug_id in enumerate(drug_ids):
            try:
                drug = Drug.objects.get(id=drug_id)
                dosage = dosages[i] if i < len(dosages) else ''
                SessionDrug.objects.create(session=session, drug=drug, dosage=dosage)
                created_count += 1
            except Drug.DoesNotExist:
                pass

        if created_count:
            messages.success(request, f'Session created: {created_count} drug(s) prescribed to {patient.full_name}.')
        else:
            session.delete()
            messages.error(request, 'No valid drugs found. Please try again.')

    return redirect('doctor_dashboard')
