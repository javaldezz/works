from django.db import transaction, connection
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.db.models import Sum, Count, F, ExpressionWrapper, FloatField, Value
from .models import ExpenseCatT, ExpenseT, MenuItemT, OrderLineT, OrderT, UserT
from django.utils import timezone
from datetime import datetime
from datetime import timedelta
from django.contrib import messages, sessions 
from django.db.models import Prefetch
from itertools import combinations
from collections import Counter
from decimal import Decimal
from django.utils.timezone import now
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear, Coalesce, Cast
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password
from functools import wraps
import numpy as np
from prophet import Prophet
from django.db.models import DecimalField, ExpressionWrapper
from collections import defaultdict
from django.http import JsonResponse
import pandas as pd 
import re
from django.core import management
from django.conf import settings
import io, os, json
from django.views.decorators.http import require_POST
from django.http import FileResponse, Http404
from django.utils.encoding import smart_str




# login authentication
from django.contrib.auth import authenticate, login, logout
# using this so that django can check if the user has authority to access certain pages
from django.contrib.auth.decorators import login_required

def superuser_required(view_func):
    """
    Decorator to restrict view access to only superusers.
    """
    def check_superuser(user):
        if not user.is_authenticated:
            return False  # Prevents anonymous users from passing the check
        return user.is_superuser
    return user_passes_test(check_superuser, login_url='login_user')(view_func)

def login_user(request): # logging in
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('landingpage') # if admin, go to reports landing page
        else:
            return redirect('order_input') # if not admin, go to order input page

    if request.method == 'POST':
        username = request.POST.get('username') # get username from login screen
        password = request.POST.get('password') # get inputted password

        ## This uses the built-in Django authentication module to check
        ## if the password is really the password of that user
        user = authenticate(request, username=username, password=password)

        ## This checks if the user exists or not
        if user is not None:
            login(request, user)
            return login_redirect(request)
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'HaoTasty/login.html')

def login_redirect(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('landingpage') # if admin, go to reports landing page
        else:
            return redirect('order_input') # if not admin, go to order input page
    messages.error(request, 'Invalid username or password')
    return render(request, 'HaoTasty/login.html') # if not authenticated, return to login screen

@login_required(login_url='login_user')
def logout_user(request): # logging out
    logout(request)
    return redirect('login_user')

@login_required(login_url='login_user')
def sales_list(request):
    sales = OrderT.objects.prefetch_related(
        Prefetch('orderlinet_set', queryset=OrderLineT.objects.select_related('menu_item'))
    ).order_by('-order_timestamp')

    today = datetime.today().date()
    is_admin = request.user.is_superuser # Check if user is an admin
    template = 'HaoTasty/sales_list.html' if is_admin else 'HaoTasty/sales_list_employee.html'
    
    # GET: Paginate results
    paginator = Paginator(sales, 50)  # Show 50 sales per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context ={
        "today":today,
        "page_obj":page_obj
    }

    return render(request, template, context)

@login_required(login_url='login_user')
def expense_list(request):
    # Load existing expenses and categories
    expense_objects = ExpenseT.objects.all().order_by('-expense_date')
    expense_cat_objects = ExpenseCatT.objects.all()
    is_admin = request.user.is_superuser # Check if user is an admin
    template = 'HaoTasty/expense_list_admin.html' if is_admin else 'HaoTasty/expense_list.html'
    
    # GET: Paginate results
    paginator = Paginator(expense_objects, 20)  # Show 20 expenses per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    if request.method == "POST":
        # Get data from form
        expense_ids = request.POST.getlist("expense_id[]")  # Hidden input for existing expense IDs
        dates = request.POST.getlist("expense_date[]")
        amounts = request.POST.getlist("expense_amount[]")
        names = request.POST.getlist("expense_name[]")
        categories = request.POST.getlist("expense_cat[]")

        # Validate and update expenses
        for i, expense_id in enumerate(expense_ids):
            if not dates[i] or not amounts[i] or not names[i] or not categories[i]:
                messages.error(request, "All fields are required.")
                return redirect("expense_list")

            try:
                # Retrieve the expense instance
                expense = ExpenseT.objects.get(pk=expense_id)
                
                # Check if any fields have changed
                updated = False

                # Convert the form date (string) to a datetime.date object
                form_date = timezone.datetime.strptime(dates[i], "%Y-%m-%d").date()

                if expense.expense_date != form_date:
                    expense.expense_date = dates[i]
                    updated = True
                if float(expense.expense_amount) != float(amounts[i]):
                    expense.expense_amount = float(amounts[i])
                    updated = True
                if expense.expense_name != names[i]:
                    expense.expense_name = names[i]
                    updated = True
                if int(expense.expense_cat.expense_cat_id) != int(categories[i]):
                    try:
                        # Retrieve FK object
                        new_category = ExpenseCatT.objects.get(pk=categories[i]) 
                        expense.expense_cat = new_category # Assign new FK object
                        updated = True
                    except ExpenseCatT.DoesNotExist:
                        messages.error(request, f"Category ID {categories[i]} ({new_category.expense_cat_name}) not found.")

                # Update timestamp only if something was changed
                if updated is True:
                    expense.expense_timestamp = timezone.now()  # Set the current timestamp
                    expense.save()  # Save the updated expense

            except ExpenseT.DoesNotExist:
                messages.error(request, f"Expense ID {expense_id} not found.")
                return redirect("expense_list")
        
        messages.success(request, "Expenses updated successfully.")
        return redirect("expense_list")

    return render(request, template, {'expense_object': expense_objects,
                                'expense_cat_objects': expense_cat_objects,
                                'page_obj': page_obj # for pagination
                                })

@login_required(login_url='login_user')
def delete_expenses(request, expense_id):
    if request.method == "POST":
        expense = get_object_or_404(ExpenseT, pk=expense_id)
        expense.delete()
        messages.success(request, "Expense deleted successfully.")
        return redirect("expense_list")
    else:
        return redirect("expense_list")

