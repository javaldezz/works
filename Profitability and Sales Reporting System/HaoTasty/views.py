from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.db.models import Sum, Count, F, ExpressionWrapper, FloatField 
from .models import ExpenseCatT, ExpenseT, MenuItemT, OrderLineT, OrderT, UserT
from datetime import datetime, timedelta
from django.contrib import messages, sessions 
from itertools import combinations
from collections import Counter
from decimal import Decimal
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.functions import TruncDate, Coalesce, TruncMonth, ExtractYear, TruncYear
from .forms import MenuItemForm
from django.http import JsonResponse



def login(request): #add login logic
    return render(request, 'HaoTasty/login.html')

def cashsales(request):
    return render(request, 'HaoTasty/cashsales.html')

def gcashsales(request):
    return render(request, 'HaoTasty/gcashsales.html')

def input_expenses(request):
    return render(request, 'HaoTasty/input_expenses.html')

def input_expenses_admin(request):
    return render(request, 'HaoTasty/input_expenses_admin.html')

def manage_expenses(request):
    return render(request, 'HaoTasty/manage_expenses.html')

def create_expense_category(request):
    return render(request, 'HaoTasty/create_expense_category.html')

def update_expense_category(request):
    return render(request, 'HaoTasty/update_expense_category.html')

def expense_list(request):
    return render(request, 'HaoTasty/expense_list.html')

def manage_users(request): 
    return render(request, 'HaoTasty/users_dashboard.html')

def add_users(request): 
    return render(request, 'HaoTasty/add_users.html')

def delete_users(request): 
    return render(request, 'HaoTasty/delete_users.html')

def update_users(request): 
    return render(request, 'HaoTasty/update_users.html')

def data_dashboard(request): 
    return render(request, 'HaoTasty/data_dashboard.html')

def restore(request): 
    return render(request, 'HaoTasty/restore.html')

def view_reports(request): 
    return render(request, 'HaoTasty/view_reports.html')

def menu_dashboard(request): 
    menu_items = MenuItemT.objects.all()
    return render(request, 'HaoTasty/menu_dashboard.html',{'menu_items': menu_items})

def add_menu(request):
    menu_items = MenuItemT.objects.all()  
    form = MenuItemForm()  # Create an empty form for display

    if request.method == "POST":
        form = MenuItemForm(request.POST)  # Populate form with POST data
        if form.is_valid():
            menu_item = MenuItemT.objects.create(
                menu_item_name=form.cleaned_data["menu_item_name"],
                menu_item_price=form.cleaned_data["menu_item_price"],
                menu_item_cost=form.cleaned_data["menu_item_cost"],
                item_availability_status=form.cleaned_data["item_availability_status"],
            )
            messages.success(request, "Menu item added successfully!")
            return redirect("add_menu")
        else:
            print(form.errors)  
            return JsonResponse({"error": "Invalid form data"}, status=400)
    return render(request, "HaoTasty/add_menu.html", {"menu_items": menu_items, "form": form})

