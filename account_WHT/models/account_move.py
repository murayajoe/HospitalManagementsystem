# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    tax_line_ids = fields.One2many(
        'account.move.tax', 'move_id',
        string='Tax Lines',
        readonly=True,
        copy=True
    )
    state = fields.Selection([
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ], string='State', default='draft')

    wht_line_ids = fields.One2many(
        'account.move.wht',
        'move_id',
        string='WHT Lines',
        readonly=True
    )
    wht_bill_created = fields.Boolean()


    taxes_line_ids = fields.One2many('account.move.tax.lines', 'move_id')

    def create_wht_line(self, line):
        amount = 0
        if self.move_type in ["out_invoice", "in_refund"]:
            amount = line.debit
        elif self.move_type in ["in_invoice", "out_refund"]:
            amount = line.credit

        if amount:
            self.wht_line_ids.create({
                'name': 'Withholding Tax',
                'account_id': line.account_id.id,
                'amount': amount,
                'move_id': self.id

            })

    def _synchronize_business_models(self, changed_fields):
        ''' Ensure the consistency between:
        account.payment & account.move
        account.bank.statement.line & account.move

        The idea is to call the method performing the synchronization of the business
        models regarding their related journal entries. To avoid cycling, the
        'skip_account_move_synchronization' key is used through the context.

        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return
        self_sudo = self.sudo()
        self_sudo.payment_id._synchronize_balance_from_moves(changed_fields)
        self_sudo.statement_line_id._synchronize_from_moves(changed_fields)
    def action_post(self):
        wht_lines = self.line_ids.filtered(lambda line: line.is_wht_line)
        for wht_line in wht_lines:
            if wht_line.wht_tax_ids.tax_application == 'invoice':
                self.create_wht_line(wht_line)

        return super(AccountMove, self).action_post()

    def append_entry(self, wht, tax_amount, line, line_ids, tax_line=None):
        wht_amount = 0
        if wht.type_tax_use != 'tax':
            product_amount_including_tax = tax_amount + line.price_subtotal
            wht_amount = round(product_amount_including_tax * (wht.amount / 100), 2)
        elif tax_amount and tax_line.ids[0] in wht.sale_tax_id.ids and wht.type_tax_use == 'tax':
            tax_on_taxes = round(
                tax_amount * (wht.amount / 100), 2)
            wht_amount = tax_on_taxes

        if wht_amount:
            debit = wht_amount if self.move_type in ["out_invoice", "in_refund"] else 0.0
            credit = wht_amount if self.move_type in ["in_invoice", "out_refund"] else 0.0

            line_ids.append((0, 0, {
                'name': wht.name,
                'account_id': wht.account_id.id,
                'debit': debit,
                'credit': credit,
                'partner_id': self.partner_id.id,
                'display_type': True,
                'wht_tax_ids': [(6, 0, [wht.id])],
                'is_wht_line': True
            }))
        return line_ids

    def generate_wht_move_lines(self, wht, line, line_ids):
        if wht.tax_application == 'invoice':
            tax_amount = 0
            if line.tax_ids:
                for tax_line in line.tax_ids:
                    tax_amount = line.price_subtotal * round(tax_line.amount / 100, 2)
                    return self.append_entry(wht, tax_amount, line, line_ids, tax_line=tax_line)
            else:
                return self.append_entry(wht, tax_amount, line, line_ids, tax_line=None)
        return line_ids

    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids(self):
        invoice_line_ids = self.invoice_line_ids

        line_ids = []
        for line in invoice_line_ids:
            if line.wht_tax_ids:
                for wht in line.wht_tax_ids:
                    line_ids = self.generate_wht_move_lines(wht, line, line_ids)

        wht_move_lines = [(2, wht.id) for wht in self.line_ids.filtered(lambda l: l.is_wht_line)]
        if wht_move_lines:
            self.line_ids = wht_move_lines

        if line_ids:
            self.line_ids = line_ids
            self.invoice_line_ids = invoice_line_ids

        return super(AccountMove, self)._onchange_quick_edit_line_ids()

    def action_register_payment(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        '''
        wht_lines = self.invoice_line_ids.filtered(
            lambda l: l.display_type != True).wht_tax_ids.filtered(
            lambda s: s.tax_application == 'payment')
        if wht_lines:
            wht_ids = wht_lines.ids
        else:
            wht_ids = []

        if wht_ids:
            return {
                'name': _('Register Payment'),
                'res_model': 'account.payment.register',
                'view_mode': 'form',
                'context': {
                    'active_model': 'account.move',
                    'active_ids': self.ids,
                    'default_wht_ids': wht_ids,
                },
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
        else:
            return super(AccountMove, self).action_register_payment()

    @api.onchange('invoice_line_ids')
    def on_change_tax_ids(self):
        self.taxes_line_ids = [(5,)]
        for line in self.invoice_line_ids:
            if line.wht_tax_ids:
                data = []
                for rec in line.wht_tax_ids:
                    if rec.type_tax_use != 'tax':
                        vals = {'name': rec.name,
                                'amount': round(line.price_total * (rec.amount/100),2),
                                'account_id': rec.account_id.id,
                                'wht_tax_id': rec.ids[0],
                                'move_id': self.id,
                                }
                        data.append(vals)
                        self.taxes_line_ids = [(0, 0, vals)]
                    if rec.type_tax_use == 'tax' and rec.sale_tax_id.id in line.tax_ids.ids:
                        if rec.sale_tax_id.price_include:
                            amount_after_tax = round(line.price_subtotal / (1 + rec.sale_tax_id.amount / 100), 2)
                            tax_amount = line.price_subtotal - amount_after_tax
                        else:
                            tax_amount = round(line.price_subtotal * (rec.sale_tax_id.amount/100),2)
                        vals = {'name': rec.name,
                                'amount': round(tax_amount * (rec.amount/100),2),
                                'account_id': rec.account_id.id,
                                'wht_tax_id': rec.ids[0],
                                'move_id': self.id,
                                }
                        data.append(vals)
                        self.taxes_line_ids = [(0, 0, vals)]


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    wht_tax_ids = fields.Many2many(
        'account.wht',
        string='WHT'
    )
    is_wht_line = fields.Boolean()
    wht_invoice_ref_id = fields.Many2one('account.move')