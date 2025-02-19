# -*- coding: utf-8 -*-
from odoo import fields, models, api
import logging
_logger = logging.getLogger(__name__)


class AccountMoveTax(models.Model):
    _name = "account.move.tax"
    _description = "Invoice Tax"
    _order = 'sequence'

    @api.depends('move_id.invoice_line_ids')
    def _compute_base_amount(self):
        tax_grouped = {}
        for invoice in self.mapped('move_id'):
            tax_grouped[invoice.id] = invoice.get_taxes_values()
        for tax in self:
            tax.base = 0.0
            if tax.tax_id:
                key = tax.tax_id.get_grouping_key({
                    'tax_id': tax.tax_id.id,
                    'account_id': tax.account_id.id,
                    'analytic_account_id': tax.analytic_account_id.id,
                })
                if tax.move_id and key in tax_grouped[tax.move_id.id]:
                    tax.base = tax_grouped[tax.move_id.id][key]['base']
                else:
                    _logger.warning('Tax Base Amount not computable probably due to a \
                            change in an underlying tax (%s).', tax.tax_id.name)

    name = fields.Char(string='Tax Description', required=True)
    tax_id = fields.Many2one('account.tax', string='Tax', ondelete='restrict')
    move_id = fields.Many2one(
        'account.move',
        string='Invoice',
        ondelete='cascade',
        index=True)

    account_id = fields.Many2one(
        'account.account',
        string='Tax Account',
        required=True,
        domain=[('deprecated', '=', False)])

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic account')
    amount = fields.Monetary()
    amount_rounding = fields.Monetary()
    amount_total = fields.Monetary(string="Total Amount", compute='_compute_amount_total')
    manual = fields.Boolean(default=True)
    sequence = fields.Integer(
        help="Gives the sequence order when displaying a list of invoice tax."
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        related='account_id.company_id',
        store=True, readonly=True)

    currency_id = fields.Many2one(
        'res.currency', related='move_id.currency_id',
        store=True, readonly=True)

    base = fields.Monetary(string='Base', compute='_compute_base_amount', store=True)

    @api.depends('amount', 'amount_rounding')
    def _compute_amount_total(self):
        for tax_line in self:
            tax_line.amount_total = tax_line.amount + tax_line.amount_rounding