def update_menu(request, menu_item_id=None):
    menu_items = MenuItemT.objects.all()

    if menu_item_id:
        menu_item = get_object_or_404(MenuItemT, pk=menu_item_id)

    if request.method == "POST":
        try:
            # Extract multiple menu items from request.POST
            menu_item_ids = request.POST.getlist("menu_item_id[]")
            menu_item_names = request.POST.getlist("menu_item_name[]")
            menu_item_prices = request.POST.getlist("menu_item_price[]")
            menu_item_statuses = request.POST.getlist("item_availability_status[]")

            # Ensure lists have the same length
            if not (len(menu_item_ids) == len(menu_item_names) == len(menu_item_prices) == len(menu_item_statuses)):
                return JsonResponse({"error": "Mismatched form data"}, status=400)

            # Update menu items
            for i in range(len(menu_item_ids)):
                menu_item = MenuItemT.objects.get(id=menu_item_ids[i])
                menu_item.menu_item_name = menu_item_names[i]
                menu_item.menu_item_price = float(menu_item_prices[i])
                menu_item.item_availability_status = menu_item_statuses[i]
                menu_item.save()
                print(f"Success: {menu_item}")

            return render(request, 'HaoTasty/update_menu.html', {
                'menu_items': menu_items,
                'message': "Menu updated successfully!"
            })

        except MenuItemT.DoesNotExist:
            return JsonResponse({"error": "Menu item not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return render(request, 'HaoTasty/update_menu.html', {'menu_items': menu_items})

def delete_menu(request, menu_item_id):
    menu_item = get_object_or_404(MenuItemT, menu_item_id=menu_item_id)
    print(menu_item.item_availability_status)
    menu_item.item_availability_status = 0
    print(menu_item.item_availability_status)
    print(type(menu_item.menu_item_profit))
    menu_item.save()
    print(f"Switched to discontinued: {menu_item}")
    return redirect("update_menu")  # Redirect back to the menu after deletion


# Report Logic 

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


def filter_order_lines(start_date, filter_type):
    """ Returns filtered OrderLineT queryset based on the date filter. """
    queryset = OrderLineT.objects.all()  # Default to all order lines

    if filter_type == "cumulative":
        return queryset  # No filtering, return everything

    if not start_date:
        return queryset  # Ensure it always returns a queryset

    if filter_type == "daily":
        return queryset.annotate(order_date=TruncDate("order__order_timestamp")).filter(order_date=start_date)
    elif filter_type == "weekly":
        return queryset.filter(
            order__order_timestamp__date__gte=start_date,
            order__order_timestamp__date__lt=start_date + timedelta(days=7)
        )
    elif filter_type == "monthly":
        return queryset.filter(
            order__order_timestamp__date__gte=start_date,
            order__order_timestamp__date__lt=(start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        )
    elif filter_type == "yearly":
        return queryset.filter(order__order_timestamp__year=start_date.year)
    
    return queryset  # Fallback return value

def get_sales_data():
    """ Returns sales data including total orders and revenue per menu item. """
    return list(MenuItemT.objects.annotate(
        total_orders=Count("orderlinet"),
        total_revenue=Coalesce(Sum(F("orderlinet__order_quantity") * F("menu_item_price")), Decimal("0.00"))
    ).values("menu_item_name", "total_orders", "menu_item_price", "total_revenue"))


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

def get_annual_revenue():
    """ Returns aggregated monthly revenue grouped by year. """
    return list(OrderT.objects
                .annotate(year=TruncYear('order_timestamp'), month=TruncMonth('order_timestamp'))
                .values('year', 'month')
                .annotate(total_revenue=Sum(F("orderlinet__order_quantity") * F("orderlinet__menu_item__menu_item_price")))
                .order_by('year', 'month'))

def landingpage(request):
    menu_items = MenuItemT.objects.all()

    filter_type = request.GET.get("filter", "cumulative")
    date_selected = request.GET.get("datePicker")

    today = datetime.today().date()
    start_date = get_start_date(filter_type, date_selected)

    order_lines = OrderLineT.objects.all()
    if start_date:
        order_lines = filter_order_lines(start_date, filter_type)

    # Compute sales data
    sales_data = get_sales_data()

    # Compute total revenue
    total_revenue = order_lines.aggregate(
        total=Sum(F("order_quantity") * F("menu_item__menu_item_price"))
    )["total"] or Decimal("0.00")

    # Best-selling and worst-selling menu items
    best_selling_item = sales_data[0] if sales_data else None
    worst_selling_item = sales_data[-1] if sales_data else None

    # Frequently Bought Together (FBT) - Top 3 pairs
    top_3_fbt = calculate_fbt(order_lines)

    # Annual Revenue
    annual_revenue = get_annual_revenue()

    # Convert Decimal values for JSON serialization
    total_revenue = str(total_revenue)
    for item in annual_revenue:
        item["total_revenue"] = str(item["total_revenue"])  # Convert Decimal to string
        item["year"] = item["year"].strftime("%Y") if item["year"] else "No Year"
        item["month"] = item["month"].strftime("%m") if item["month"] else "No Month"

    context = {
        "menu_items": menu_items,
        "sales": json.dumps(sales_data, default=str),
        "total_revenue": total_revenue,
        "best_selling": best_selling_item,
        "worst_selling": worst_selling_item,
        "top_fbt": json.dumps(top_3_fbt),
        "annual_revenue": json.dumps(annual_revenue, default=str),
        "filter_type": filter_type,
        "date_selected": date_selected or today.strftime("%Y-%m-%d"),
        "order_lines": order_lines,
        "start_date": start_date,
    }

    print(context)

    return render(request, "HaoTasty/landingpage.html", context)


def order_input(request):
    return render(request, 'HaoTasty/order_input.html')

def create_order(request):
    menu_items = MenuItemT.objects.all()

    return render(request, 'HaoTasty/order_input.html', {'menu_items': menu_items})

def make_order(request):
    request.session.flush()
    order_session = request.session.get("order_session", {"order_content": []})
    if request.method == "POST":
        menu_item_name = request.POST.getlist("menu_item_name[]")
        menu_item_price = request.POST.getlist("menu_item_price[]")
        menu_quantity = request.POST.getlist("order_quantity[]", "0")

        for x in range(len(menu_item_name)):
            name = menu_item_name[x]
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
                        "total_price": quantity*price
                        })

    request.session["order_session"] = order_session  # Save order in session
    request.session.modified = True  # Mark session as modified
    if request.POST.get('cash'):
        return redirect('cash_sales')
    elif request.POST.get('gcash'):
        return redirect('gcashsales')
    # return render(request, 'HaoTasty/order_input.html', {'menu_items': menu_items})

def testpage(request):
    expense_category_objects = ExpenseCatT.objects.all()
    orderline_objects = OrderLineT.objects.all()
    test_input = "Burger"
    filtered_output = orderline_objects.filter(menu_item__menu_item_name = test_input)
    return render(request, 'HaoTasty/testpage.html', {'expense_cat': expense_category_objects, 'order_line': filtered_output})

def create_testpage(request):
    expense_category_objects = ExpenseCatT.objects.all()
    if request.method == "POST":
        new_expense_cat_name = request.POST.get('input_field_1')
        new_expense_cat_timestamp = datetime.datetime.now()

        if not (new_expense_cat_name):
            messages.info(request, 'All fields are required.')
            return redirect('create_testpage')
        else:
            ExpenseCatT.objects.create(expense_cat_name=new_expense_cat_name, category_timestamp = new_expense_cat_timestamp)
            messages.success(request, 'Expense Category has been created.')
            return redirect('testpage')
        
    return render(request, 'HaoTasty/testpage.html', {'expense_cat': expense_category_objects})

def modify_testpage(request):
    if request.method == "POST":
        expense_cat_to_modify = request.POST.get('to_modify')
        new_expense_cat_name = request.POST.get('input_field_2')
        new_expense_cat_timestamp = datetime.datetime.now()

        if not (new_expense_cat_name):
            messages.info(request, 'All fields are required.')
            return redirect('modify_testpage')
        
        else:
            if ExpenseCatT.objects.filter(expense_cat_name=new_expense_cat_name).exists():
                messages.info(request, 'Category with this name already exists.')
                return redirect('testpage')

            # Update the employee object
            ExpenseCatT.objects.filter(expense_cat_name=expense_cat_to_modify).update(expense_cat_name=new_expense_cat_name, category_timestamp = new_expense_cat_timestamp)
            messages.success(request, 'Category has been updated.')
            return redirect('testpage')
    else:
        return redirect('testpage')
        

def delete_testpage(request):
    expense_cat_to_delete = request.POST.get('to_delete')
    ExpenseCatT.objects.filter(expense_cat_name=expense_cat_to_delete).delete()
    messages.info(request, 'Category has been deleted.')
    return redirect('testpage')

# def test_cash_sales(request):
#     order_session= request.session.get("order_session", {"order_content": []})  # Get order data
#     order_content = order_session.get("order_content", [])
#     grand_total = sum(item['total_price'] for item in order_content)

#     # return render(request, "HaoTasty/test_cash_sales.html", {"order": order_content, "grand_total": grand_total})
#     return render(request, "HaoTasty/cashsales.html", {"order": order_content, "grand_total": grand_total})

def cash_sales(request):
    order_session= request.session.get("order_session", {"order_content": []})  # Get order data
    order_content = order_session.get("order_content", [])
    grand_total = sum(item['total_price'] for item in order_content)

    return render(request, "HaoTasty/cashsales.html", {"order": order_content, "grand_total": grand_total})

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


