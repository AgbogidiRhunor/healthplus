from django.db import models


class Drug(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    dosage_form = models.CharField(max_length=100, blank=True, help_text="e.g. Tablet, Capsule, Injection")
    strength = models.CharField(max_length=100, blank=True, help_text="e.g. 500mg, 10mg/ml")
    manufacturer = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        parts = [self.name]
        if self.strength:
            parts.append(self.strength)
        if self.dosage_form:
            parts.append(self.dosage_form)
        return ' - '.join(parts)
