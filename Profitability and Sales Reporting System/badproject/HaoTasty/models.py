from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.core.validators import MinValueValidator
from decimal import Decimal

class ExpenseCatT(models.Model):
    expense_cat_id = models.AutoField(primary_key=True)
    expense_cat_name = models.CharField(max_length=50)
    category_timestamp = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'expense_cat_t'

class ExpenseT(models.Model):
    expense_id = models.AutoField(primary_key=True)
    expense_cat = models.ForeignKey(ExpenseCatT, models.CASCADE,  db_column="expense_cat")
    expense_date = models.DateField()
    expense_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('1.00'))])
    expense_name = models.CharField(max_length=255)
    expense_timestamp = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'expense_t'

class MenuItemT(models.Model):
    menu_item_id = models.AutoField(primary_key=True)
    menu_item_name = models.CharField(max_length=100)
    menu_item_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('1.00'))])
    menu_item_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(Decimal('0.00'))])
    menu_item_profit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    menu_item_timestamp = models.DateTimeField(auto_now_add=True)
    item_availability_status = models.IntegerField()
    menu_item_type = models.CharField(max_length=20, default='Main')

    def __str__(self):
        return self.menu_item_name

    def save(self, *args, **kwargs):
        self.menu_item_profit = float(self.menu_item_price) - float(self.menu_item_cost)
        super().save(*args, **kwargs)

    class Meta:
        managed = True
        db_table = 'menu_item_t'


class OrderT(models.Model):
    order_id = models.AutoField(primary_key=True)
    payment_type = models.CharField(max_length=20)
    order_timestamp = models.DateTimeField()
    reference_num = models.CharField(max_length=100, blank=True, null=True)
    order_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'order_t'

class OrderLineT(models.Model):
    order_line_id = models.AutoField(primary_key=True)
    menu_item = models.ForeignKey(MenuItemT, models.DO_NOTHING)
    order = models.ForeignKey(OrderT, models.DO_NOTHING)
    order_quantity = models.IntegerField()
    order_subtotal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'order_line_t'

class UserT(models.Model):
    user_id = models.AutoField(primary_key=True)
    user_added_by = models.ForeignKey(User, on_delete=models.SET_NULL, db_column='user_added_by', blank=True, null=True)
    django_user = models.OneToOneField(User, 
                                       on_delete=models.CASCADE,
                                       related_name='usert_profile',
                                       db_column='django_user_id')  # Unique related_name) 
    ## No need to enforce uniqueness because we are extending from Django's User model, which does that for us
    user_type = models.CharField(max_length=13, 
                                 choices=[("Administrator", "Administrator"), ("Employee", "Employee")])
    user_timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return self.user.username

    class Meta:
        managed = True
        db_table = 'user_t'

    ## Final model