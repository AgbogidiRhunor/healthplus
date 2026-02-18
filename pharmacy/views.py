from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import Drug
from records.models import AdministrationSession


def pharmacist_required(func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'pharmacist':
            messages.error(request, 'Access denied.')
            return redirect('login')
        return func(request, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


@pharmacist_required
def add_drug(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Drug name is required.')
        else:
            Drug.objects.create(
                name=name,
                description=request.POST.get('description', ''),
                dosage_form=request.POST.get('dosage_form', ''),
                strength=request.POST.get('strength', ''),
                manufacturer=request.POST.get('manufacturer', ''),
            )
            messages.success(request, f'Drug "{name}" added successfully.')
    # Stay on drugs tab
    return redirect('/pharmacist/dashboard/?tab=drugs')


@pharmacist_required
def edit_drug(request, drug_id):
    drug = get_object_or_404(Drug, id=drug_id)
    if request.method == 'POST':
        drug.name = request.POST.get('name', drug.name).strip()
        drug.description = request.POST.get('description', drug.description)
        drug.dosage_form = request.POST.get('dosage_form', drug.dosage_form)
        drug.strength = request.POST.get('strength', drug.strength)
        drug.manufacturer = request.POST.get('manufacturer', drug.manufacturer)
        drug.save()
        messages.success(request, f'Drug "{drug.name}" updated.')
    return redirect('/pharmacist/dashboard/?tab=drugs')


@pharmacist_required
def delete_drug(request, drug_id):
    drug = get_object_or_404(Drug, id=drug_id)
    if request.method == 'POST':
        name = drug.name
        drug.delete()
        messages.success(request, f'Drug "{name}" deleted.')
    return redirect('/pharmacist/dashboard/?tab=drugs')


@pharmacist_required
def update_session_status(request, session_id):
    if request.method == 'POST':
        session = get_object_or_404(AdministrationSession, id=session_id)
        status = request.POST.get('status')
        if status in ['administered', 'rejected']:
            session.status = status
            session.pharmacist_note = request.POST.get('pharmacist_note', '')
            session.save()
            messages.success(request, f'Session marked as {status}.')
    return redirect('pharmacist_dashboard')


def drug_search_api(request):
    """JSON API for doctor drug search."""
    if not request.user.is_authenticated or request.user.role != 'doctor':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    query = request.GET.get('q', '').strip()
    drugs = Drug.objects.all().order_by('name')
    if query:
        drugs = drugs.filter(name__icontains=query)
    drugs = drugs[:20]
    data = [{'id': d.id, 'name': d.name, 'strength': d.strength, 'dosage_form': d.dosage_form, 'display': str(d)} for d in drugs]
    return JsonResponse({'drugs': data})
