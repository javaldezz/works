"""
URL configuration for badproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', views.login, name='login'), 
    path('cash_sales', views.cash_sales, name='cash_sales'),
    path('gcashsales', views.gcashsales, name='gcashsales'),
    path("landingpage", views.landingpage, name="landingpage"), #temporary default route for DEMO, change "" when login is implement
    path("testpage", views.testpage, name='testpage'),
    path("order_input", views.create_order, name='order_input'),
    path('create_testpage', views.create_testpage, name='create_testpage'),
    path('modify_testpage', views.modify_testpage, name='modify_testpage'),
    path('delete_testpage', views.delete_testpage, name='delete_testpage'),
    # path('test_cash_sales', views.test_cash_sales, name='test_cash_sales'),
    path('make_order', views.make_order, name='make_order'),
    path('access/', views.access_session, name='access'),
    path('create/', views.create_session, name='create'),
    path('delete/', views.delete_session, name='delete'),

    # reports 
    path("view_reports", views.view_reports, name='view_reports'),

    #expenses
    path("input_expenses", views.input_expenses, name='input_expenses'),
    path("input_expenses_admin", views.input_expenses_admin, name='input_expenses_admin'),
    path("manage_expenses", views.manage_expenses, name='manage_expenses'),
    path("expense_list", views.expense_list, name='expense_list'),
    
    #expense category
    path("create_expense_category", views.create_expense_category, name='create_expense_category'),
    path("update_expense_category", views.update_expense_category, name='update_expense_category'),
    
    #menuitem
    path('menu_dashboard/', views.menu_dashboard, name='menu_dashboard'),
    path('add_menu/', views.add_menu, name='add_menu'),
    path('update_menu/', views.update_menu, name='update_menu'),
    path('delete-menu/<int:menu_item_id>/',views.delete_menu, name='delete_menu'),
    
    #manageusers
    path('manage_users/', views.manage_users, name='manage_users'),
    path('add_users/', views.add_users, name='add_users'),
    path('delete_users/', views.delete_users, name='delete_users'),
    path('update_users/', views.update_users, name='update_users'),

    #backup and restore
    path('data_dashboard/', views.data_dashboard, name='data_dashboard'), #the backup happens here acc to UCD
    path('restore/', views.restore, name='restore'),
]
