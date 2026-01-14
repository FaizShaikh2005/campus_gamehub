from django import forms

class RentalRequestForm(forms.Form):
    rental_days = forms.IntegerField(
        min_value=1,
        max_value=30,
        initial=3,
        label="Number of days",
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )
