from django.contrib import admin
from .models import Game

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('title', 'available')
    list_filter = ('available',)
    search_fields = ('title',)
