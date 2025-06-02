from django.urls import path 
from .views import venueavailability, home_view, faqs_view, load_reservations_data
urlpatterns = [
     path('', home_view, name='home'),

     path('venueavailability/',venueavailability, name='tool'), 
     path('faqs/',faqs_view, name='faqs'), 
     path('load_reservations/', load_reservations_data, name='load_reservations')
     ]