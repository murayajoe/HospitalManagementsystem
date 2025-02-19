from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class WHTBillWizard(models.TransientModel):
    _name = 'wht.bill.wizard'
    _description = 'WHT Bill Wizard'

    date_from = fields.Date()
    date_to = fields.Date()
    payment_state = fields.Selection([
        ('not_paid', 'Open'),
        ('paid', 'Paid'),
        ('both', 'Both'),
    ])
    partner_id = fields.Many2one('res.partner')
    check_all = fields.Boolean()

    wht_bill_line_ids = fields.One2many('wht.bill.wizard.lines', 'wht_bill_id')

    @api.onchange('check_all')
    def _onchange_check_all(self):
        if self.check_all and self.wht_bill_line_ids:
            for rec in self.wht_bill_line_ids:
                rec.check = True
        else:
            for rec in self.wht_bill_line_ids:
                rec.check = False


    def search_records(self):
        self.wht_bill_line_ids = [(5,)]
        wht_invoice = self.env['account.move.line'].search([]).filtered(lambda l: l.wht_tax_ids).mapped('move_id')
        if wht_invoice:
            for rec in wht_invoice.filtered(lambda l: l.state == 'posted' and l.invoice_date >= self.date_from and l.invoice_date <= self.date_to and l.wht_bill_created != True):
                if self.payment_state == 'both':
                    self.wht_bill_line_ids = [(0, 0, {
                        'check': True if self.check_all else False,
                        'move_id': rec.id,
                        'amount_untaxed': rec.amount_untaxed,
                        'amount_total': rec.amount_total,
                        'payment_state': rec.payment_state,
                        'tax_ids': rec.invoice_line_ids.mapped('tax_ids').ids,
                        'wht_ids': rec.invoice_line_ids.mapped('wht_tax_ids').ids,
                        'wht_bill_id': self.id
                    })]
                elif self.payment_state == rec.payment_state:
                    self.wht_bill_line_ids = [(0, 0, {
                        'check': True if self.check_all else False,
                        'move_id': rec.id,
                        'amount_untaxed': rec.amount_untaxed,
                        'amount_total': rec.amount_total,
                        'payment_state': rec.payment_state,
                        'tax_ids': rec.invoice_line_ids.mapped('tax_ids').ids,
                        'wht_ids': rec.invoice_line_ids.mapped('wht_tax_ids').ids,
                        'wht_bill_id': self.id
                    })]

        return {
            'context': self.env.context,
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def create_bills(self):
        if not self.wht_bill_line_ids:
            raise ValidationError('No record found!')

        checked_lines = self.wht_bill_line_ids.filtered(lambda l: l.check == True)
        if not checked_lines:
            raise ValidationError('Please mark lines to create bills.')
        prod = []
        for rec in checked_lines.move_id.taxes_line_ids:
            prod.append((0, 0, {
                    'name': rec.move_id.name,
                    'account_id': rec.wht_tax_id.account_id.id,
                    'price_unit': rec.amount,
                    'quantity': 1,
                    'wht_invoice_ref_id': rec.move_id.id,
                })),
            rec.move_id.wht_bill_created = True
        invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': prod
        })

        return {
            'effect': {
                'type': 'rainbow_man',
                'fadeout': 'slow',
                'message': _("Vendor Bills Generated Successfully!"),
            }
        }


class WHTBillWizardLines(models.TransientModel):
    _name = 'wht.bill.wizard.lines'
    _description = 'WHT Bill Wizard Lines'

    check = fields.Boolean()
    move_id = fields.Many2one('account.move')
    date = fields.Date(related='move_id.invoice_date')
    partner_id = fields.Many2one('res.partner', related='move_id.partner_id')
    amount_untaxed = fields.Float()
    amount_total = fields.Float()
    payment_state = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('partial', 'Partial'),
        ('paid', 'Paid')
    ])
    tax_ids = fields.Many2many('account.tax')
    wht_ids = fields.Many2many('account.wht')

    wht_bill_id = fields.Many2one('wht.bill.wizard')