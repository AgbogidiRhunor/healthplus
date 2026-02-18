# 🏥 Health Plus – Django Application

A healthcare management system for Patients, Doctors, and Pharmacists.

---

## 📁 Project Structure

```
health_plus/
├── health_plus/          # Project settings & config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── management/           # Authentication + user roles
│   ├── models.py         # Custom User model with roles
│   ├── views.py          # Login, signup, dashboards
│   ├── forms.py          # Signup form
│   ├── admin.py          # Admin panel config
│   └── urls.py
├── pharmacy/             # Drug inventory
│   ├── models.py         # Drug model
│   ├── views.py          # CRUD + drug search API
│   └── urls.py
├── records/              # Drug administration sessions
│   ├── models.py         # DrugAdministration model
│   ├── views.py          # Administer drugs, patient search
│   └── urls.py
├── templates/            # 4 HTML dashboards
│   ├── login.html
│   ├── signup.html
│   ├── patient.html
│   ├── doctor.html
│   └── pharmacist.html
├── requirements.txt
├── setup.sh              # One-command setup
└── manage.py
```

---

## 🚀 Quick Setup

### Prerequisites
- Python 3.8+
- pip

### 1. Run the setup script
```bash
cd health_plus
bash setup.sh
```
This will:
- Install Django
- Run database migrations
- Create a superuser (admin account)
- Load 10 sample drugs

### 2. Start the server
```bash
python manage.py runserver
```

### 3. Open your browser
- **App:** http://localhost:8000/
- **Admin panel:** http://localhost:8000/admin/

---

## 👥 User Roles & Flow

### 🧑‍💼 Patients
- Sign up → **immediately** can log in
- Dashboard shows:
  - Medical profile (all info filled during signup)
  - Full drug record history with status badges (⏳ Pending / ✅ Administered / ❌ Rejected)

### 👨‍⚕️ Doctors
- Sign up → see "Waiting for admin approval" message
- Admin must go to `/admin/` → Users → find the doctor → tick `Is approved` → Save
- Once approved, can log in
- Dashboard:
  - Search for any patient by name or username
  - Search drugs with live autocomplete
  - Select multiple drugs, set dosage per drug
  - Add an optional note for the pharmacist
  - Submit → creates pending record(s) on pharmacist's queue

### 💊 Pharmacists
- Same approval process as Doctors
- Dashboard has two tabs:
  1. **Pending Prescriptions** – see all pending drug administrations with doctor's note, mark each as Administered or Rejected (with optional pharmacist note)
  2. **Drug Inventory** – add, edit, delete drugs in the system

---

## ⚙️ Approving Doctors & Pharmacists (Admin)

1. Go to http://localhost:8000/admin/
2. Log in with your superuser credentials
3. Click **Users** under the **Management** section
4. Find the doctor/pharmacist account
5. Click on their name → check the **Is approved** checkbox → Save
6. They can now log in

**Quick way:** In the Users list view, you can directly tick the `Is approved` column inline and save.

---

## 🔄 Full Application Flow

```
Doctor logs in
  → Searches patient by name
  → Selects patient
  → Searches + selects drugs (with dosage)
  → Adds optional note for pharmacist
  → Submits

Pharmacist logs in
  → Sees pending prescription(s) in queue
  → Reads doctor's note
  → Marks as "Administered" or "Rejected" + optional pharmacist note

Patient logs in
  → Sees drug in records with:
     - ⏳ Pending  (before pharmacist action)
     - ✅ Administered  (after pharmacist approves)
     - ❌ Rejected  (after pharmacist rejects)
```

---

## 🛠 Technical Notes

- **Auth:** Custom `User` model extending `AbstractUser` with `role` + `is_approved` fields
- **Database:** SQLite (default) — easy to switch to PostgreSQL via `settings.py`
- **Login redirect:** Automatically routes to the correct dashboard based on role
- **Drug search API:** `/pharmacy/api/drugs/?q=` — JSON endpoint for doctor's live drug search
- **Patient search API:** `/records/api/patient-search/?q=` — JSON endpoint for doctor's patient search

---

## 🔮 Features to Add Later
- Email notifications (Django + SMTP)
- Drug stock tracking (quantity field on Drug model)
- PDF medical report export
- Audit logs (django-auditlog)
- REST API (Django REST Framework)
