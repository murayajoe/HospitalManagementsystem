# -*- coding: utf-8 -*-
from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)


class AccountWHT(models.Model):
    _name = "account.wht"
    _description = "Account WHT"

    @api.model
    def _default_wht_tax_group(self):
        return self.env['account.tax.group'].search([('is_wht', '=', True)], limit=1)

    name = fields.Char(string='Name', required=True, copy=False)
    tax_code = fields.Char(string='Tax Code', required=True, copy=False)
    type_tax_use = fields.Selection([
        ('tax', 'Witholding of Taxes'),
        ('sale', 'Sales'),
        ('purchase', 'Purchases'),
        ],
        string='Tax Scope', required=True, default="sale")

    tax_application = fields.Selection([('payment', 'At Payment'), (
        'invoice', 'At Invoice')], string='Tax Application', default="payment")
    sale_tax_id = fields.Many2one('account.tax', string='Sales Tax')
    amount_type = fields.Selection(
        default='percent', string="Tax Computation", required=True,
        selection=[
            ('group', 'Group of Taxes'), ('fixed', 'Fixed'),
            ('percent', 'Percentage of Price'),
            ('division', 'Percentage of Price Tax Included')])

    active = fields.Boolean(
        default=True,
        help="Set active to false to hide the tax without removing it."
    )
    amount = fields.Float(required=True, digits=(16, 4))
    account_id = fields.Many2one(
        'account.account',
        domain=[('deprecated', '=', False)],
        string='WHT Account',
        ondelete='restrict', )
    refund_account_id = fields.Many2one(
        'account.account',
        domain=[('deprecated', '=', False)],
        string='WHT Account on Credit Notes',
        ondelete='restrict')

    description = fields.Text()
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company)
    tax_group_id = fields.Many2one(
        'account.tax.group', string="Tax Group",
        default=_default_wht_tax_group, required=True)

    @api.onchange('account_id')
    def onchange_account_id(self):
        self.refund_account_id = self.account_id

    def copy(self, default=None):
        default = dict(default or {})
        default.update({'name': self.name + ' (Copy)' if self.name else "New WHT", 'tax_code': self.tax_code + ' (Copy)' if self.tax_code else "Code"})

        return super(AccountWHT, self).copy(default)
