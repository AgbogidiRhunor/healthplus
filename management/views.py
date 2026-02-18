from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from .forms import SignupForm


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            role = form.cleaned_data['role']
            user.role = role
            if role == 'patient':
                user.is_approved = True
            else:
                user.is_approved = False
            user.save()

            if role == 'patient':
                login(request, user)
                messages.success(request, f'Welcome, {user.first_name}! Your account has been created.')
                return redirect('dashboard')
            else:
                messages.info(request, f'Your {role} account has been submitted. Please wait for admin approval before logging in.')
                return redirect('login')
    else:
        form = SignupForm()

    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if not user.can_login:
                messages.warning(request, 'Your account is awaiting admin approval. Please check back later.')
                return redirect('login')
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')


@login_required
def dashboard_view(request):
    user = request.user
    if user.role == 'patient':
        return redirect('patient_dashboard')
    elif user.role == 'doctor':
        return redirect('doctor_dashboard')
    elif user.role == 'pharmacist':
        return redirect('pharmacist_dashboard')
    return redirect('login')


@login_required
def patient_dashboard(request):
    if request.user.role != 'patient':
        return redirect('dashboard')

    from records.models import AdministrationSession
    sessions = AdministrationSession.objects.filter(patient=request.user).prefetch_related('drugs__drug').order_by('-created_at')
    total = sessions.count()
    pending = sessions.filter(status='pending').count()
    administered = sessions.filter(status='administered').count()
    return render(request, 'patient.html', {
        'sessions': sessions,
        'total': total,
        'pending': pending,
        'administered': administered,
    })


@login_required
def doctor_dashboard(request):
    if request.user.role != 'doctor':
        return redirect('dashboard')

    patients = User.objects.filter(role='patient').order_by('first_name', 'last_name', 'username')
    from pharmacy.models import Drug
    drugs = Drug.objects.all().order_by('name')
    return render(request, 'doctor.html', {'patients': patients, 'drugs': drugs})


@login_required
def pharmacist_dashboard(request):
    if request.user.role != 'pharmacist':
        return redirect('dashboard')

    from records.models import AdministrationSession
    from pharmacy.models import Drug
    pending = AdministrationSession.objects.filter(status='pending').prefetch_related('drugs__drug').select_related('patient', 'doctor').order_by('-created_at')
    drugs = Drug.objects.all().order_by('name')
    active_tab = request.GET.get('tab', 'pending')
    return render(request, 'pharmacist.html', {'pending_sessions': pending, 'drugs': drugs, 'active_tab': active_tab})
