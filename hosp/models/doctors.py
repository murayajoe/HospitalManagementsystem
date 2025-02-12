from odoo import fields, models, api 


class HospitalDoctor(models.Model):
    _name = 'hospital.doctor'
    _description = 'Hospital doctor'

    name = fields.Char(string='doctor Name', required=True)
    age = fields.Integer(string='Age')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    contact = fields.Char(string="Phone Number")
    next_of_kin_name = fields.Char(string="Next of Kin")
    next_of_kin_contact = fields.Char(string="Next of Kin Phone Number")
    identification_number = fields.Char(string="National ID")
    insurance = fields.Selection([('Yes', 'Yes'), ('No', 'No')], string='Are you insured?')
    insurance_number = fields.Integer(string="Insurance Number")
    weight = fields.Float(string="Weight")
    
