from django import forms
from .models import Game

class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['title', 'description', 'image', 'available', 'price_per_day']
        widgets = {
            'price_per_day': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '1'}),
        }
        labels = {
            'price_per_day': 'Price per day (₹)',
        }

# from django import forms
# from .models import Game

# class GameForm(forms.ModelForm):
#     class Meta:
#         model = Game
#         fields = ['title', 'description', 'image', 'available']
