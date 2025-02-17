from odoo import models, fields

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    related_ticket_ids = fields.Many2many(
        'helpdesk.ticket', 'helpdesk_ticket_rel', 'ticket_id', 'related_ticket_id', 
        string='Related Tickets'
    )
