# Hospital Management System for Odoo

## Overview
The **Hospital Management System (HMS)** is an Odoo module designed to streamline hospital operations, improve patient care, and optimize administrative processes. This system efficiently manages patient records, doctor schedules, appointments, billing, and medical inventory.

## Features
- **Patient Management**: Register new patients, maintain medical history, and track treatments.
- **Doctor Management**: Manage doctor profiles, specializations, and availability schedules.
- **Appointment Booking**: Allow patients to book appointments with doctors based on availability.
- **Medical Records**: Store and access medical history, prescriptions, and test results.
- **Billing & Invoicing**: Automate billing processes with seamless integration into Odoo's accounting module.
- **Pharmacy & Inventory**: Track medical supplies, prescriptions, and stock levels.
- **Laboratory Management**: Manage lab test requests, results, and reports.
- **Insurance & Payments**: Handle insurance claims and multiple payment methods.
- **User Roles & Security**: Access control for different user roles (Admin, Doctor, Nurse, Receptionist, etc.).

## Installation
1. **Ensure Odoo is installed**
   - This module is compatible with Odoo 18.
2. **Download the module**
   - Clone the repository or copy the module folder into your Odoo addons directory.
   ```bash
   git clone <repository-url> /odoo/custom/addons/hospital_management
   ```
3. **Restart Odoo Server**
   ```bash
   systemctl restart odoo18
   ```
4. **Activate Developer Mode**
   - Navigate to **Settings > Developer Mode**.
5. **Install the Module**
   - Go to **Apps**, search for "Hospital Management System," and click **Install**.

## Configuration
1. **Set up User Roles**
   - Navigate to **Settings > Users & Companies > Users**.
   - Assign appropriate roles (e.g., Doctor, Nurse, Receptionist, Admin).
2. **Define Departments & Specialties**
   - Configure hospital departments such as Cardiology, Neurology, etc.
3. **Enable Accounting Integration**
   - Link the system to Odoo's accounting module for billing and invoicing.

## Usage
- **Register New Patients**: Go to **Patients > Create New Patient**.
- **Schedule Appointments**: Navigate to **Appointments > Schedule Appointment**.
- **Manage Billing**: View invoices under **Billing > Invoices**.
- **Track Inventory**: Check stock levels in **Inventory > Medical Supplies**.
- **View Reports**: Generate reports from **Reporting > Hospital Reports**.

## Support
For any issues, bugs, or feature requests, please contact:
- **Email**: support@clickpoa.com
- **GitHub Issues**: <[HospitalManagementsystem](https://github.com/murayajoe/HospitalManagementsystem)>/issues

## License
This module is licensed under the MIT License. See `LICENSE` for details.

## Contributors
- **Joe Muraya** - Lead Developer & Maintainer
---

