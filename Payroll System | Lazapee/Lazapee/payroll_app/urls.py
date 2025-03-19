from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.employees, name='employees'),
    path('employees', views.employees, name='employees'),
    path('create_employee', views.create_employee, name='create_employee'),
    path('view_employee/<str:id_number>/', views.view_employee, name='view_employee'),
    path('update_employee/<str:id_number>/', views.update_employee, name='update_employee'),
    path('delete_employee/<str:id_number>/', views.delete_employee, name='delete_employee'),
    path('update_overtime/<str:id_number>/', views.update_overtime, name='update_overtime'),
    path('payslip', views.payslip, name='payslip'),
    path('view_payslip/<int:pk>/', views.view_payslip, name='view_payslip'),
    path('update_payslip/<int:pk>/', views.update_payslip, name='update_payslip'),
    path('delete_payslip/<int:pk>/', views.delete_payslip, name='delete_payslip'),
    ]
