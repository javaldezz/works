from django import forms
from .models import Employee, Payslip

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['name', 'id_number', 'rate', 'overtime_pay', 'allowance'] 

class PayslipForm(forms.ModelForm):
    class Meta:
        model = Payslip
        fields = ['id_number', 'month', 'year', 'pay_cycle'] 

