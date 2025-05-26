from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ExpenseCatT, ExpenseT, MenuItemT, OrderT, OrderLineT, UserT

admin.site.register(ExpenseCatT)
admin.site.register(ExpenseT)
admin.site.register(MenuItemT)
admin.site.register(OrderT)
admin.site.register(OrderLineT)
admin.site.register(UserT)

