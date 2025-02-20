from odoo import models, fields

class HospitalPatient(models.Model):
    _name = 'hospital.patient'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hospital Patient'
   
    name = fields.Char(string='Patient Name', required=True Tracking=True)
    age = fields.Integer(string='Age' Tracking=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender'Tracking=True)
    contact = fields.Char(string="Phone Number" Tracking=True)
    next_of_kin_name = fields.Char(string="Next of Kin")
    next_of_kin_contact = fields.Char(string="Next of Kin Phone Number")
    identification_number = fields.Char(string="National ID" Tracking=True)
    insurance = fields.Selection([('Yes', 'Yes'), ('No', 'No')], string='Are you insured?'Tracking=True)
    insurance_number = fields.Integer(string="Insurance Number" Tracking=True)
    weight = fields.Float(string="Weight" Tracking=True)
    active = fields.Boolean(string="Active", default='True')
    category = fields.Selection([('Patient', 'patient'), ('Doctor', 'doctor')], string='Category'Tracking=True)



     # New Fields
    blood_group = fields.Selection([
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B-'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-')
    ], string="Blood Group")

    medical_history = fields.Text(string="Medical History")
    allergies = fields.Text(string="Allergies")
    chronic_diseases = fields.Text(string="Chronic Diseases")

    last_visit_date = fields.Date(string="Last Visit Date")
    next_appointment_date = fields.Date(string="Next Appointment Date")
    doctor_assigned = fields.Many2one('hospital.doctor', string="Assigned Doctor")

    emergency_contact_name = fields.Char(string="Emergency Contact Name")
    emergency_contact_number = fields.Char(string="Emergency Contact Number")
    emergency_relationship = fields.Selection([
        ('parent', 'Parent'), ('spouse', 'Spouse'), ('child', 'Child'),
        ('sibling', 'Sibling'), ('friend', 'Friend'), ('other', 'Other')
    ], string="Relationship with Patient")

    marital_status = fields.Selection([
        ('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'),
        ('widowed', 'Widowed')
    ], string="Marital Status")

    address = fields.Text(string="Address")
    occupation = fields.Char(string="Occupation")
    payment_method = fields.Selection([
        ('cash', 'Cash'), ('insurance', 'Insurance'), ('card', 'Card')
    ], string="Preferred Payment Method")