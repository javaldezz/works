from django import forms
from .models import MenuItemT
from decimal import Decimal, ROUND_DOWN

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItemT
        fields = ["menu_item_name", "menu_item_price", "menu_item_cost", "item_availability_status"]
        widgets = {
            "menu_item_name": forms.TextInput(attrs={"class": "input-field", "placeholder": "Enter menu item name"}),
            "menu_item_price": forms.NumberInput(attrs={"class": "input-field", "placeholder": "Enter price", "min": "0", "step": "0.01"}),
            "menu_item_cost": forms.NumberInput(attrs={"class": "input-field", "placeholder": "Enter cost", "min": "0", "step": "0.01"}),
            "item_availability_status": forms.Select(choices=[
                (1, "For Sale"), 
                (0, "Discontinued")
            ], attrs={"class": "availability-dropdown"})
        }

    def clean_menu_item_price(self):
        price = self.cleaned_data.get("menu_item_price")
        if price is not None:
            if price < 0:
                raise forms.ValidationError("Price must be a positive number.")
            return Decimal(price).quantize(Decimal("0.01"), rounding=ROUND_DOWN)  # ✅ Enforces 2 decimal places
        return price

    def clean_menu_item_cost(self):
        cost = self.cleaned_data.get("menu_item_cost")
        if cost is not None:
            if cost < 0:
                raise forms.ValidationError("Cost must be a positive number.")
            return Decimal(cost).quantize(Decimal("0.01"), rounding=ROUND_DOWN)  # ✅ Enforces 2 decimal places
        return cost
