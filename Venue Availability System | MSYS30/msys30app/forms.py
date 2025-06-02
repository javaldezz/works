from django import forms # type: ignore | imports the library

class VenueAvailabilityForm(forms.Form):
    capacity = forms.IntegerField(
        min_value=1,  
        required=False,  
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )

    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    target_time = forms.ChoiceField(
        choices=[
            ("08:00 - 09:30", "08:00 - 09:30"),
            ("09:30 - 11:00", "09:30 - 11:00"),
            ("11:00 - 12:30", "11:00 - 12:30"),
            ("12:30 - 14:00", "12:30 - 14:00"),
            ("14:00 - 15:30", "14:00 - 15:30"),
            ("15:30 - 17:00", "15:30 - 17:00"),
            ("17:00 - 18:30", "17:00 - 18:30"),
            ("18:30 - 20:00", "18:30 - 20:00"),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ("capacity", "Capacity"),
            ("venue_name", "Venue ID"),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
 
    order = forms.ChoiceField(
        choices=[
            ("Ascending", "Ascending"),
            ("Descending", "Descending"),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
