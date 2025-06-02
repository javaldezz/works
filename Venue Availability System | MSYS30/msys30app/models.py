from django.db import models  # type: ignore
from django.core.exceptions import ValidationError # type: ignore

TIME_SLOTS = [
    ("08:00 - 09:30", "08:00 - 09:30"),
    ("09:30 - 11:00", "09:30 - 11:00"),
    ("11:00 - 12:30", "11:00 - 12:30"),
    ("12:30 - 14:00", "12:30 - 14:00"),
    ("14:00 - 15:30", "14:00 - 15:30"),
    ("15:30 - 17:00", "15:30 - 17:00"),
    ("17:00 - 18:30", "17:00 - 18:30"),
    ("18:30 - 20:00", "18:30 - 20:00"),
]

class Venues(models.Model):
    venue_name = models.CharField(max_length=100, help_text="Name of the venue.")
    capacity = models.PositiveIntegerField(help_text="Capacity of the venue.")

    class Meta:
        verbose_name = "Venue"
        verbose_name_plural = "Venues"
        ordering = ["venue_name"]

    def __str__(self):
        return self.venue_name


class Reservations(models.Model):
    venue_name = models.ForeignKey("Venues", on_delete=models.CASCADE, null=True, blank=True, help_text="Select a venue (optional).")
    reservation_date = models.DateField(help_text="Reservation date in YYYY-MM-DD format.")
    target_time = models.CharField(max_length=15, choices=TIME_SLOTS, help_text="Select a time slot for the reservation.")

    class Meta:
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"
        ordering = ["reservation_date", "target_time"]

    def __str__(self):
        return f"{self.venue_name} on {self.reservation_date} at {self.target_time}"


class UserInput(models.Model):
    building = models.CharField(max_length=100, choices=[("Faura", "Faura")], null=True, blank=True, help_text="Building name where the venue is located.")
    venue_name = models.ForeignKey("Venues", on_delete=models.CASCADE, help_text="Select the venue for the reservation.", null=True, blank=True)
    reservation_date = models.DateField(help_text="Reservation date in YYYY-MM-DD format.", null=True, blank=True)
    target_time = models.CharField(max_length=15, choices=TIME_SLOTS, help_text="Select a start time for the reservation.", null=True, blank=True)
    capacity = models.PositiveIntegerField(help_text="Enter the capacity needed for the venue.", null=True, blank=True)
    
    class Meta:
        verbose_name = "User Input"
        verbose_name_plural = "User Inputs"
        ordering = ["reservation_date", "target_time"]

    def __str__(self):
        return f"Reservation request for {self.venue_name} on {self.reservation_date} at {self.target_time}"
