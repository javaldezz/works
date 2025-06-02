import csv
import os
from django.conf import settings  # type: ignore | imports 
from django.shortcuts import render  # type: ignore | imports 
from .forms import VenueAvailabilityForm
from datetime import datetime, date


# Load data from CSV files -------

def load_reservations_data():
    available_slots = []

    # Get the file path using BASE_DIR
    slots_data_file = os.path.join(settings.BASE_DIR, 'data/MOCK_DATA.csv')  

    # Load MOCK_DATA.csv
    with open(slots_data_file, mode='r') as slots_file:
        csv_reader = csv.DictReader(slots_file)
        for row in csv_reader:
            available_slots.append(row)

    # Print to show row structure and confirm with sample data
    if available_slots:
        # Columns names
        print(f"Columns in CSV: {available_slots[0].keys()}")

        # Check the first row of data
        print(f"First row data: {available_slots[0]} \n")  
    return available_slots

# Search Algorithm -------

def binary_search(arr, key, index):
    """
    Binary Search to find the Index of the first element greater than or equal to the key.
    - `reservation_date` will be compared as a datetime object.
    - `target_time` will be compared as a string.
    - `capacity` will be compared as an integer.

    As each feature has a different data type, the key must be adjusted to compare values without errors.
    """
    low, high = 0, len(arr) - 1
    
    # Convert the key for Comparison
    if index == 'reservation_date':
        # If the key is already a datetime object, no need to convert
        if isinstance(key, date):  
            key = datetime(key.year, key.month, key.day)  # Convert it to datetime
        else:
            key = datetime.strptime(key, '%Y-%m-%d')  # Convert the key to datetime

    elif index == 'capacity':
        key = int(key)  # Convert the key to integer 

    # Search Algorithm-proper    

    while low <= high:
        mid = (low + high) // 2
    
        # Convert the element for comparison
        if index == 'reservation_date':
            # If the reservation_date is already a datetime object, skip strptime
            if isinstance(arr[mid][index], datetime):
                mid_value = arr[mid][index]
            elif isinstance(arr[mid][index], date):  # Handle datetime.date as well
                mid_value = datetime(arr[mid][index].year, arr[mid][index].month, arr[mid][index].day)
            else:
                mid_value = datetime.strptime(arr[mid][index], '%Y-%m-%d')

        elif index == 'capacity':
            mid_value = int(arr[mid][index])

        else:  # target_time
            mid_value = arr[mid][index]
        
        # Binary Search comparisons
        if mid_value < key:
            low = mid + 1
        else:
            high = mid - 1
    
    return low

# Sorting Algorithm -------

def merge_sort(data, key):
    """
    Merge sort to sort a list of dictionaries by a specific key given as a parameter.
    """
    if len(data) <= 1:
        return data
    
    mid = len(data) // 2
    left = merge_sort(data[:mid], key)
    right = merge_sort(data[mid:], key)
    
    return merge(left, right, key)

def merge(left, right, key):
    """
    Merge two sorted lists.
    """
    merged = []
    i, j = 0, 0
    while i < len(left) and j < len(right):
        if left[i][key] <= right[j][key]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    merged += left[i:]
    merged += right[j:]
    return merged

def filter_and_sort(slots, key, value, exact_match=True):
    """
    Sort the slots by a specific key using merge sort, perform a binary search, 
    and filter the slots. Supports filtering for exact matches or greater-than values.
    """
    # Sort the slots by the specified key
    slots = merge_sort(slots, key)
    
    # Perform binary search to find the insertion position
    insert_position = binary_search(slots, value, key)
    slots = slots[insert_position:]

    if exact_match:
        # Keep only those slots where the key matches the value exactly
        slots = [slot for slot in slots if str(slot[key]) == str(value)]
    else:
        # For non-exact matches (e.g., capacity >= value)
        slots = [slot for slot in slots if int(slot[key]) >= int(value)]
    
    return slots

# Tool-Proper -------

def venueavailability(request):
    # Initialize variables for filtering, sorting, and pagination
    sort_by = request.GET.get('sort_by', 'Capacity')  # Default to sorting by capacity
    order = request.GET.get('order', 'Ascending')  # Default to sorting by capacity

    # Load available slots (venues and their times)
    available_slots = load_reservations_data()

    # Handle form submission and validation
    form = VenueAvailabilityForm(request.POST or None)
    filtered_slots = available_slots

    if form.is_valid():
        capacity = form.cleaned_data.get('capacity')
        date = form.cleaned_data.get('date')
        target_time = form.cleaned_data.get('target_time')
        sort_by = form.cleaned_data.get('sort_by')
        order = form.cleaned_data.get('order')

        # Print statement to check the form values
        print(f"Form submitted with: Capacity={capacity}, Date={date}, Target Time={target_time}")

        # Apply filtering and sorting for each variable
        if date:
            filtered_slots = filter_and_sort(filtered_slots, 'reservation_date', date)
        
        if target_time:
            filtered_slots = filter_and_sort(filtered_slots, 'target_time', target_time)
        
        if capacity:
            filtered_slots = filter_and_sort(filtered_slots, 'capacity', int(capacity), exact_match=False)

    # Add another print to check filtered slots before rendering
    print(f"Filtered slots: {len(filtered_slots)} available slots found \n")

    # Sorting the query set based on 'sort_by' and 'order'
    if sort_by:

        # Sort using merge_sort based on the sort_by parameter
        filtered_slots = merge_sort(filtered_slots, sort_by.lower())

        # Reversing the order if necessary (Descending order)
        if order == "Descending":
            filtered_slots = filtered_slots[::-1]  # Reversing the list in place

    context = {
        'form': form,
        'available_slots': filtered_slots,
        'sort_by': sort_by,
        'order': order,
    }

    return render(request, 'msys30app/venueavailability.html', context)

# Load Home Page -------

def home_view(request): 
    return render(request, 'msys30app/home.html') 


# Load FAQs Page -------

def faqs_view(request): 
    return render(request, 'msys30app/faqs.html')
