from odoo import models, fields

class HospitalPatient(models.Model):
    _name = 'hospital.patient'
    _description = 'Hospital Patient'

    name = fields.Char(string='Patient Name', required=True)
    age = fields.Integer(string='Age')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    contact = fields.integer(string="Phone Number")
    next_of_kin_name = fields.char(string="next of kin")
    next_of_kin_contact = fields.integer(string="next of kin phone number")
    identification_number = fields.integer(string="ID")
    insurance = fields.selection([('Yes', 'yes'), ('No', 'no')],string='Do you have insurace?')
    insurance_number = fields.integer(string="insurance number")
    Weight = fields.float(string=" weight (Kgs)")

