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


   # login
   path('', views.login_user, name='login_user'),
   path('login_redirect/', views.login_redirect, name='login_redirect'),
   path('logout/', views.logout_user, name='logout_user'),


   # sales checkout
   path('cash_sales', views.cash_sales, name='cash_sales'),
   path('gcash_sales', views.gcash_sales, name='gcash_sales'),


   # loading order page
   path("order_input", views.create_order, name='order_input'),


   # code for making the order and saving data for payment
   path('make_order', views.make_order, name='make_order'),


   # code for passing payment data to database
   path('complete_payment', views.complete_payment, name='complete_payment'),
  
   # for session access
   path('access/', views.access_session, name='access'),
   path('create/', views.create_session, name='create'),
   path('delete/', views.delete_session, name='delete'),


   #sales and expense report, report dashboard
   path("landingpage", views.landingpage, name="landingpage"), #reports dashboard
   path("sales_report/", views.sales_report, name='sales_report'),
   path("expense_report/", views.expense_report, name='expense_report'),


   #forecasts and profitability assessment
   path("sales_forecast/", views.sales_forecast, name='sales_forecast'),
   path("expense_forecast/", views.expense_forecast, name='expense_forecast'),
   path("profitability_assessment/", views.profitability_assessment, name='profitability_assessment'),


   #sales
   path("sales_list", views.sales_list, name='sales_list'),
  
   #expenses
   path("input_expenses/", views.input_expenses, name='input_expenses'),
   path("expense_list", views.expense_list, name='expense_list'),
   path("delete_expense/<int:expense_id>/", views.delete_expenses, name="delete_expense"),
  
   #expense category
   path("create_expense_category", views.create_expense_category, name='create_expense_category'),
   path("update_expense_category", views.update_expense_category, name='update_expense_category'),
   path("manage_expense_category", views.manage_expense_category, name='manage_expense_category'),
   path("delete_expense_category/<int:expense_cat_id>/", views.delete_expense_category, name='delete_expense_category'),
  
   #menuitem
   path('menu_dashboard', views.menu_dashboard, name='menu_dashboard'),
   path('add_menu/', views.add_menu, name='add_menu'),
   path('update_menu/', views.update_menu, name='update_menu'),
   path('delete-menu/<int:menu_item_id>/',views.delete_menu, name='delete_menu'),


  
   #manageusers
   path('profile_employee/', views.profile_employee, name='profile_employee'),
   path('manage_users/', views.manage_users, name='manage_users'),
   path('add_users/', views.add_users, name='add_users'),
   path('delete_users/', views.delete_users, name='delete_users'),
   path('update_users/<int:user_id>/', views.update_users, name='update_users'),


   #backup and restore
   path('data_dashboard/', views.data_dashboard, name='data_dashboard'), #the backup happens here acc to UCD
   path('create_backup', views.create_backup, name='create_backup'),
   path('restore/', views.restore, name='restore'),
   path('delete-backup/', views.delete_backup, name='delete_backup'),
   path('download-backup/<str:filename>/', views.download_backup, name='download_backup'),

]