@login_required(login_url='login_user')
def input_expenses(request):
    expense_category_objects = ExpenseCatT.objects.all()
    expense_summary = []
    is_admin = request.user.is_superuser # Check if user is an admin
    template = 'HaoTasty/input_expenses_admin.html' if is_admin else 'HaoTasty/input_expenses.html'

    if request.method == "POST":
        expense_names = request.POST.getlist('expense_description[]')
        expense_amounts = request.POST.getlist('expense_amount[]')
        expense_dates = request.POST.getlist('expense_date[]')
        expense_categories = request.POST.getlist('expense_category[]')

        if not (expense_names):
            messages.info(request, 'All fields are required.')
            return render(request, template, {'expense_categ': expense_category_objects})

        for i in range(len(expense_names)):
            new_expense_name = expense_names[i]
            new_expense_amount = float(expense_amounts[i])
            new_expense_date_str = expense_dates[i]
            new_expense_cat_id = expense_categories[i]
            new_expense_timestamp = now()

            # Convert string to datetime.date
            try:
                new_expense_date = datetime.strptime(new_expense_date_str, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid date format. Use YYYY-MM-DD.")
                return render(request, template, {'expense_categ': expense_category_objects})
            
            if new_expense_amount < 1:
                messages.error(request, "Expense amount cannot be less than 0.")
                return render(request, template, {'expense_categ': expense_category_objects})
            
            if new_expense_date > datetime.today().date():
                messages.error(request, "Expense date cannot be set in the future.")
                return render(request, template, {'expense_categ': expense_category_objects})
            
            if len(new_expense_name) > 255:
                messages.error(request, "Expense name cannot be longer than 255 characters.")
                return render(request, template, {'expense_categ': expense_category_objects})

            new_expense_cat = ExpenseCatT.objects.get(expense_cat_id=new_expense_cat_id)
        
            new_expense = ExpenseT.objects.create(
                expense_name = new_expense_name, 
                expense_timestamp = new_expense_timestamp,
                expense_amount = new_expense_amount,
                expense_date = new_expense_date,
                expense_cat = new_expense_cat
                )
        
            expense_summary.append({
            'expense_name': new_expense.expense_name,
            'expense_amount': new_expense.expense_amount,
            'expense_date': new_expense.expense_date,
            'expense_category': new_expense.expense_cat.expense_cat_name,
            })

        messages.success(request, 'Expenses have been created.')
        
    return render(request, template, {'expense_categ': expense_category_objects,
                                    'expense_summary': expense_summary})
@superuser_required
def manage_expense_category(request):
    # Load existing expense category objects
    expense_category_objects = ExpenseCatT.objects.all()
    return render(request, 'HaoTasty/manage_expenses_category.html', {'expense_category': expense_category_objects})

@superuser_required
def delete_expense_category(request, expense_cat_id):
    if request.method == "POST":
        expense_cat = get_object_or_404(ExpenseCatT, pk=expense_cat_id)
        expense_cat.delete()
        messages.success(request, "Expense category deleted successfully.")
        return redirect("update_expense_category")
    else:
        return redirect("update_expense_category")

@superuser_required
def create_expense_category(request):
    # Require the form to have method='POST'
    if request.method == 'POST':
        new_category_name = request.POST.get('category-name')
        new_category_timestamp = now()

        # Make sure all fields are inputed
        if not (new_category_name) or not new_category_name.strip():
            messages.info(request, 'All fields are required.')
            return redirect('create_expense_category')
        
        # Check if the category name already exists
        if ExpenseCatT.objects.filter(expense_cat_name=new_category_name).exists():
            messages.error(request, 'This expense category name already exists.')
            return redirect('create_expense_category')

        # Create new expense category if it doesn't exist
        ExpenseCatT.objects.create(expense_cat_name=new_category_name, category_timestamp = new_category_timestamp)
        messages.success(request, 'Expense Category has been created.')
        return redirect('create_expense_category')
        
    return render(request, 'HaoTasty/create_expense_category.html')

@superuser_required
def update_expense_category(request):
    # Load existing expense categories
    expense_category_objects = ExpenseCatT.objects.all().order_by('-category_timestamp')
    
    if request.method == "POST":
        # Get data from form
        category_ids = request.POST.getlist("expense_cat_id[]")  # Hidden input for existing expense IDs
        categories = request.POST.getlist("categories[]")

        # Validate and update expenses
        for i, category_id in enumerate(category_ids): ## check if an expense category field is empty
            if not categories[i].strip():
                messages.error(request, "All fields are required.")
                return redirect("update_expense_category")

            try:
                # Retrieve the expense category instance
                expense_category = ExpenseCatT.objects.get(pk=category_id)
                
                # Check if any fields have changed
                updated = False

                if expense_category.expense_cat_name != categories[i]:
                    # Check if the new name already exists (exclude the current category)
                    if ExpenseCatT.objects.filter(expense_cat_name=categories[i]).exclude(pk=category_id).exists():
                        messages.error(request, 'This expense category name already exists.')
                        return redirect('update_expense_category')
                    
                    # Update category name if unique
                    expense_category.expense_cat_name = categories[i]
                    updated = True

                # Update timestamp only if something was changed
                if updated is True:
                    expense_category.category_timestamp  = timezone.now()  # Set the current timestamp
                    expense_category.save()  # Save the updated expense

            except ExpenseCatT.DoesNotExist:
                messages.error(request, f"Expense Category ID {category_id} not found.")
                return redirect("update_expense_category")
        
        # messages.success(request, "Expenses updated successfully.")
        return redirect("manage_expense_category")
    
    return render(request, 'HaoTasty/update_expense_category.html', {'categories': expense_category_objects})

@superuser_required
def manage_users(request):
    user_objects = User.objects.all()
    return render(request, 'HaoTasty/users_dashboard.html', {'user_objects': user_objects})

#for editing of pw from employee perspective
def profile_employee(request):
    return redirect('update_users', user_id=request.user.id)

@superuser_required
@transaction.atomic
def add_users(request): 
    if request.method == 'POST':
        username = request.POST.get('username') # get username from login screen
        password = request.POST.get('password') # get inputted password
        confirmpassword = request.POST.get('confirm_password') # get the second password input to check if the pw is the same
        firstname = request.POST.get('first_name') # get the first name
        lastname = request.POST.get('last_name') # get the last name
        usertype = request.POST.get('user_type') # whether user is an admin or employee

        if User.objects.filter(username=username).exists(): # Checks if username exists
            messages.error(request, "Username already exists.")
            return redirect('add_users')

        if password != confirmpassword: # Checks if passwords match
            messages.error(request, "Passwords do not match.")
            return redirect('add_users')

        ## This will create the user in Django's user table

        if usertype == 'Admin':
            user = User.objects.create_user(
                username = username,
                first_name = firstname,
                last_name = lastname,
                password = password,
                is_superuser = True, # sets role to admin
                is_staff = True # sets role to staff as well so can access admin panel
            )

            ## This will create a UserT instance to include the other information
            ## that we want to store

            user_t = UserT.objects.create(
                django_user = user,
                user_timestamp = now(),
                user_type = "Administrator",
                user_added_by = request.user if request.user.is_authenticated else None
            )

            ## This will save the UserT instance

        elif usertype == 'Employee':
            user = User.objects.create_user(
                username = username,
                first_name = firstname,
                last_name = lastname,
                password = password
            )

            ## This will create a UserT instance to include the other information
            ## that we want to store

            user_t = UserT.objects.create(
                django_user = user,
                user_timestamp = now(),
                user_type = "Employee",
                user_added_by = request.user if request.user.is_authenticated else None
            )

            ## This will save the UserT instance
            
        messages.success(request, "User account created successfully.")
        return redirect('add_users')

    return render(request, 'HaoTasty/add_users.html')

@superuser_required
def delete_users(request):
    if request.method == 'POST': 
        user_to_delete = request.POST.get('delete_username')
        try:
            user = User.objects.get(username=user_to_delete) # Get the user to delete
            user_t_details = UserT.objects.get(django_user=user) # Also delete associated user_t entry
            user_t_details.delete()
            user.delete()
            messages.info(request, 'User has been deleted from the system.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
        except UserT.DoesNotExist:
            messages.error(request, 'User profile not found.')
    return redirect('manage_users')

@login_required(login_url='login_user')
def update_users(request, user_id):
    user = get_object_or_404(User, id=user_id) # Get user from auth_user table
    usert_profile = get_object_or_404(UserT, django_user=user) # Get other details from user_t table
    is_admin = request.user.is_superuser # Check if user is an admin
    template = 'HaoTasty/update_users.html' if is_admin else 'HaoTasty/profile_employee.html'

    if request.method == 'POST':
        username = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        user_type = request.POST.get("user_type", "").strip()
        updated = False
        
        # Validate required fields
        if not username or not first_name or not last_name or not user_type:
            messages.error(request, "All fields (username, first name, last name, user type) are required.")
            return redirect("update_users", user_id=user.id)
        
        # Else all required fields are filled

        if username and username != user.username:
            if User.objects.filter(username=username).exists(): # Checks if username exists
                messages.error(request, "Username already exists.")
                return redirect("update_users", user_id=user.id)
            else:
                user.username = username
                updated = True
        
        if first_name and first_name != user.first_name:
            user.first_name = first_name
            updated = True

        if last_name and last_name != user.last_name:
            user.last_name = last_name
            updated = True
        
        if user_type and user_type != usert_profile.user_type:
            usert_profile.user_type = user_type
            updated = True

        # Handle admin roles

        if user_type == 'Administrator':
            if not user.is_superuser or not user.is_staff:
                user.is_superuser = True
                user.is_staff = True
                updated = True
        elif user.is_superuser or user.is_staff:
            user.is_superuser = False
            user.is_staff = False
            updated = True

        # Handle password update
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        if password or confirm_password:
            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect("update_users", user_id=user.id)
            else:
                user.password = make_password(password)
                updated = True
        
        if updated:
            user.save()
            usert_profile.save()
            messages.success(request, 'User details updated successfully.')
        else:
            messages.info(request, 'No changes were made.')
        
        return redirect("update_users", user_id=user.id)

    return render(request, template, {"user": user, 
                                      "usert_profile": usert_profile})


# --- System Back Ups ---------
@superuser_required
def data_dashboard(request): 
    context=list_backups(request)
    print(context)
    return render(request, 'HaoTasty/data_dashboard.html',context)

@superuser_required
def create_backup(request):
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    now = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{now}"
    backup_path = os.path.join(backup_dir, f"{filename}.json")
    meta_path = os.path.join(backup_dir, f"{filename}.meta.json")

    try:
        # Dump to a temporary string first
        from io import StringIO
        buffer = StringIO()
        management.call_command(
            'dumpdata',
            'HaoTasty.OrderT',
            'HaoTasty.OrderLineT',
            'HaoTasty.MenuItemT',
            'HaoTasty.ExpenseT',
            'HaoTasty.ExpenseCatT',
            indent=2,
            stdout=buffer
        )
        # Only save to file if dumpdata succeeded
        with open(backup_path, 'w') as f:
            f.write(buffer.getvalue())

        metadata = {
            "filename": filename,
            "backup_path": backup_path,
            "created_by": request.user.username,
            "timestamp": datetime.now().isoformat(),
            "notes": request.POST.get("notes", ""),
        }
        with open(meta_path, "w") as mf:
            json.dump(metadata, mf)

        messages.success(request, f"Backup {filename} created successfully")

    except Exception as e:
        messages.error(request, f"Backup failed: {e}")

    return redirect('data_dashboard')

@superuser_required
def list_backups(request):
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    backups = []

    for fname in os.listdir(backup_dir):
        if fname.endswith('.json') and not fname.endswith('.meta.json'):
            meta_file = fname.replace(".json", ".meta.json")
            meta_path = os.path.join(backup_dir, meta_file)

            metadata = {}
            timestamp = None

            if os.path.exists(meta_path):
                with open(meta_path) as mf:
                    metadata = json.load(mf)
                    if 'timestamp' in metadata:
                        try:
                            timestamp = datetime.fromisoformat(metadata['timestamp'])
                            metadata['timestamp'] = timestamp
                        except ValueError:
                            metadata['timestamp'] = None
            backups.append({
                "filename": fname,
                "metadata": metadata,
                "sort_key": timestamp or datetime.min  # fallback for invalid/missing timestamp
            })

    # Sort from most recent to oldest
    backups.sort(key=lambda b: b['sort_key'], reverse=True)

    # Remove sort_key before returning
    for b in backups:
        b.pop('sort_key', None)

    return {"backups": backups}

@superuser_required
def restore(request): 
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    backups = [f for f in os.listdir(backup_dir) if f.endswith('.json') and not f.endswith('.meta.json')]

    if request.method == 'POST':
        selected_file = request.POST.get('selected_backup')
        messages.info(request, f"Restoring system data from {selected_file}")
        if selected_file:
            backup_path = os.path.join(backup_dir, selected_file)
            
            # Step 1: Truncate only selected tables
            tables_to_clear = ['order_line_t', 'order_t', 'menu_item_t', 'expense_t']
            try:
                with connection.cursor() as cursor:
                    cursor.execute('SET FOREIGN_KEY_CHECKS=0;')
                    for table in tables_to_clear:
                        cursor.execute(f'TRUNCATE TABLE {table};')
                    cursor.execute('SET FOREIGN_KEY_CHECKS=1;')
            except Exception as e:
                messages.error(request, f"Table clearing failed: {e}")
                return redirect('data_dashboard')

            # Step 2: Load selected backup
            try:
                management.call_command('loaddata', backup_path, verbosity=0)
                messages.success(request, f"Successfully restored from {selected_file}")
            except Exception as e:
                messages.error(request, f"Restore failed: {e}")
            return redirect('data_dashboard')

    return render(request, 'HaoTasty/restore.html', {'backups': backups})



@superuser_required
def download_backup(request, filename):
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    file_path = os.path.join(backup_dir, filename)

    if not os.path.exists(file_path):
        raise Http404("Backup file not found")

    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
    response['Content-Disposition'] = f'attachment; filename="{smart_str(filename)}"'
    return response

@superuser_required
@require_POST
def delete_backup(request):
    filename = request.POST.get('filename')
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    
    try:
        # Delete JSON file and associated .meta.json
        os.remove(os.path.join(backup_dir, filename))
        meta_file = filename.replace('.json', '.meta.json')
        meta_path = os.path.join(backup_dir, meta_file)
        if os.path.exists(meta_path):
            os.remove(meta_path)
        messages.success(request, f"Backup '{filename}' deleted successfully.")
    except Exception as e:
        messages.error(request, f"Failed to delete backup: {e}")

    return redirect('data_dashboard')  


# --- Menu CRUD Module ---------
@login_required(login_url='login_user')
def menu_dashboard(request): 
    menu_items = MenuItemT.objects.all()
    is_admin = request.user.is_superuser # Check if user is an admin
    template = 'HaoTasty/menu_dashboard.html' if is_admin else 'HaoTasty/menu_dashboard_employee.html'
    return render(request, template,{'menu_items': menu_items})

def validate_menu_item(name, price, cost, menu_item_id, menu_item_type):
    if MenuItemT.objects.exclude(menu_item_id=menu_item_id).filter(menu_item_name=name).exists():
        return "This menu item name already exists."
    if price <= 0:
        return "Price must be greater than 0."
    if cost < 1:
        return "Cost must be at least 1."
    if menu_item_type not in {"Main", "Side", "Addon"}:
        return "Type must be Main, Side, or Add-on"
    return None

def archive_menu_item(request, menu_item, new_name, new_price, new_cost, new_status, new_type):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    archived_name = f"{menu_item.menu_item_name} ({timestamp})"

    if MenuItemT.objects.filter(menu_item_name__iexact=archived_name).exclude(menu_item_id=menu_item.menu_item_id).exists():
        messages.error(request, "This menu item already exists.")
        return redirect("add_menu")
    
    # Create new item with updated values
    MenuItemT.objects.create(
        menu_item_name=new_name,
        menu_item_price=new_price,
        menu_item_cost=new_cost,
        menu_item_profit=new_price - new_cost,
        item_availability_status=new_status,
        menu_item_type=new_type
    )

    # Archive old item
    menu_item.menu_item_name = archived_name
    menu_item.item_availability_status = 0
    menu_item.save()

@superuser_required
def add_menu(request): 
    menu_items = MenuItemT.objects.all()  # Fetch all menu items

    if request.method == "POST":
        menu_item_name = request.POST.get("menu_item_name")
        menu_item_price = request.POST.get("menu_item_price")
        menu_item_cost = request.POST.get("menu_item_cost")
        item_availability_status = request.POST.get("item_availability_status")
        menu_item_type = request.POST.get("menu_item_type")

        # Basic validation
        if not menu_item_name or not menu_item_price or not menu_item_cost or not menu_item_type:
            messages.error(request, "All fields are required.")
            return redirect("add_menu")  # Redirect to the same page to display messages
        
        # Check if menu item already exists
        if MenuItemT.objects.filter(menu_item_name__iexact=menu_item_name).exists():
            messages.error(request, "This menu item already exists.")
            return redirect("add_menu")

        try:
            menu_item_price = Decimal(menu_item_price)
            menu_item_cost = Decimal(menu_item_cost)

            # Validate price is greater than zero
            if menu_item_price <= 0 or menu_item_cost < 0:
                messages.error(request, "Price must be greater than zero.")
                return redirect("add_menu")
            
            if menu_item_price-menu_item_cost <= 0:
                messages.info(request, f"Warning: Profit is negative. Review price and cost of {menu_item_name}")

            # Check for timestamp-like substring
            if MenuItemT.objects.filter(menu_item_name__iexact=menu_item_name).exists():
                menu_item_name = re.sub(r"\(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\)", "", menu_item_name)
                menu_item_name = re.sub(r"\s+", " ", menu_item_name).strip()

            menu_item = MenuItemT.objects.create(
                menu_item_name=menu_item_name.strip(),
                menu_item_price=menu_item_price,
                menu_item_cost=menu_item_cost,
                menu_item_profit=menu_item_price - menu_item_cost,
                item_availability_status=int(item_availability_status),
                menu_item_type=menu_item_type.strip()
            )
            messages.success(request, f"{menu_item.menu_item_name} added successfully!")
            return redirect("add_menu")
        except ValueError:
            messages.error(request, "Invalid numeric values. Please enter valid numbers.")
            return redirect("add_menu")

    return render(request, "HaoTasty/add_menu.html", {"menu_items": menu_items})

@superuser_required
def update_menu(request): 
    menu_items = MenuItemT.objects.all()

    if request.method == "POST":
        try:
            menu_item_ids = request.POST.getlist("menu_item_id[]")
            menu_item_names = request.POST.getlist("menu_item_name[]")
            menu_item_prices = list(map(Decimal, request.POST.getlist("menu_item_price[]")))
            menu_item_costs = list(map(Decimal, request.POST.getlist("menu_item_cost[]")))
            menu_item_statuses = list(map(int, request.POST.getlist("item_availability_status[]")))
            menu_item_types = list(request.POST.getlist("menu_item_type[]"))

            if not menu_item_names:
                messages.error(request, "No menu items were selected for update.")
                return redirect("update_menu")

            updated_count = 0
            updated=[]

            for item_id, new_name, new_price, new_cost, new_status, new_type in zip(menu_item_ids, menu_item_names, menu_item_prices, 
                                                                                    menu_item_costs, menu_item_statuses, menu_item_types):
                # Fetch the existing menu item using its name
                menu_item = get_object_or_404(MenuItemT, pk=item_id)

                # Validate input (use menu_item_id instead of old_name)
                error = validate_menu_item(new_name, new_price, new_cost, menu_item.menu_item_id, new_type)
                if error:
                    messages.error(request, error)
                    return redirect("update_menu")

                # Skip update if nothing changed
                if (
                    menu_item.menu_item_name == new_name
                    and menu_item.menu_item_price == new_price
                    and menu_item.menu_item_cost == new_cost
                    and menu_item.item_availability_status == new_status
                    and menu_item.menu_item_type == new_type
                ):
                    continue

                changed = False

                # Check for timestamp-like substring
                new_name = re.sub(r"\(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\)", "", new_name)
                new_name = re.sub(r"\s+", " ", new_name).strip()
                if MenuItemT.objects.filter(menu_item_name__iexact=new_name).exclude(menu_item_id=menu_item.menu_item_id).exists():
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_name += " ("+timestamp+")"
                    print(new_name)

                if menu_item.menu_item_name != new_name:
                    if MenuItemT.objects.filter(menu_item_name__iexact=new_name).exclude(menu_item_id=menu_item.menu_item_id).exists():
                        archive_menu_item(request, menu_item, new_name, new_price, new_cost, new_status, new_type)
                        messages.success(request, f"Menu Item {menu_item.menu_item_name}: name has been updated.")
                    else:
                        menu_item.menu_item_name = new_name
                        messages.success(request, f"Menu Item {menu_item.menu_item_name}: name has been updated.")
                        changed = True

                if menu_item.menu_item_price != new_price or menu_item.menu_item_cost != new_cost:
                    archive_menu_item(request, menu_item, new_name, new_price, new_cost, new_status, new_type)
                    messages.success(request, f"Menu Item {menu_item.menu_item_name}: price/cost have been updated.")
                    updated_count += 1
                    updated.append(menu_item.menu_item_name)
                    continue

                if menu_item.menu_item_type != new_type:
                    menu_item.menu_item_type = new_type
                    messages.success(request, f"Menu Item {menu_item.menu_item_name}: type has been updated.")
                    changed = True

                if menu_item.item_availability_status != new_status:
                    menu_item.item_availability_status = new_status
                    messages.success(request, f"Menu Item {menu_item.menu_item_name}: availability status has been updated.")
                    changed = True

                if changed:
                    menu_item.save()
                    updated_count += 1
                    updated.append(menu_item.menu_item_name)

            if updated_count:
                messages.success(request, f"{updated_count} menu item(s) updated successfully: {', '.join(updated)}")
            else:
                messages.info(request, "No changes were made.")

            return redirect("update_menu")
        
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect("update_menu")

    return render(request, "HaoTasty/update_menu.html", {"menu_items": menu_items})

@superuser_required
def delete_menu(request, menu_item_id):
    menu_item = get_object_or_404(MenuItemT, menu_item_id=menu_item_id)
    menu_item.item_availability_status = 0
    menu_item.save()
    messages.success(request, f"Menu Item {menu_item.menu_item_name} has been discontinued. Historical data not affected. To delete a menu item completely, update all existing sales entries dependent on the menu item.")
    return redirect("update_menu")  # Redirect back to the menu after deletion








# --- Report Logic ---------

def get_start_date(filter_type, date_selected):
    """ Returns the start date based on filter type. """
    if not date_selected:
        return None

    start_date = datetime.strptime(date_selected, "%Y-%m-%d").date()

    if filter_type == "weekly":
        start_date -= timedelta(days=start_date.weekday())  # Start of the week
    elif filter_type == "monthly":
        start_date = start_date.replace(day=1)  # Start of the month
    elif filter_type == "yearly":
        start_date = start_date.replace(month=1, day=1)  # Start of the year

    return start_date


def filter_order_lines(start_date, filter_type, data_type="sales"):
    """ Returns filtered queryset based on the date filter for sales or expenses. """
    
    model = OrderLineT if data_type == "sales" else ExpenseT
    date_field = "order__order_timestamp" if data_type == "sales" else "expense_date"

    queryset = model.objects.all()

    if filter_type == "cumulative":
        return queryset

    if not start_date:
        return queryset  

    if filter_type == "daily":
        if date_field == "expense_date":  
            return queryset.filter(expense_date=start_date)  # Direct match since it's already a DateField
        return queryset.filter(**{f"{date_field}__date": start_date})  # Use __date for DateTimeField

    elif filter_type == "weekly":
        return queryset.filter(
            **{f"{date_field}__gte": start_date, f"{date_field}__lt": start_date + timedelta(days=7)}
        )
    elif filter_type == "monthly":
        return queryset.filter(
            **{
                f"{date_field}__gte": start_date,
                f"{date_field}__lt": (start_date.replace(day=28) + timedelta(days=4)).replace(day=1),
            }
        )
    elif filter_type == "yearly":
        return queryset.filter(**{f"{date_field}__year": start_date.year})

    return queryset

def get_data(queryset, data_type="sales"):
    """Returns sales or expense data grouped by category or menu item."""
    
    if data_type == "sales":
        model = MenuItemT
        filter_field = "orderlinet"
        amount_field = "orderlinet__order_quantity"
        price_field = "menu_item_price"
        name_field = "menu_item_name"
    else:  # Expense Case
        model = ExpenseCatT
        filter_field = "expenset"
        amount_field = "expenset__expense_amount"
        price_field = None  # No price field for expenses
        name_field = "expense_cat_name"

    # 🔹 Choose the correct filtering logic
    if data_type == "sales":
        filtered_queryset = model.objects.filter(**{f"{filter_field}__in": queryset})
        
        queryset_result = filtered_queryset.annotate(
        total_orders=Coalesce(Sum(F(amount_field)),0),
        total_revenue=Coalesce(
            Sum(
                ExpressionWrapper(
                    F(amount_field) * F(price_field) if price_field else F(amount_field), 
                    output_field=DecimalField()
                )
            ),
            Decimal("0.00")
        )
    ).values(name_field, price_field, "total_orders", "total_revenue")  
        
    else:  # Expenses
        filtered_queryset = model.objects.filter(expenset__in=queryset) 
        queryset_result = filtered_queryset.annotate(
        total_expense_count=Count(filter_field),
        total_expense=Coalesce(
            Sum(
                ExpressionWrapper(
                    F(amount_field) * F(price_field) if price_field else F(amount_field), 
                    output_field=DecimalField()
                )
            ),
            Decimal("0.00")
        )
    ).values(name_field, "total_expense_count", "total_expense")   

    print("Queryset:", list(queryset_result))  # Debugging output
    return list(queryset_result)

def calculate_fbt(order_lines):
    """ Returns the top 3 frequently bought together items. """
    fbt_counter = Counter()
    order_items = order_lines.values("order_id", "menu_item__menu_item_name")

    order_dict = {}
    for item in order_items:
        order_dict.setdefault(item["order_id"], []).append(item["menu_item__menu_item_name"])

    for items in order_dict.values():
        for pair in combinations(sorted(items), 2):
            fbt_counter[pair] += 1

    return [{"pair": f"{pair[0]} & {pair[1]}", "count": count} for pair, count in fbt_counter.most_common(3)]

def get_annual_metric(mode, data_type="sales"):
    """Returns aggregated revenue (sales) or total expenses grouped by year or month."""
    
    model = OrderT if data_type == "sales" else ExpenseT
    date_field = "order_timestamp" if data_type == "sales" else "expense_date"
    amount_field = "orderlinet__order_quantity" if data_type == "sales" else "expense_amount"
    price_field = "orderlinet__menu_item_id__menu_item_price" if data_type == "sales" else None

    queryset = model.objects.annotate(year=TruncYear(F(date_field)))

    if mode == "month":
        queryset = queryset.annotate(month=TruncMonth(F(date_field)))
        values = ["year", "month"]
    else:
        values = ["year"]

    # Expenses don't have price_field, so avoid multiplying
    queryset = queryset.values(*values).annotate(
        total_value=Coalesce(
            Sum(
                F(amount_field) if data_type == "expenses" 
                else ExpressionWrapper(F(amount_field) * F(price_field), output_field=DecimalField())
            ),
            Decimal("0.00")
        )
    ).order_by(*values)

    return list(queryset)

@superuser_required
def sales_report(request):
    menu_items = list(MenuItemT.objects.values("menu_item_id", "menu_item_name", "menu_item_price","menu_item_type"))
    menu_item_types = list(MenuItemT.objects.values_list("menu_item_type", flat=True).distinct())

    # Checking Filter Selected 
    filter_type = request.GET.get("filter", "cumulative")


    # FOR INVALID DATE RANGE -------

    # Checking Date Selected 
    date_selected = request.GET.get("datePicker", str(datetime.today().date()))
    today = datetime.today().date()
    start_date = get_start_date(filter_type, date_selected)
    week_start_date = None
    daily_date = None
    month_date = None
    year_date = None
    if not start_date:
        start_date = today

    # Calculate the end date based on filter_type
    if filter_type == "daily":
        end_date = today  # For daily, end date is today
        daily_date = start_date
    elif filter_type == "weekly":
        # Get the end date of the week (Sunday) based on the start_date
        end_date = start_date + timedelta(days=(6 - start_date.weekday()))  # Sunday of the week
        week_start_date = end_date - timedelta(days=(6 - start_date.weekday())) 
    elif filter_type == "monthly":
        # Get the last day of the selected month
        end_date = start_date.replace(day=1) + timedelta(days=32)
        end_date = end_date.replace(day=1) - timedelta(days=1)  # End of the month
        month_date = end_date.strftime('%B, %Y')
    elif filter_type == "yearly":
        # Get the last day of the selected year
        end_date = start_date.replace(month=12, day=31)
        year_date = end_date.strftime('%Y')
    else:
        # For cumulative, the end date is today
        end_date = today


    earliest_order_obj = OrderT.objects.order_by("order_timestamp").first()
    if earliest_order_obj:
        earliest_date = earliest_order_obj.order_timestamp.date()
    else:
        earliest_date = today # Fallback if no orders yet

    if date_selected:
        selected_date_obj = datetime.strptime(date_selected, "%Y-%m-%d").date()
        if selected_date_obj < earliest_date or selected_date_obj > today:
            messages.error(
                request,
                f"Error: Selected date is out of range. Please select a date between {earliest_date.strftime('%m/%d/%Y')} and {today.strftime('%m/%d/%Y')}."
            )
    # Checking the Menu Type Filter 
    menu_selected = request.GET.get("menuItemDropdown","All")
    if start_date:
        order_lines = filter_order_lines(start_date, filter_type, "sales")
        if menu_selected != "All":
            order_lines = order_lines.filter(menu_item__menu_item_type=menu_selected)
    else:
        order_lines = OrderLineT.objects.all()

    # FOR INSUFFICIENT DATA ------- 

    # Get all unique transaction days
    transaction_dates = order_lines.annotate(date=TruncDate("order_id__order_timestamp")).values_list("date", flat=True).distinct()
    
    # Count operating days
    operating_days = len(transaction_dates)
    
    # Count unique year-months with at least 1 transaction
    month_count = len(set((date.year, date.month) for date in transaction_dates))
    day_count = len(set((date.year,date.month,date.day) for date in transaction_dates))

    # Count unique sales transactions
    unique_sales_count = order_lines.values('order_id').distinct().count()

    # Count unique sales (orders) per date
    daily_transaction_counts = (
        order_lines
        .annotate(date=TruncDate('order_id__order_timestamp'))
        .values('date')
        .annotate(transaction_count=Count('order_id', distinct=True))
        .order_by('date')
    )

    # Check if operating days are below threshold or 0
    if operating_days == 0: 
        messages.error(request, f"Error: No transactions found for the selected date.")
    # Determine threshold based on filter_type
    elif filter_type == "daily":
        if unique_sales_count < 5:
            messages.warning(request, f"Warning: Reports may be incomplete. Only {unique_sales_count} record/s of transaction data.")
    elif filter_type == "weekly": 
        if day_count < 5:
            messages.warning(request, f"Warning: Reports may be incomplete. Only {day_count} operating day/s of transaction data.")
    elif filter_type == "monthly":
        if day_count < 20:
            messages.warning(request, f"Warning: Reports may be incomplete. Only {day_count} operating day/s of transaction data.")
    elif filter_type in ["yearly", "cumulative"]:
        if month_count < 12:
            messages.warning(request, f"Warning: Reports may be incomplete. Only {month_count} month/s with transaction data.")

    # Compute total revenue
    total_revenue = order_lines.aggregate(
        total=Sum(F("order_quantity") * F("menu_item__menu_item_price"))
    )["total"] or Decimal("1.00")  # Avoid division by zero

    # Convert to string for JSON serialization
    total_revenue_str = "{:,.2f}".format(total_revenue)

    # Compute sales data
    sales_data = get_data(order_lines, "sales")
    sales_data.sort(key=lambda item: Decimal(item["total_revenue"]), reverse=True)

    # Convert Decimal values to strings in sales_data
    for item in sales_data:
        item["bar_width"] = (Decimal(item["total_revenue"]) / total_revenue) * 100

    # Handle case where sales_data is empty
    if sales_data:
        max_bar_width = max(item["bar_width"] for item in sales_data)
    else:
        max_bar_width = 1  # Default to prevent division by zero

    for item in sales_data:
        item["menu_item_price"] = str(item["menu_item_price"])
        item["total_revenue"] = str(item["total_revenue"])
        item["bar_width"] = int(round((item["bar_width"] / max_bar_width) * 100)) if max_bar_width > 0 else 0  # Safe scaling
    
    # Best-selling and worst-selling menu items
    best_selling_item = sales_data[0]['menu_item_name'] if sales_data else None
    worst_selling_item = sales_data[-1]['menu_item_name'] if sales_data else None

    # Frequently Bought Together (FBT) - Top 3 pairs
    top_3_fbt = calculate_fbt(order_lines)

    # Annual Revenue
    annual_revenue = get_annual_metric(filter_type,"sales")
    for item in annual_revenue:
        item["total_value"] = str(item["total_value"])  # Convert Decimal to string
        item["year"] = item["year"].strftime("%Y") if item["year"] else "No Year"

        if filter_type == "monthly" and "month" in item:
            item["month"] = item["month"].strftime("%m") if item["month"] else "No Month"
        else:
            item.pop("month", None)

    # Get revenue by day (daily data, always)
    revenue_by_date = order_lines.annotate(
        date=TruncDate("order_id__order_timestamp")  # Group by date
    ).values("date").annotate(
        total_revenue=Sum(F("order_quantity") * F("menu_item__menu_item_price"))
    ).order_by("date")

   # Ensure the data is always daily, even if the filter is weekly/monthly/yearly
    revenue_by_date_list = []

    # Generate daily data for the full range
    if filter_type == "cumulative":
        start_date = earliest_date
    while start_date <= end_date:
        revenue_for_day = next(
            (item for item in revenue_by_date if item["date"] == start_date), 
            {"date": start_date, "total_revenue": 0}
        )
        revenue_by_date_list.append({
            "date": revenue_for_day["date"].strftime("%Y-%m-%d"),  # Convert to string
            "total_revenue": float(revenue_for_day["total_revenue"] or 0),  # Convert Decimal to float
        })
        start_date += timedelta(days=1)



    context = {
        "menu_items": menu_items,
        "menu_item_types": menu_item_types,
        "sales": json.dumps(sales_data, cls=DjangoJSONEncoder),
        "operating_days": operating_days,
        "unique_sales_count":unique_sales_count,
        "daily_transaction_counts":daily_transaction_counts,
        "overall_total_revenue": total_revenue_str,  
        "best_selling": best_selling_item,
        "worst_selling": worst_selling_item,
        "top_fbt": json.dumps(top_3_fbt),
        "revenue_by_date": json.dumps(revenue_by_date_list),
        "annual_revenue": json.dumps(annual_revenue),
        "filter_type": filter_type,
        "date_selected": date_selected or today.strftime("%Y-%m-%d"),
        "order_lines": order_lines,
        "start_date": start_date,
        "end_date":end_date,
        "menu_selected": menu_selected,
        "earliest_date": earliest_date,
        "week_start_date": week_start_date,
        "daily_date": daily_date,
        "month_date": month_date,
        "year_date": year_date
   }

    print(context)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(context, safe=False)

    return render(request, "HaoTasty/sales_report.html", context)


# --- Report Logic: Expense Report ---------
@superuser_required
def expense_report(request):
    """Generates an expense report similar to the sales report."""
    expense_cat=ExpenseCatT.objects.all()

    # Get filter type and selected date
    filter_type = request.GET.get("filter", "cumulative")

    # Checking Date Selected 
    date_selected = request.GET.get("datePicker", None)
    today = datetime.today().date()
    start_date = get_start_date(filter_type, date_selected)

    earliest_order_obj = ExpenseT.objects.order_by("expense_date").first()
    if earliest_order_obj:
        earliest_date = earliest_order_obj.expense_date
    else:
        earliest_date = today # Fallback if no orders yet
        messages.error(
                request,
                f"Error: No expense entries recorded in your database."
            )
    if date_selected:
        selected_date_obj = datetime.strptime(date_selected, "%Y-%m-%d").date()
        if selected_date_obj < earliest_date or selected_date_obj > today:
            messages.error(
                request,
                f"Error: Selected date is out of range. Please select a date between {earliest_date.strftime('%m/%d/%Y')} and {today.strftime('%m/%d/%Y')}."
            )

    # Fetch expense records
    if start_date:
        expense_lines = filter_order_lines(start_date, filter_type, "expenses")
    else:
        expense_lines = ExpenseT.objects.all()
    
    # FOR INSUFFICIENT DATA ------- 

    # Get all unique transaction days
    transaction_dates = expense_lines.values_list("expense_date", flat=True).distinct()
    
    # Count operating days
    days_with_expense = len(transaction_dates)
    
    # Count unique year-months with at least 1 transaction
    month_count = len(set((date.year, date.month) for date in transaction_dates))
    week_count = len(set((date.year, date.isocalendar().week) for date in transaction_dates))

    # Count unique sales transactions
    unique_expense_count = expense_lines.values('expense_id').distinct().count()

    # Count unique sales (orders) per date
    daily_transaction_counts = (
        expense_lines
        .values('expense_date')
        .annotate(transaction_count=Count('expense_id', distinct=True))
        .order_by('expense_date')
    )

    # Check if operating days are below threshold or 0
    if days_with_expense == 0: 
        messages.error(request, f"Error: No expense entries recorded in your database.")
    # Determine threshold based on filter_type
    elif filter_type in ("daily","weekly"):
        if unique_expense_count < 1:
            messages.warning(request, f"Warning: Reports may be incomplete. Only {unique_expense_count} record/s of expense data.")
    elif filter_type == "monthly":
        if week_count < 4:
            messages.warning(request, f"Warning: Reports may be incomplete. Only {week_count} week/s with recorded expense data.")
    elif filter_type in ["yearly", "cumulative"]:
        if month_count < 12:
            messages.warning(request, f"Warning: Reports may be incomplete. Only {month_count} month/s with recorded expense data.")


    # Compute total expenses
    total_expenses = expense_lines.aggregate(
        total=Coalesce(Sum(F("expense_amount")), Decimal("0.00"))
    )["total"]

    total_expenses_str = "{:,.2f}".format(total_expenses)  # Convert for JSON response

    # Compute expense data grouped by category
    expense_data = get_data(expense_lines,"expenses")
    expense_data.sort(key=lambda item: Decimal(item["total_expense"]), reverse=True)

    # Compute bar widths
    for item in expense_data:
        item["bar_width"] = (Decimal(item["total_expense"]) / total_expenses) * 100

    # Scale bars to a max of 100%
    if expense_data:
        max_bar_width = max(item["bar_width"] for item in expense_data)
    else:
        max_bar_width = 1  # Default to prevent division by zero
    
    for item in expense_data:
        item["bar_width"] = int(round((item["bar_width"] / max_bar_width) * 100))
        item["total_expense"] = str(item["total_expense"])  # Convert Decimal to string

    # Most and least expensive categories
    highest_expense_category = expense_data[0]["expense_cat_name"] if expense_data else None
    lowest_expense_category = expense_data[-1]["expense_cat_name"] if expense_data else None

    expense_qs = expense_lines

    # Top 3 Expense Entries
    expense_lines = list(expense_qs)
    expense_lines.sort(key=lambda item: Decimal(item.expense_amount), reverse=True)

    # Get top 3 expense entries
    top_expenses = expense_lines[:3]

    # Annual Expense Breakdown
    annual_expenses = get_annual_metric(filter_type)
    for item in annual_expenses:
        item["total_value"] = str(item["total_value"])  # Convert Decimal to string
        item["year"] = item["year"].strftime("%Y") if item["year"] else "No Year"
        if filter_type == "monthly" and "month" in item:
            item["month"] = item["month"].strftime("%m") if item["month"] else "No Month"
        else:
            item.pop("month", None)

    week_start_date = None
    daily_date = None
    month_date = None
    year_date = None

     # Calculate the end date based on filter_type
    if filter_type == "daily":
        end_date = today  # For daily, end date is today
        daily_date = start_date
    elif filter_type == "weekly":
        # Get the end date of the week (Sunday) based on the start_date
        end_date = start_date + timedelta(days=(6 - start_date.weekday()))  # Sunday of the week
        week_start_date = end_date - timedelta(days=(6 - start_date.weekday())) 
    elif filter_type == "monthly":
        # Get the last day of the selected month
        end_date = start_date.replace(day=1) + timedelta(days=32)
        end_date = end_date.replace(day=1) - timedelta(days=1)  # End of the month
        month_date = end_date.strftime('%B, %Y')
    elif filter_type == "yearly":
        # Get the last day of the selected year
        end_date = start_date.replace(month=12, day=31)
        year_date = end_date.strftime('%Y')
    else:
        # For cumulative, the end date is today
        end_date = today
        start_date = earliest_date

    if filter_type in("daily","weekly"):
        weekly_expenses = expense_qs.filter(expense_date__range=(start_date, end_date)).annotate(
        day=TruncDate("expense_date")
        ).values("day").annotate(
        total_expense=Sum("expense_amount")
        ).order_by("day")

        weekly_expenses_serialized = [
        {
            "day": item["day"].strftime("%Y-%m-%d") if item["day"] else "Unknown",
            "total_expense": float(item["total_expense"])
        }
        for item in weekly_expenses
        ]

    else:
        weekly_expenses = expense_qs.filter(expense_date__range=(start_date, end_date)).annotate(
                week=TruncWeek("expense_date")
            ).values("week").annotate(
                total_expense=Sum("expense_amount")
            ).order_by("week")
        
        weekly_expenses_serialized = [
            {
                "week": item["week"].strftime("%Y-%m-%d") if item["week"] else "Unknown",
                "total_expense": float(item["total_expense"])
            }
            for item in weekly_expenses
        ]

    # Final context
    context = {
        "expenses": json.dumps(expense_data, cls=DjangoJSONEncoder),
        "expenses2":expense_data,
        "expense_cat":expense_cat,
        "days_with_expense":days_with_expense,
        "unique_expense_count":unique_expense_count,
        "daily_transaction_counts":daily_transaction_counts,
        "total_expenses": total_expenses_str,
        "highest_expense": highest_expense_category,
        "top_expenses":top_expenses,
        "lowest_expense": lowest_expense_category,
        "annual_expenses": json.dumps(annual_expenses),
        "filter_type": filter_type,
        "date_selected": date_selected or today.strftime("%Y-%m-%d"),
        "expense_lines": expense_lines,
        "start_date": start_date,
        "end_date":end_date,
        "weekly_expenses":json.dumps(weekly_expenses_serialized),
        "earliest_date": earliest_date,
        "week_start_date": week_start_date,
        "daily_date": daily_date,
        "month_date": month_date,
        "year_date": year_date
    }

    print(context)

    return render(request, "HaoTasty/expense_report.html", context)











# --- Report Logic: Sales Forecast --------
def forecast_sales(request, filter_type):
    # Fetch sales data
    monthly_sales = get_annual_metric(mode="month")  # Fetch monthly revenue
    yearly_sales = get_annual_metric(mode="year")  # Fetch yearly revenue

    # Convert monthly data to arrays
    months = []
    revenue = []

    for entry in monthly_sales:
        year = entry["year"].year  # Extract integer year
        month = entry["month"].month  # Extract integer month
        total_value = float(entry["total_value"])  # Convert Decimal to float

        # Convert year-month to an integer scale (e.g., 2023-01 → 202301)
        months.append(year * 12 + month)
        revenue.append(total_value)


    # FOR INSUFFICIENT DATA ------- 
    order_lines = OrderLineT.objects.all()

    # Get all unique transaction days
    transaction_dates = order_lines.annotate(date=TruncDate("order_id__order_timestamp")).values_list("date", flat=True).distinct()
    
    # Count operating days
    operating_days = len(transaction_dates)
    
    # Count unique year-months with at least 1 transaction
    month_count = len(set((date.year, date.month) for date in transaction_dates))

    # Count unique sales transactions
    unique_sales_count = order_lines.values('order_id').distinct().count()

    # Check if operating days are below threshold or 0
    if operating_days == 0: 
        messages.error(request, f"Error: No historical data found.")
    # Determine threshold based on filter_type
    elif filter_type in ("next_month","next_3_months"):
        if month_count < 3:
            messages.warning(request, f"Important: Forecasts are based on {month_count} month(s) of transaction data. Results should be interpreted with caution due to potential data limitations.")
    elif filter_type in ["next_6_months", "next_12_months"]:
        if month_count < 12:
            messages.warning(request, f"Important: Forecasts are based on {month_count} month(s) of transaction data. Results should be interpreted with caution due to potential data limitations.")

    # Determine the last complete year
    current_year = datetime.now().year
    available_years = sorted(set(entry["year"].year for entry in yearly_sales))
    last_complete_year = None
    for y in reversed(available_years):
        if y < current_year:
            last_complete_year = y
            break
    if last_complete_year is None:
        last_complete_year = current_year - 1 # Or handle it as appropriate for your logic

    # Forecast per menu_item 

    # Step 1: Fetch monthly order data per menu item
    raw_data = (
        OrderLineT.objects.annotate(month=TruncMonth("order__order_timestamp"))
        .values("month", "menu_item__menu_item_name")
        .annotate(total_ordered=Sum("order_quantity"))
        .order_by("month")
    )

    # Organize data: {(menu_item, month_num): quantity}
    item_month_data = defaultdict(lambda: defaultdict(int))
    all_months = set()

    for row in raw_data:
        item = row["menu_item__menu_item_name"]
        month_date = row["month"]
        month_num = month_date.year * 12 + month_date.month  # e.g. 2023*12+5 = 24281
        all_months.add(month_num)
        item_month_data[item][month_num] = row["total_ordered"]

    all_months = sorted(all_months)

    # Step 2–3: Train separate model per item and forecast next 12 months
    item_forecasts = {}

    for item, monthly_counts in item_month_data.items():
        months = sorted(monthly_counts.keys())
        if len(months) < 3:
            continue  # Not enough data to forecast reliably

        # Get the first day of this month
        this_month_start = datetime.today().replace(day=1)

        # Convert month integers to datetime objects
        ds = [datetime(year=(m - 1) // 12, month=((m - 1) % 12) + 1, day=1) for m in months]

        # Filter out this month (keep only full months of data)
        ds_y = [(d, monthly_counts[m]) for d, m in zip(ds, months) if d < this_month_start]

        # Unpack filtered ds and y
        if len(ds_y) < 3:
            continue  # Still not enough data

        ds, y = zip(*ds_y)
        df = pd.DataFrame({"ds": ds, "y": y})

        model = Prophet()
        model.fit(df)

        # Compute how many months from the last training date to current month
        last_date = max(ds)
        today = datetime.today().replace(day=1)  # First of this month (e.g., May 1, 2025)
        months_ahead = (today.year - last_date.year) * 12 + (today.month - last_date.month)

        # Ensure forecast covers at least months_ahead + 12
        total_months_needed = months_ahead + 12
        future_df = model.make_future_dataframe(periods=total_months_needed, freq='M')
        forecast_df = model.predict(future_df)

        # Get the forecast for the last 12 months only
        forecast_df["ds"] = pd.to_datetime(forecast_df["ds"])
        forecast_df = forecast_df[forecast_df["ds"] >= today]
        forecast_tail = forecast_df.head(12)

        future_dates = forecast_tail["ds"].dt.to_pydatetime()
        predicted_orders = [max(0, round(p)) for p in forecast_tail["yhat"]]

        # Format like "5/2025"
        item_forecasts[item] = [
            {
                "month": f"{m.month}/{m.year}",
                "predicted_orders": p
            }
            for m, p in zip(future_dates, predicted_orders)
        ]

    # Get item prices
    menu_items = MenuItemT.objects.all()
    item_price_dict = {item.menu_item_name: float(item.menu_item_price) for item in menu_items}

    # Build monthly revenue forecast from item forecasts
    monthly_revenue = defaultdict(float)

    for item, forecasts in item_forecasts.items():
        price = item_price_dict.get(item, 0)
        for f in forecasts:
            month = f["month"]  # format: "5/2025"
            monthly_revenue[month] += f["predicted_orders"] * price

    # Build sorted forecast list
    sorted_months = sorted(monthly_revenue.keys(), key=lambda x: (int(x.split("/")[1]), int(x.split("/")[0])))
    monthly_forecast = [
        {"month": month, "predicted_revenue": round(monthly_revenue[month], 2)}
        for month in sorted_months
    ]

    # Get yearly forecast by summing 12-month revenue
    predicted_yearly_revenue = round(sum(monthly_revenue.values()), 2)
    last_complete_year = datetime.now().year - 1


    # Format results
    future_forecast = {
        "monthly_forecast": monthly_forecast,
        "yearly_forecast": {
            "year": last_complete_year + 1,
            "predicted_revenue": predicted_yearly_revenue
        },
        "item_forecast": item_forecasts
    }

    print(future_forecast)

    return future_forecast, operating_days, unique_sales_count


@superuser_required
def sales_forecast(request): 
    filter_type = request.GET.get("filter", "next_month")
    forecast, operating_days, unique_sales_count = forecast_sales(request, filter_type)

    menu_items = MenuItemT.objects.all()
    item_price_dict = {item.menu_item_name: float(item.menu_item_price) for item in menu_items}
    print(f"Sales Forecast: {item_price_dict}")
    print(f"Filter selected: {filter_type}")

    # Determine the number of months to slice
    filter_map = {
        "next_month": 1,
        "next_3_months": 3,
        "next_6_months": 6,
        "next_12_months": 12
    }
    num_months = filter_map.get(filter_type, 12)

    # Slice monthly revenue forecast
    forecast["monthly_forecast"] = forecast["monthly_forecast"][:num_months]

    # Slice item forecasts
    for item in forecast["item_forecast"]:
        forecast["item_forecast"][item] = forecast["item_forecast"][item][:num_months]

    # --- Add filtered forecasted revenue total ---
    filtered_forecasted_revenue = round(sum(
        month["predicted_revenue"] for month in forecast["monthly_forecast"]
    ), 2)
    
    filtered_forecasted_revenue = "{:,.2f}".format(filtered_forecasted_revenue)

    context = {
        'forecast': forecast,
        'menu_item_prices': item_price_dict,
        'filter_type': filter_type,
        'filtered_forecasted_revenue': filtered_forecasted_revenue,        
        "operating_days": operating_days,
        "unique_sales_count":unique_sales_count,
    }

    return render(request, 'HaoTasty/sales_forecast.html', context)



# --- Report Logic: Expense Forecast ---------
def convert_np_floats(data):
    """ Recursively convert np.float64 values to Python float. """
    if isinstance(data, dict):
        return {key: convert_np_floats(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_np_floats(item) for item in data]
    elif isinstance(data, np.float64):
        return float(data)  # Convert np.float64 to Python float
    return data


def forecast_expenses(request, filter_type):    
    monthly_expenses = get_annual_metric(mode="month", data_type="expenses")

    # Insufficient data check
    expense_lines = ExpenseT.objects.all()
    transaction_dates = expense_lines.values_list("expense_date", flat=True).distinct()
    days_with_expense = len(transaction_dates)
    month_count = len(set((d.year, d.month) for d in transaction_dates))
    unique_expense_count = expense_lines.values('expense_id').distinct().count()

    if days_with_expense == 0:
        messages.error(request, "Error: No historical data found.")
    elif filter_type in ["next_month", "next_3_months", "next_6_months", "next_12_months"]:
        if month_count < 12:
            messages.warning(request, f"Warning: Forecasts may be inaccurate. Only {month_count} months with recorded expense data.")

    # Get last day of previous month
    today = datetime.today()
    first_day_this_month = datetime(today.year, today.month, 1)
    last_day_prev_month = first_day_this_month - timedelta(days=1)

    # Monthly data per category
    raw_data = (
        ExpenseT.objects.filter(expense_date__lte=last_day_prev_month)
        .annotate(month=TruncMonth("expense_date"))
        .values("month", "expense_cat__expense_cat_name")
        .annotate(total_expense=Sum("expense_amount"))
        .order_by("month")
    )

    category_month_data = defaultdict(lambda: defaultdict(float))
    all_months = set()

    for row in raw_data:
        cat = row["expense_cat__expense_cat_name"]
        month = row["month"]
        month_num = month.year * 12 + month.month
        all_months.add(month_num)
        category_month_data[cat][month_num] = row["total_expense"]

    all_months = sorted(all_months)
    category_forecasts = {}
    monthly_total = defaultdict(float)

    for cat, monthly_data in category_month_data.items():
        months = sorted(monthly_data.keys())
        if len(months) < 3:
            continue

        ds = [datetime(year=(m - 1) // 12, month=((m - 1) % 12) + 1, day=1) for m in months]
        y = [monthly_data[m] for m in months]

        df = pd.DataFrame({"ds": ds, "y": y})
        model = Prophet()
        model.fit(df)

        # Ensure forecast starts from current month (today)
        last_date = max(ds)
        today = datetime.today().replace(day=1)
        months_ahead = (today.year - last_date.year) * 12 + (today.month - last_date.month)
        total_months_needed = max(12, months_ahead + 12)  # Ensure we forecast at least 12 ahead

        future_df = model.make_future_dataframe(periods=total_months_needed, freq='M')
        forecast_df = model.predict(future_df)

        # Filter to forecasts starting from this month
        forecast_df["ds"] = pd.to_datetime(forecast_df["ds"])
        forecast_df = forecast_df[forecast_df["ds"] >= today]
        forecast_tail = forecast_df.head(12)

        future_dates = forecast_tail["ds"].dt.to_pydatetime()
        predicted_expenses = [max(0, round(p, 2)) for p in forecast_tail["yhat"]]

        category_forecasts[cat] = [
            {
                "month": f"{d.month}/{d.year}",
                "predicted_expense": e
            }
            for d, e in zip(future_dates, predicted_expenses)
        ]

        for d, e in zip(future_dates, predicted_expenses):
            month_key = f"{d.month}/{d.year}"
            monthly_total[month_key] += e

    # Build final forecast format
    sorted_months = sorted(monthly_total.keys(), key=lambda x: (int(x.split("/")[1]), int(x.split("/")[0])))
    monthly_forecast = [
        {
            "month": m,
            "predicted_expenses": round(monthly_total[m], 2)
        }
        for m in sorted_months
    ]
    predicted_yearly_expenses = round(sum(monthly_total.values()), 2)

    future_forecast = {
        "monthly_forecast": monthly_forecast,
        "yearly_forecast": {
            "year": datetime.now().year + 1,
            "predicted_expenses": predicted_yearly_expenses
        },
        "category_forecast": category_forecasts
    }

    return convert_np_floats(future_forecast), days_with_expense, unique_expense_count


@superuser_required
def expense_forecast(request):
    filter_type = request.GET.get("filter", "next_month") 
    forecast, days_with_expense, unique_expense_count = forecast_expenses(request, filter_type)  # Fetch the forecast

    # Determine the number of months to slice
    filter_map = {
        "next_month": 1,
        "next_3_months": 3,
        "next_6_months": 6,
        "next_12_months": 12
    }
    num_months = filter_map.get(filter_type, 12)

    # Slice monthly expense forecast
    forecast["monthly_forecast"] = forecast["monthly_forecast"][:num_months]

    # --- Add filtered forecasted expense total ---
    filtered_forecasted_expenses = round(sum(
        month["predicted_expenses"] for month in forecast["monthly_forecast"]
    ), 2)

    filtered_forecasted_expenses = "{:,.2f}".format(filtered_forecasted_expenses)
 

    # Update the context to use category_forecast (instead of item_forecast)
    context = {
        'forecast': forecast,
        'filter_type': filter_type,
        'filtered_forecasted_expenses': filtered_forecasted_expenses,
        "days_with_expense":days_with_expense,
        "unique_expense_count":unique_expense_count,
        'category_forecast': forecast.get("category_forecast", {})
    }
    
    print(f"Expense Forecast:{context}")

    return render(request, 'HaoTasty/expense_forecast.html', context)


# --- Report Logic: Profitability Forecast ---------

def assess_profitability(request, menu_item_id, new_price, elasticity):
    # Fetch historical data
    orderlines = OrderLineT.objects.filter(menu_item_id=menu_item_id)

    # Check if no data at all
    if not get_data(orderlines, "sales"):
        messages.error(request, f"Error: No historical data found.")
    else:
        # Count the number of data points
        count = orderlines.count()

        if count <= 2:
            messages.error(request, f"Insufficient data: Only {count} data points found.")
        elif count < 250:
            messages.warning(request, f"Note: Only {count} data points available for analysis.")

    # Get Menu Item Name
    menu_item = get_object_or_404(MenuItemT, menu_item_id=menu_item_id)
    menu_item_name = menu_item.menu_item_name

    # Get Base/Current Price
    base_price = float(MenuItemT.objects.get(menu_item_id=menu_item_id).menu_item_price)
    new_price = float(new_price)
    elasticity = float(elasticity)

    # Get Sales Forecast
    sales_forecast, operating_days, unique_sales_count = forecast_sales(request, "next_3_months")
        # Warning Messages embedded in the forecast_sales
    
    # Step 1: Get predicted sales for this item
    item_forecast = sales_forecast["item_forecast"].get(menu_item_name, [])

    adjusted_forecast=[]

    for entry in item_forecast:
        month = entry["month"]
        base_quantity = entry["predicted_orders"]



        # Step 2: Apply elasticity adjustment
        quantity_change = elasticity * ((new_price - base_price) / base_price)
        adjusted_quantity = base_quantity * (1 + quantity_change)
        adjusted_quantity = max(0, round(adjusted_quantity))  # Avoid negative sales

        # Step 3: Compute new revenue
        old_revenue = base_quantity * base_price
        new_revenue = adjusted_quantity * new_price

        adjusted_forecast.append({
        "month": month,
        "base_quantity": base_quantity,
        "adjusted_quantity": adjusted_quantity,
        "old_revenue": round(old_revenue, 2),
        "new_revenue": round(new_revenue, 2),
        "revenue_change": round(new_revenue - old_revenue, 2)
    })
        
    # Calculate total revenue with current price
    total_revenue_current = sum(entry["old_revenue"] for entry in adjusted_forecast)

    # Calculate new revenue with new price
    total_revenue_new = sum(entry["new_revenue"] for entry in adjusted_forecast)

    # Calculate the difference between the current and new revenue
    revenue_difference = total_revenue_new - total_revenue_current
    percentage_change = round((revenue_difference / total_revenue_current) * 100, 2) if total_revenue_current != 0 else "N/A" 

    total_revenue_current_str = "{:,.2f}".format(total_revenue_current)
    total_revenue_new_str = "{:,.2f}".format(total_revenue_new)
    revenue_difference_str = "{:,.2f}".format(revenue_difference)
   

    # Prepare the result
    context = {
        "menu_items": MenuItemT.objects.all(),
        "menu_item_name": menu_item_name,
        "base_price": str(base_price),
        "new_price": new_price,
        "elasticity": elasticity,
        "adjusted_forecast":adjusted_forecast,
        "total_revenue_current": str(total_revenue_current),
        "total_revenue_new": str(total_revenue_new),
        "revenue_difference": str(revenue_difference),
        "total_revenue_current_str": total_revenue_current_str,
        "total_revenue_new_str": total_revenue_new_str,
        "revenue_difference_str": revenue_difference_str,
        "percentage_change": percentage_change
    }

    context['months'] = [entry['month'] for entry in adjusted_forecast]
    context['old_revenues'] = [entry['old_revenue'] for entry in adjusted_forecast]
    context['new_revenues'] = [entry['new_revenue'] for entry in adjusted_forecast]


    return context

@superuser_required
def profitability_assessment(request): 
    menu_item_id = request.GET.get("menu_item_id", 1)
    new_price = float(request.GET.get("new_price", 55.00))
    elasticity = float(request.GET.get("elasticity", 1.5))
    menu_item = get_object_or_404(MenuItemT, menu_item_id=menu_item_id)
    old_price = menu_item.menu_item_price

    context = {
        "menu_items": MenuItemT.objects.all(),
    }


    # Check if new price is valid
    if new_price <= 0:
        messages.error(request, "Error: New Price is invalid. Kindly input a value greater than 0.")
        context["page_loaded"] = False
        return render(request, "HaoTasty/profitability_assessment.html",context)

    # Check data sufficiency
    orderlines = OrderLineT.objects.filter(menu_item_id=menu_item_id)
    data_count = orderlines.count()
    print(menu_item_id)

    if data_count <= 2:
        messages.error(request, f"Insufficient data: {data_count} data points found for this menu item.")
        context["page_loaded"] = False
        return render(request, "HaoTasty/profitability_assessment.html",context)
    elif data_count < 250:
        messages.warning(request, f"Note: Only {data_count} data points available. Analysis may be less reliable.")
        # Run profitability assessment
        context = assess_profitability(request, menu_item_id, new_price, elasticity)
        context["page_loaded"] = True
        print(context)

    else:
        # Run profitability assessment
        context = assess_profitability(request, menu_item_id, new_price, elasticity)
        context["page_loaded"] = True
        print(context)


    # Determine success message
    if new_price == float(old_price):
        messages.success(request, f"The projected profitability for Menu Item: {menu_item.menu_item_name} has been generated with the same price ₱{new_price:.2f} at elasticity value of {elasticity}.")
    else:
        messages.success(request, f"The projected profitability for Menu Item: {menu_item.menu_item_name} has been generated with the new price ₱{new_price:.2f} from the old price ₱{old_price:.2f} at elasticity value of {elasticity}.")

    return render(request, "HaoTasty/profitability_assessment.html", context)




# ---------- 


@superuser_required
def landingpage(request):
    date = datetime.now().strftime("%m/%d/%Y")
    return render(request, "HaoTasty/landingpage.html", {'date':date})


# --- Sales Input ---------

## I think this one is redundant and can be removed -T
def order_input(request):
    return render(request, 'HaoTasty/order_input.html')

@login_required(login_url='login_user')
def create_order(request):
    menu_items = MenuItemT.objects.all()

    return render(request, 'HaoTasty/order_input.html', {'menu_items': menu_items})

@login_required(login_url='login_user')
def make_order(request):
    request.session.pop("order_session", None) 
    order_session = request.session.get("order_session", {"order_content": []})
    if request.method == "POST":
        menu_item_name = request.POST.getlist("menu_item_name[]")
        menu_item_price = request.POST.getlist("menu_item_price[]")
        menu_quantity = request.POST.getlist("order_quantity[]", "0")
        menu_item_id = request.POST.getlist("menu_item_id[]")

        for x in range(len(menu_item_name)):
            name = menu_item_name[x]
            menu_id = menu_item_id[x]
            price = float(menu_item_price[x])
            quantity = int(menu_quantity[x])

            if quantity > 0:
                item_found = False
                for item in order_session['order_content']:
                    if item['menu_item_name'] == name:
                        item['menu_quantity'] += quantity
                        item['total_price'] += quantity*price
                        item_found = True
                        break

                if not item_found:
                    order_session["order_content"].append({
                        "menu_quantity": quantity, 
                        "menu_item_name": name,
                        "menu_item_price": price,
                        "menu_item_id": menu_id,
                        "total_price": quantity*price
                        })

    request.session["order_session"] = order_session  # Save order in session
    request.session.modified = True  # Mark session as modified
    if request.POST.get('cash'):
        return redirect('cash_sales')
    elif request.POST.get('gcash'):
        return redirect('gcash_sales')

@login_required(login_url='login_user')
def cash_sales(request):
    order_session= request.session.get("order_session", {"order_content": []})  # Get order data
    order_content = order_session.get("order_content", [])
    grand_total = sum(item['total_price'] for item in order_content)

    return render(request, "HaoTasty/cashsales.html", {"order": order_content, "grand_total": grand_total})

@login_required(login_url='login_user')
def gcash_sales(request):
    order_session= request.session.get("order_session", {"order_content": []})  # Get order data
    order_content = order_session.get("order_content", [])
    grand_total = sum(item['total_price'] for item in order_content)

    return render(request, 'HaoTasty/gcashsales.html', {"order": order_content, "grand_total": grand_total})

@login_required(login_url='login_user')
def complete_payment(request):
    order_data = request.session.get("order_session", {"order_content": []})
    payment_type = request.GET.get("payment_type") # Will get payment type from URL
    reference_num = request.POST.get("reference_num", None)
    order_total = sum(item["total_price"] for item in order_data["order_content"])

    # If there are no items to save it will return to the order input screen
    if not order_data["order_content"]: 
        return redirect("order_input")
    
    reference_num = str(request.POST.get("reference_num", "")).strip() or None


    with transaction.atomic():
        ## Creating OrderT entry
        new_order = OrderT.objects.create(
            payment_type = payment_type,
            order_timestamp=now(),
            reference_num = reference_num,
            order_total = order_total
        )

        ## Creating OrderLineT entries
        order_lines = [
            OrderLineT(
                order_id = new_order.order_id,
                menu_item_id = item["menu_item_id"],
                order_quantity = item["menu_quantity"],
                order_subtotal = item["menu_quantity"]*item["menu_item_price"] # TO save subtotal
            )
            for item in order_data["order_content"]
        ]
        OrderLineT.objects.bulk_create(order_lines)

    ## Clear session order data
    request.session.pop("order_session", None)
    request.session.modified = True

    return redirect("order_input")

def access_session(request):
    response = "<h1>Welcome to Sessions of dataflair</h1><br>"
    if request.session.get('name'):
        response += "Name : {0} <br>".format(request.session.get('order_session'))
    if request.session.get('password'):
        response += "Password : {0} <br>".format(request.session.get('password'))
        return HttpResponse(response)
    else:
        return redirect('create/')

def create_session(request):
    request.session['name'] = 'username'
    request.session['password'] = 'password123'
    return HttpResponse("<h1>dataflair<br> the session is set</h1>")

def delete_session(request):
    try:
        del request.session['order_session']
        del request.session['password']
    except KeyError:
        pass
    return HttpResponse("<h1>dataflair<br>Session Data cleared</h1>")


