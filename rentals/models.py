from django.db import models
from django.conf import settings
from django.utils import timezone
from games.models import Game
import uuid

class Rental(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    # Who approved this rental
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rentals_approved"
    )

    # Phase 2 fields
    rental_days = models.PositiveIntegerField(default=7)
    cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # 💰 Mock Payment Fields
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    transaction_id = models.CharField(max_length=50, null=True, blank=True)

    def calculate_cost(self):
        """Calculate total rental cost"""
        return self.rental_days * self.game.price_per_day

    def save(self, *args, **kwargs):
        # Auto-calc cost before saving
        if self.status == 'approved' and (self.cost is None or self.cost == 0):
            self.cost = self.calculate_cost()
            if not self.approved_at:
                self.approved_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.game.title} ({self.status})"

