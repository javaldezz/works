# Venue Availability System

## Table of Contents

- [Business Understanding](#business-understanding)
- [Data Understanding](#data-understanding)
- [Screenshots of Visualizations/Results](#screenshots-of-visualizationsresults)
- [Technologies](#technologies)
- [Setup](#setup)
- [Approach](#approach)
- [Future Enhancements](#future-enhancements)
- [Contact](#contact)
- [Acknowledgments](#acknowledgments)

## Business Understanding

<details>
  <summary>Click to expand</summary>

  This project is developed for the **Central Facilities Management Office (CFMO)** of Ateneo de Manila University. The system aims to streamline venue reservations, addressing the following current issues:

  * **Delays in booking** due to inefficiencies in the manual checking process.
  * **Overbooking** caused by a lack of transparency in venue availability.
  * **Manual looking at different venues** requiring significant time and effort.

  The goal is to create a **consolidated venue availability system** for students and the CFMO, providing real-time information on venue availability, capacities, and equipment. This enhances transparency, reduces overbooking, and facilitates a seamless user experience.

</details>

## Data Understanding

<details>
  <summary>Click to expand</summary>

  The system manages large datasets effectively using **arrays and dictionaries**. The data for venue availability appears to be drawn from and integrated with **Google Calendar** (GCal), with extraction potentially done through Apps Script/Add-on.

  The core data points include:
  * Venue codes (e.g., F-101, F-104, F-105)
  * Dates (e.g., 2025-02-00, 2025-02-02, 2025-02-13)
  * Time slots (e.g., 08:00-09:30, 14:00-16:30)
  * Capacity (e.g., 10, 30)

  **Edge Cases Handled for Data:**
  * **Data outside date range:** "Venue availability data is not available for this date range."
  * **No results after filtering:** "No match found."
  * **Results available after filtering:** "Filter complete. Available venues displayed below."
  * **No data in `load_reservations_data()`:** "No reservation data found."

  The project uses **dummy data generators** for testing and software development purposes. An **Entity-Relationship Diagram (ERD)** is also mentioned, indicating structured data management.
</details>


## Technologies

<details>
  <summary>Click to expand</summary>

  * **Framework:** Django (as indicated by the reference: `https://docs.djangoproject.com/en/5.1/ref/contrib/messages/`)
  * **Programming Language:** Python (implied by Django)
  * **Data Structures:** Arrays, Dictionaries
  * **Algorithms:** Binary Search, MergeSort (for efficient search and sorting operations)
  * **Data Integration:** Google Calendar (GCal), Apps Script/Add-on (for data extraction)
  * **Other Tools/Concepts:** CSV data import (reference to `https://plainenglish.io/blog/importing-csv-data-into-django-models`), Git.
  * **User Interface:** Aims for a simple, intuitive, and familiar interface, complying with typical design conventions.

</details>

## Setup

<details>
  <summary>Click to expand</summary>

  Based on the technologies used, a typical setup would involve:

  ### Prerequisites

  * Python 3.x
  * pip (Python package installer)
  * Git
  * A database system (e.g., PostgreSQL, SQLite, MySQL) if not using Django's default SQLite.
  * (Optional, if integrated) Google Cloud SDK / configured Google API access for GCal integration.

  ### Steps

  1.  **Clone the repository:**
      ```bash
      git clone [https://github.com/your_username/venue-availability-system.git](https://github.com/your_username/venue-availability-system.git)
      ```
  2.  **Navigate to the project directory:**
      ```bash
      cd venue-availability-system
      ```
  3.  **Create a virtual environment (recommended):**
      ```bash
      python -m venv venv
      source venv/bin/activate # On Windows: .\venv\Scripts\activate
      ```
  4.  **Install dependencies:**
      ```bash
      pip install -r requirements.txt
      ```
      (You will need a `requirements.txt` file containing Django and any other Python libraries used.)

  5.  **Apply database migrations:**
      ```bash
      python manage.py migrate
      ```
  6.  **Load initial data (if applicable, e.g., dummy data):**
      ```bash
      # This command might vary based on how you implemented data loading
      python manage.py loaddata initial_venues.json # Example
      # Or if using a CSV import script:
      python manage.py your_custom_command_to_import_csv
      ```
  7.  **Run the development server:**
      ```bash
      python manage.py runserver
      ```
      The application should now be accessible at `http://127.0.0.1:8000/` or similar.

  *(Note: Specific commands for configuring Google Calendar integration or running Apps Script would be additional steps if fully implemented.)*

</details>

## Approach

<details>
  <summary>Click to expand</summary>

  The project adopts a structured approach to address venue availability challenges:

  1.  **Problem Identification:** Identify inefficiencies in manual booking, overbooking, and scattered venue information within the Ateneo CFMO.
  2.  **Objective Setting:** Establish clear objectives, including creating a centralized monitoring system, integrating search and sort functions, and recommending suitable venues.
  3.  **System Design:**
      * **Consolidation:** Unify venue availability data into a single platform.
      * **Data Structures:** Utilize arrays and dictionaries for efficient management of large datasets, providing real-time information.
      * **Algorithms:** Implement Binary Search and MergeSort for efficient search and sorting operations of venue availability data.
      * **Integration:** Explore integration with existing systems like Google Calendar for data extraction.
      * **Dummy Data Generation:** Develop tools for generating test data to facilitate development and testing.
      * **ERD Design:** Design an Entity-Relationship Diagram for structured data management.
  4.  **Implementation (Django-based):** Develop the system using the Django framework, leveraging its capabilities for web application development.
  5.  **User Interface Design:** Focus on creating a simple, intuitive, and familiar user interface that complies with typical design conventions.
  6.  **Testing & Evaluation:**
      * Handle various **edge cases** (e.g., date ranges, no results, data not found) with appropriate warning/error messages.
      * Evaluate for **accuracy** (correct venues displayed) and **efficiency** (sorting within $O(N \log N)$ complexity).
  7.  **Future Enhancements:** Identify and plan for further improvements and features.

</details>

## Future Enhancements

<details>
  <summary>Click to expand</summary>

  The project has outlined several future enhancement opportunities:

  * **Integration with GSuite:** Further integrate availabilities stored in GCal, extracted through Apps Script/Add-on.
  * **Room Capacity Filtering:** Allow filtering by room capacity for more precise venue recommendations.
  * **Room Type Filtering:** Enable filtering by room type (e.g., classroom, lecture hall, lab).
  * **User Account System:** Implement user accounts with authentication and roles for personalized experiences and access control.
  * **Reservation Booking Functionality:** Directly allow users to book venues through the system, rather than just checking availability.
  * **Admin Panel:** Develop a comprehensive admin panel for CFMO staff to manage venues, reservations, and user permissions.
  * **Notifications:** Implement email or in-app notifications for reservation confirmations, changes, or cancellations.
  * **User Feedback System:** Allow users to provide feedback or report issues.
  * **Detailed Venue Information:** Provide more comprehensive details for each venue (e.g., available equipment, photos).

</details>

## Contact

* **Jana Almira J. Boco** - jana.boco@student.ateneo.edu
* **Nathan Luna** - luis.luna@student.ateneo.edu
* **Juliana Ysabelle S. Valdez** - juliana.valdez@student.ateneo.edu

Project Link: [Your GitHub Repository Link Here](https://github.com/javaldezz/works/tree/main/Venue%20Availability%20System%20%7C%20MSYS30)

## Acknowledgments

* **Course Instructor:** Josh Daniel L. Ong
* **Course Title:** Data Structures and Algorithms (MSYS 30C)
* **References/Inspiration:**
    * [Django Documentation](https://docs.djangoproject.com/en/5.1/ref/contrib/messages/)
    * [Importing CSV data into Django models](https://plainenglish.io/blog/importing-csv-data-into-django-models)
    * Ateneo de Manila University Central Facilities Management Office (CFMO)
