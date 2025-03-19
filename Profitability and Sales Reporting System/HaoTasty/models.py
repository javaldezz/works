from django.db import models

class ExpenseCatT(models.Model):
    expense_cat_id = models.AutoField(primary_key=True)
    expense_cat_name = models.CharField(max_length=50)
    category_timestamp = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'expense_cat_t'

class ExpenseT(models.Model):
    expense_id = models.AutoField(primary_key=True)
    expense_cat = models.ForeignKey(ExpenseCatT, models.DO_NOTHING)
    expense_date = models.DateField()
    expense_amount = models.JSONField()
    expense_name = models.CharField(max_length=255)
    expense_timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'expense_t'

class MenuItemT(models.Model):
    menu_item_id = models.AutoField(primary_key=True)
    menu_item_name = models.CharField(max_length=100)
    menu_item_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    menu_item_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    menu_item_timestamp = models.DateTimeField(auto_now=True)
    menu_item_profit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, editable=False)
    item_availability_status = models.IntegerField(choices=[(1, "For Sale"), (0, "Discontinued")], default=1)

    def __str__(self):
        return self.menu_item_name
    
    def save(self, *args, **kwargs):
        if self.pk is not None:  # Update Menu Item
            super().save(update_fields=["menu_item_name", "menu_item_price", "menu_item_cost", "menu_item_timestamp", "item_availability_status"])
        else: # Create Menu Item
            super().save(*args, **kwargs)

    class Meta:
        managed = True
        db_table = 'menu_item_t'

class OrderT(models.Model):
    order_id = models.AutoField(primary_key=True)
    payment_type = models.CharField(max_length=20)
    order_timestamp = models.DateTimeField()
    reference_num = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order_t'

class OrderLineT(models.Model):
    order_line_id = models.AutoField(primary_key=True)
    menu_item = models.ForeignKey(MenuItemT, models.DO_NOTHING)
    order = models.ForeignKey(OrderT, models.DO_NOTHING)
    order_quantity = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'order_line_t'

class UserT(models.Model):
    user_id = models.AutoField(primary_key=True)
    user_added_by = models.ForeignKey('self', models.DO_NOTHING, db_column='user_added_by', blank=True, null=True)
    username = models.CharField(unique=True, max_length=50)
    user_password = models.CharField(max_length=255)
    user_first_name = models.CharField(max_length=50)
    user_last_name = models.CharField(max_length=50)
    user_type = models.CharField(max_length=13)
    user_timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'user_t'