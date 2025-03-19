from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Case, CharField, Value, When
from .models import Employee, Payslip 
from .forms import EmployeeForm, PayslipForm
import re

month_mapping = {
    'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
    'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
}

month_equivalent = Case(
    *[When(month=name, then=Value(number)) for name, number in month_mapping.items()],
    output_field=CharField()
)

# CRUD Features for Employees

def create_employee(request):
    employees_objects = Employee.objects.all()
    if request.method == "POST":
        name = request.POST.get("name")
        id_number = request.POST.get("id_number") 
        rate = request.POST.get("rate") 
        overtime_pay = request.POST.get("overtime_pay") 
        allowance = request.POST.get("allowance") 

        if allowance.strip() == "" or allowance is None or not allowance:
            allowance = 0
        if overtime_pay is None or not overtime_pay:
            overtime_pay = 0
        if int(rate) < 0: 
            messages.error(request, 'Employee Rate cannot be negative. Please enter a valid rate.')
            return redirect('create_employee')

        if Employee.objects.filter(id_number=id_number).exists():
            messages.error(request, 'Employee ID Number already exists. Please enter a unique ID Number.')
            return redirect('create_employee')
        elif not bool(re.match(r'^\d{6}$', id_number)):
                messages.error(request, 'Employee creation failed. Incorrect ID number format, 6 Consecutive Digits.')
        else:
            Employee.objects.create(name=name,id_number=id_number,rate=float(rate),overtime_pay=float(overtime_pay),allowance=float(allowance))
            messages.success(request, 'Employee created successfully.')
            return redirect('create_employee')
    return render(request, 'payroll_app/create_employee.html', {'employees_objects':employees_objects})

def view_employee(request,id_number):
    d = get_object_or_404(Employee, id_number=id_number)
    payslip_objects = Payslip.objects.filter(id_number=id_number).annotate(month_number=month_equivalent).order_by('year', 'month_number','pay_cycle')
    return render(request, 'payroll_app/view_employee.html', {'d': d, 'payslip_objects':payslip_objects})

def employees(request):
    employees_objects = Employee.objects.all()
    return render(request, 'payroll_app/employees.html', {'employees_objects':employees_objects})

def update_overtime(request, id_number):
    if request.method == 'POST':
        employee = Employee.objects.get(id_number=id_number)
        overtime_hours = request.POST.get('add_overtime')
        try:
            overtime_hours = float(overtime_hours)
            if overtime_hours > 0:  
                employee.overtime_hours += overtime_hours
                employee.getOvertimePay()
                employee.save()
                messages.success(request, f'{overtime_hours} overtime hours added for {employee.name}.')
            else:
                messages.error(request, 'Please enter a valid non-negative number for overtime hours.')
        except ValueError:
            messages.error(request, 'Please enter a valid number for overtime hours.')
    return redirect('employees')

def update_employee(request, id_number):
    employee = get_object_or_404(Employee, id_number=id_number)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        new_id_number = request.POST.get("id_number")
        allowance = request.POST.get("allowance")
          
        if new_id_number != id_number:
            if Employee.objects.filter(id_number=new_id_number).exists():
                messages.error(request, 'Employee update failed. ID number already exists.')
                return redirect('update_employee', id_number=id_number)
            elif not bool(re.match(r'^\d{6}$', new_id_number)):
                messages.error(request, 'Employee update failed. Incorrect ID number format, 6 Consecutive Digits.')
                return redirect('update_employee', id_number=id_number)
            else: 
                with transaction.atomic():
                    employee.id_number = new_id_number
                    employee.save()
                    
                    old_employee = Employee.objects.create(
                        name=employee.name,
                        id_number=id_number,
                        rate=employee.rate,
                        overtime_hours=employee.overtime_hours,
                        overtime_pay=employee.overtime_pay,
                        allowance=employee.allowance
                    )

                    Payslip.objects.filter(id_number=id_number).update(id_number=new_id_number)
                    old_employee.delete()

        if form.is_valid():
            form.save()
            if not allowance or allowance == "" or allowance is None:
                employee.allowance = 0
                employee.save()
 

            messages.success(request, f'Employee {employee.id_number}: {employee.name} updated successfully.')
            return redirect('employees')
        else:
            messages.error(request, 'Employee update failed. Rate and Allowance (optional) must be a number.')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'payroll_app/update_employee.html', {'form': form, 'employee': employee})


def delete_employee(request, id_number):
    employee = get_object_or_404(Employee, id_number=id_number)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Employee deleted successfully.')
        return redirect('employees')  
    return render(request, 'payroll_app/delete_employee.html', {'employee': employee})



