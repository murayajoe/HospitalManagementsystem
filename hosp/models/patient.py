from odoo import models, fields

class HospitalPatient(models.Model):
    _name = 'hospital.patient'
    _description = 'Hospital Patient'

    name = fields.Char(string='Patient Name', required=True)
    age = fields.Integer(string='Age')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    contact = fields.Char(string="Phone Number")
    next_of_kin_name = fields.Char(string="Next of Kin")
    next_of_kin_contact = fields.Char(string="Next of Kin Phone Number")
    identification_number = fields.Char(string="National ID")
    insurance = fields.Selection([('Yes', 'Yes'), ('No', 'No')], string='Are you insured?')
    insurance_number = fields.Integer(string="Insurance Number")
    weight = fields.Float(string="Weight")
    active = fields.Boolean(string="Active", default='True')
    category = fields.Selection([('Patient', 'patient'), ('Doctor', 'doctor')], string='Category')