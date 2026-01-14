# rentals/admin.py
from django.contrib import admin
from .models import Rental

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'status', 'requested_at', 'approved_at')
    list_filter = ('status',)
    actions = ['approve_rentals', 'deny_rentals']

    def approve_rentals(self, request, queryset):
        queryset.update(status='approved')
        for rental in queryset:
            rental.game.available = False
            rental.game.save()
    approve_rentals.short_description = "Approve selected rentals"

    def deny_rentals(self, request, queryset):
        queryset.update(status='denied')
    deny_rentals.short_description = "Deny selected rentals"