# CRUD Features for Payslip

def payslip(request):
    payslip_objects = Payslip.objects.all()
    employees_objects = Employee.objects.all()

    if request.method == "POST":
        if 'payslip' in request.POST:
            id_number_a = request.POST.get("id_number") 
            month = request.POST.get("month")
            year = request.POST.get("year") 
            cycle = int(request.POST.get("cycle"))  

            if not bool(re.match(r'^\d{4}$', year)):
                messages.error(request, 'Payslip creation failed. Incorrect year format, must be 4 consecutive digits.')
                return redirect('payslip')

            if id_number_a == "All Employees":
                existing_payslips = Payslip.objects.filter(month=month, year=year, pay_cycle=str(cycle))
                if existing_payslips.exists():
                    id_numbers = ', '.join(str(p.id_number.id_number) for p in existing_payslips)
                    messages.error(request, f'Payslips already exist for ID numbers: {id_numbers}.')
                else:
                    for employee in employees_objects:
                        Payslip.objects.create(id_number=employee, month=month, year=year, pay_cycle=cycle)
                        employee.resetOvertime()
                    messages.success(request, 'Payslips created successfully for all employees.')
                return redirect('payslip') 

            else:
                id_number = Employee.objects.get(id_number=id_number_a)
                if Payslip.objects.filter(id_number=id_number, month=month, year=year, pay_cycle=cycle).exists():
                    messages.error(request, 'Payslip already exists.')
                else:
                    Payslip.objects.create(id_number=id_number, month=month, year=year, pay_cycle=cycle)             
                    id_number.resetOvertime()
                    messages.success(request, 'Payslip created successfully.')
                return redirect('payslip')
            
        elif 'sort_payslip' in request.POST:
            sort = request.POST.get("sort")
            request.session['sort'] = sort 
            if sort == "By ID Number":
                payslip_objects = Payslip.objects.all().order_by('id_number')

            elif sort == "By Date":
                payslip_objects = Payslip.objects.all().annotate(month_number=month_equivalent).order_by('year', 'month_number','pay_cycle')

            elif sort == "By Total Pay":
                payslip_objects = sorted(Payslip.objects.all(), key=lambda x: x.total_pay)
            
            return render(request, 'payroll_app/payslip.html', {'payslip_objects': payslip_objects, 'employees_objects': employees_objects})

    return render(request, 'payroll_app/payslip.html', {'payslip_objects': payslip_objects, 'employees_objects': employees_objects})

def view_payslip(request,pk):
    payslip = get_object_or_404(Payslip, pk=pk)
    return render(request, 'payroll_app/view_payslip.html', {'payslip': payslip})


def update_payslip(request,pk):
    payslip = get_object_or_404(Payslip, pk=pk)
    employees_objects = Employee.objects.all()

    if request.method == 'POST':
        form = PayslipForm(request.POST, instance=payslip)
        id_number_a = request.POST.get("id_number")
        id_number = Employee.objects.get(id_number=id_number_a)
        month = request.POST.get("month")  
        year = request.POST.get("year")
        cycle = request.POST.get("cycle") 

        if Payslip.objects.filter(id_number=id_number_a,month=month,year=year,pay_cycle=cycle).exists(): 
            messages.error(request, 'Payslip update failed. Payslip already exists.')
            return redirect('update_payslip', pk=pk)

        if not bool(re.match(r'^\d{4}$', year)):
            messages.error(request, 'Payslip update failed. Incorrect year format, must be 4 consecutive digits.')
            return redirect('update_payslip', pk=pk)

        Payslip.objects.filter(pk=pk).update(id_number=id_number, month=month,year=year,pay_cycle=cycle)

        if Payslip.objects.filter(id_number=id_number, month=month,year=year,pay_cycle=cycle).exists():
            messages.success(request, f'Payslip  {payslip.pk} updated successfully for Employee {payslip.id_number.id_number}: {payslip.id_number.name}.')
            return redirect('payslip')
        else:
            messages.error(request, 'Payslip update failed.')

    else:
        form = PayslipForm(instance=payslip)

    return render(request, 'payroll_app/update_payslip.html', {'form': form, 'payslip': payslip, 'employees_objects': employees_objects})


def delete_payslip(request, pk):
    payslip = get_object_or_404(Payslip, pk=pk)
    if request.method == 'POST':
        payslip.delete()
        messages.success(request, 'Payslip deleted successfully.')
        return redirect('payslip')  
    return render(request, 'payroll_app/delete_payslip.html', {'payslip': payslip})
