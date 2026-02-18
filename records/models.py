from django.db import models
from django.conf import settings


class AdministrationSession(models.Model):
    """
    One session = one visit/prescription by a doctor for a patient.
    Multiple drugs can be administered under a single session.
    The pharmacist approves/rejects the entire session at once.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('administered', 'Administered'),
        ('rejected', 'Rejected'),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='doctor_sessions'
    )
    doctor_note = models.TextField(blank=True, help_text="Note for the pharmacist")
    pharmacist_note = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Session #{self.id} - {self.patient.username} [{self.status}]"

    @property
    def drug_count(self):
        return self.drugs.count()


class SessionDrug(models.Model):
    """A single drug entry within a session."""
    session = models.ForeignKey(
        AdministrationSession,
        on_delete=models.CASCADE,
        related_name='drugs'
    )
    drug = models.ForeignKey(
        'pharmacy.Drug',
        on_delete=models.PROTECT,
        related_name='session_entries'
    )
    dosage = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.drug.name} ({self.dosage or 'no dosage'})"
