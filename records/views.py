from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from management.models import User
from pharmacy.models import Drug
from .models import AdministrationSession, SessionDrug
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

def doctor_required(func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'doctor':
            messages.error(request, 'Access denied.')
            return redirect('login')
        return func(request, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


def patient_required(func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'patient':
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
    if not request.user.is_authenticated or request.user.role != 'doctor':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    patients = User.objects.filter(role='patient').order_by('first_name', 'last_name', 'username')
    data = [{'id': p.id, 'username': p.username, 'name': p.full_name, 'display': f"{p.full_name} (@{p.username})"} for p in patients]
    return JsonResponse({'patients': data})


def patient_records_api(request, patient_id):
    """Returns a patient's full session history as JSON for the doctor modal."""
    if not request.user.is_authenticated or request.user.role != 'doctor':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    patient = get_object_or_404(User, id=patient_id, role='patient')
    sessions = AdministrationSession.objects.filter(patient=patient).prefetch_related('drugs__drug').select_related('doctor').order_by('-created_at')

    data = []
    for i, s in enumerate(sessions):
        data.append({
            'id': s.id,
            'session_num': sessions.count() - i,
            'status': s.status,
            'created_at': s.created_at.strftime('%b %d, %Y at %I:%M %p'),
            'doctor': s.doctor.full_name if s.doctor else 'Unknown',
            'doctor_note': s.doctor_note,
            'pharmacist_note': s.pharmacist_note,
            'drugs': [
                {
                    'name': e.drug.name,
                    'strength': e.drug.strength,
                    'dosage_form': e.drug.dosage_form,
                    'dosage': e.dosage,
                }
                for e in s.drugs.all()
            ]
        })
    return JsonResponse({'patient': {'name': patient.full_name, 'username': patient.username}, 'sessions': data})


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


@patient_required
def download_medical_record(request):

    user = request.user
    sessions = AdministrationSession.objects.filter(patient=user).prefetch_related('drugs__drug').select_related('doctor').order_by('-created_at')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm)

    primary = colors.HexColor('#0ea5e9')
    light_bg = colors.HexColor('#f0f9ff')
    muted = colors.HexColor('#64748b')
    border = colors.HexColor('#e2e8f0')
    pending_bg = colors.HexColor('#fef9c3')
    pending_fg = colors.HexColor('#92400e')
    admin_bg = colors.HexColor('#d1fae5')
    admin_fg = colors.HexColor('#065f46')
    reject_bg = colors.HexColor('#fee2e2')
    reject_fg = colors.HexColor('#b91c1c')
    note_doc_bg = colors.HexColor('#fffbeb')
    note_phar_bg = colors.HexColor('#f0fdf4')

    styles = getSampleStyleSheet()
    story = []

    # ── Header ──
    header_data = [[
        Paragraph('<font color="#0ea5e9"><b>Health Plus</b></font>', ParagraphStyle('h', fontSize=20, fontName='Helvetica-Bold')),
        Paragraph('<font color="#64748b">Medical Record — Confidential</font>', ParagraphStyle('s', fontSize=9, fontName='Helvetica', alignment=2))
    ]]
    header_table = Table(header_data, colWidths=['60%', '40%'])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 1.5, primary),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10*mm))

    # ── Section label helper ──
    def section_label(text):
        return Paragraph(f'<font color="#0ea5e9"><b>{text}</b></font>',
            ParagraphStyle('sl', fontSize=9, fontName='Helvetica-Bold', spaceBefore=4, spaceAfter=4))

    def field_row(label, value):
        return [
            Paragraph(f'<font color="#64748b"><b>{label}</b></font>',
                ParagraphStyle('lbl', fontSize=8, fontName='Helvetica-Bold')),
            Paragraph(str(value) if value else '—',
                ParagraphStyle('val', fontSize=9, fontName='Helvetica'))
        ]

    # ── Patient Info ──
    story.append(section_label('PATIENT INFORMATION'))
    story.append(HRFlowable(width='100%', thickness=0.5, color=border, spaceAfter=6))

    info_data = [
        field_row('Full Name', user.full_name),
        field_row('Username', f'@{user.username}'),
        field_row('Date of Birth', user.date_of_birth or 'Not provided'),
        field_row('Gender', user.gender.capitalize() if user.gender else 'Not provided'),
        field_row('Blood Group', user.blood_group or 'Not provided'),
        field_row('Phone', user.phone or 'Not provided'),
        field_row('Address', user.address or 'Not provided'),
        field_row('Allergies', user.allergies or 'None'),
        field_row('Medical Conditions', user.medical_conditions or 'None'),
    ]
    info_table = Table(info_data, colWidths=['35%', '65%'])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), light_bg),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0,0), (-1,-1), 0.3, border),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8*mm))

    # ── Medical Records ──
    story.append(section_label('MEDICAL RECORDS'))
    story.append(HRFlowable(width='100%', thickness=0.5, color=border, spaceAfter=6))

    if not sessions:
        story.append(Paragraph('No medical records found.', ParagraphStyle('e', fontSize=9, textColor=muted)))
    else:
        total = sessions.count()
        for i, session in enumerate(sessions):
            session_num = total - i
            if session.status == 'pending':
                status_text, s_bg, s_fg = 'Pending', pending_bg, pending_fg
            elif session.status == 'administered':
                status_text, s_bg, s_fg = 'Administered', admin_bg, admin_fg
            else:
                status_text, s_bg, s_fg = 'Rejected', reject_bg, reject_fg

            doctor_name = session.doctor.full_name if session.doctor else 'Unknown'
            date_str = session.created_at.strftime('%B %d, %Y at %I:%M %p')

            # Session header row
            session_header = Table([[
                Paragraph(f'<b>Session #{session_num}</b> &nbsp;·&nbsp; {session.drug_count} drug{"s" if session.drug_count != 1 else ""}',
                    ParagraphStyle('sh', fontSize=9, fontName='Helvetica-Bold')),
                Paragraph(f'Dr. {doctor_name} · {date_str}',
                    ParagraphStyle('sm', fontSize=8, textColor=muted)),
                Paragraph(f'<b>{status_text}</b>',
                    ParagraphStyle('sb', fontSize=8, fontName='Helvetica-Bold', textColor=s_fg, alignment=2)),
            ]], colWidths=['30%', '50%', '20%'])
            session_header.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
                ('GRID', (0,0), (-1,-1), 0.3, border),
                ('PADDING', (0,0), (-1,-1), 6),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BACKGROUND', (2,0), (2,0), s_bg),
            ]))
            story.append(session_header)

            # Drugs
            for entry in session.drugs.all():
                drug_str = entry.drug.name
                if entry.drug.strength:
                    drug_str += f' – {entry.drug.strength}'
                if entry.drug.dosage_form:
                    drug_str += f' ({entry.drug.dosage_form})'
                dosage_str = entry.dosage or ''
                drug_row_table = Table([[
                    Paragraph(f'&#9670; &nbsp;{drug_str}',
                        ParagraphStyle('dr', fontSize=9, fontName='Helvetica-Bold')),
                    Paragraph(dosage_str,
                        ParagraphStyle('dd', fontSize=8, textColor=muted, alignment=2)),
                ]], colWidths=['70%', '30%'])
                drug_row_table.setStyle(TableStyle([
                    ('GRID', (0,0), (-1,-1), 0.3, border),
                    ('PADDING', (0,0), (-1,-1), 5),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ]))
                story.append(drug_row_table)

            # Notes
            if session.doctor_note:
                note = Table([[Paragraph(f"<b>Doctor's Note:</b> {session.doctor_note}",
                    ParagraphStyle('dn', fontSize=8, fontName='Helvetica'))]],
                    colWidths=['100%'])
                note.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), note_doc_bg),
                    ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#fde68a')),
                    ('PADDING', (0,0), (-1,-1), 5),
                ]))
                story.append(note)

            if session.pharmacist_note:
                note = Table([[Paragraph(f"<b>Pharmacist's Note:</b> {session.pharmacist_note}",
                    ParagraphStyle('pn', fontSize=8, fontName='Helvetica'))]],
                    colWidths=['100%'])
                note.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), note_phar_bg),
                    ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#86efac')),
                    ('PADDING', (0,0), (-1,-1), 5),
                ]))
                story.append(note)

            story.append(Spacer(1, 4*mm))

    # ── Footer ──
    story.append(HRFlowable(width='100%', thickness=0.5, color=border, spaceBefore=4))
    story.append(Paragraph(
        f'Generated on {timezone.now().strftime("%B %d, %Y at %I:%M %p")} &nbsp;·&nbsp; Health Plus &nbsp;·&nbsp; Confidential',
        ParagraphStyle('footer', fontSize=8, textColor=muted, alignment=TA_CENTER, spaceBefore=4)
    ))

    doc.build(story)
    buffer.seek(0)

    filename = f'medical_record_{user.username}_{timezone.now().strftime("%Y%m%d")}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def patient_records_api(request, patient_id):
    """Return a patient's full session history as JSON — for the doctor modal."""
    if not request.user.is_authenticated or request.user.role != 'doctor':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    patient = get_object_or_404(User, id=patient_id, role='patient')
    sessions = AdministrationSession.objects.filter(patient=patient).prefetch_related('drugs__drug').select_related('doctor').order_by('-created_at')

    data = []
    for i, s in enumerate(sessions):
        data.append({
            'session_num': sessions.count() - i,
            'date': s.created_at.strftime('%b %d, %Y'),
            'time': s.created_at.strftime('%I:%M %p'),
            'doctor': s.doctor.full_name if s.doctor else '—',
            'status': s.status,
            'doctor_note': s.doctor_note,
            'pharmacist_note': s.pharmacist_note,
            'drugs': [
                {
                    'name': sd.drug.name,
                    'strength': sd.drug.strength,
                    'dosage_form': sd.drug.dosage_form,
                    'dosage': sd.dosage,
                }
                for sd in s.drugs.all()
            ]
        })

    return JsonResponse({
        'patient': {'name': patient.full_name, 'username': patient.username},
        'sessions': data
    })
