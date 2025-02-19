# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import logging
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _wht_domain(self):
        domain = [['tax_application', '=', 'payment']]
        if self._context.get('default_payment_type', False) and self._context.get('default_payment_type') == 'inbound':
            domain.append(['type_tax_use', 'in', ('sale','tax')])
        elif self._context.get('default_payment_type', False) and self._context.get(
                'default_payment_type') == 'outbound':
            domain.append(['type_tax_use', 'in', ('purchase','tax')])

        return domain

    wht_ids = fields.Many2many(
        'account.wht',
        domain=_wht_domain
    )
    override_wht = fields.Boolean('Override WHT')

    payment_amount = fields.Monetary(related='move_id.amount_total', string='Total ')
    wht_amount = fields.Monetary(string='WHT amount', compute='compute_wht_amount')
    after_wh_payment_amount = fields.Monetary(string='Net Payment', compute='compute_wht_amount')

    @api.onchange('override_wht')
    def _onchange_override_wht(self):
        if self.override_wht:
            self.wht_ids = False

    @api.onchange('wht_ids')
    def _onchange_wht_ids(self):
        domain = [('tax_application', '=', 'payment')]
        if self.partner_type == 'customer':
            domain.append(('type_tax_use', 'in', ('sale','tax')))
        elif self.partner_type == 'supplier':
            domain.append(('type_tax_use', 'in', ('purchase','tax')))

        return {'domain': {'wht_ids': domain}}

    @api.depends('amount', 'wht_ids')
    def compute_wht_amount(self):
        for payment in self:
            final_amount = 0.00
            invoice = False
            if payment.reconciled_bill_ids:
                invoice = payment.reconciled_bill_ids
            if payment.reconciled_invoice_ids:
                invoice = payment.reconciled_invoice_ids

            if invoice:
                percentage = round(payment.amount_total / invoice.amount_total, 5)
                if any(rec.override_wht for rec in self) and self.wht_ids:
                    for wht in self.wht_ids:
                        if wht.type_tax_use != 'tax' and wht.amount:
                            wht_amount = round(payment.amount_total * (wht.amount / 100), 2)
                            final_amount += wht_amount
                        if wht.type_tax_use == 'tax':
                            tax_amount = round(invoice.amount_untaxed * (wht.sale_tax_id.amount / 100), 2)
                            wht_amount = round(tax_amount * (wht.amount / 100), 2)
                            final_amount += wht_amount
                else:
                    for line in invoice.invoice_line_ids.filtered(lambda l: l.wht_tax_ids):
                        for wht in line.wht_tax_ids.filtered(lambda w: w.tax_application == 'payment'):
                            if wht.type_tax_use != 'tax' and wht.amount:
                                wht_amount = round(line.price_total * (wht.amount / 100), 2)
                                wht_amount_ded = round(wht_amount * percentage, 2)
                                final_amount += wht_amount_ded
                            if wht.type_tax_use == 'tax' and wht.sale_tax_id.id in line.tax_ids.ids:
                                if wht.sale_tax_id.price_include:
                                    amount_after_tax = round(line.price_subtotal / (1 + wht.sale_tax_id.amount / 100), 2)
                                    tax_amount = line.price_subtotal - amount_after_tax
                                else:
                                    tax_amount = round(line.price_subtotal * (wht.sale_tax_id.amount / 100), 2)
                                wht_amount = round(tax_amount * (wht.amount / 100), 2)
                                wht_amount_ded = round(wht_amount * percentage, 2)
                                final_amount += wht_amount_ded

            else:
                if payment.move_id:
                    for wht in self.wht_ids:
                        if wht.type_tax_use != 'tax' and wht.amount:
                            wht_amount = round(payment.payment_amount * (wht.amount / 100), 2)
                            final_amount += wht_amount


            payment.wht_amount = final_amount
            payment.after_wh_payment_amount = payment.payment_amount - payment.wht_amount

            if not final_amount:
                payment.wht_amount = 0.00
                payment.after_wh_payment_amount = payment.amount

    def generate_lines(self, payment, wht_amount_ded, res, wht, inv=False):
        company_currency = payment.company_id.currency_id
        if payment.currency_id == company_currency:
            wht_amount = wht_amount_ded
        else:
            wht_amount = payment.currency_id._convert(
                wht_amount_ded,
                company_currency,
                payment.company_id,
                payment.date)
        debit = 0.0
        credit = 0.0
        if wht_amount and payment.payment_type == 'outbound':
            for line in res:
                if line['credit'] != 0.0 and 'Write-Off' not in line['name'] and line['name'] not in self.env['account.wht'].search([]).mapped('name'):
                    line['credit'] = round(line['credit'] - wht_amount, 2)

            debit = 0.0
            credit = wht_amount
        elif wht_amount and payment.payment_type == 'inbound':
            for line in res:
                if line['debit'] != 0.0 and 'Write-Off' not in line['name'] and line['account_id'] not in [wht.account_id.id]:
                    line['debit'] = round(line['debit'] - wht_amount, 2)

            debit = wht_amount
            credit = 0.0

        res.append({
            'name': wht.name,
            'currency_id': payment.currency_id.id,
            'debit': debit,
            'credit': credit,
            'date_maturity': payment.date,
            'partner_id': payment.partner_id.commercial_partner_id.id,
            'account_id': wht.account_id.id
        })

        if inv and inv.move_type in ["out_invoice", "in_refund", "in_invoice", "out_refund"]:
            inv.wht_line_ids.create({
                'name': 'Withholding Tax',
                'account_id': wht.account_id.id,
                'amount': wht_amount,
                'move_id': inv.id

            })

    # overriding this function to by pass validation in case of wht payment
    def     _synchronize_balance_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):

            # After the migration to 14.0, the journal entry could be shared between the account.payment and the
            # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
            if pay.move_id.statement_line_id:
                continue

            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}

            if 'journal_id' in changed_fields:
                if pay.journal_id.type not in ('bank', 'cash'):
                    raise UserError(_("A payment must always belongs to a bank or cash journal."))

            if 'line_ids' in changed_fields:
                all_lines = move.line_ids
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

                if len(liquidity_lines) != 1:
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "include one and only one outstanding payments/receipts account.",
                        move.display_name,
                    ))

                # Commented this validation to allow wht journal entry
                # if len(counterpart_lines) != 1:
                #     raise UserError(_(
                #         "Journal Entry %s is not valid. In order to proceed, the journal items must "
                #         "include one and only one receivable/payable account (with an exception of "
                #         "internal transfers).",
                #         move.display_name,
                #     ))

                # Commented this validation to allow wht journal entry

                # if writeoff_lines and len(writeoff_lines.account_id) != 1:
                #     raise UserError(_(
                #         "Journal Entry %s is not valid. In order to proceed, "
                #         "all optional journal items must share the same account.",
                #         move.display_name,
                #     ))

                if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "share the same currency.",
                        move.display_name,
                    ))

                if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "share the same partner.",
                        move.display_name,
                    ))
                #To avoid singleton error in case of partial payments
                if len(self) > 1:
                    if self[0].payment_type == 'inbound':
                        partner_type = 'customer'
                    if self[0].payment_type == 'outbound':
                        partner_type = 'supplier'
                else:
                    if self.payment_type == 'inbound':
                        partner_type = 'customer'
                    if self.payment_type == 'outbound':
                        partner_type = 'supplier'

                # changing existing logic to get partner type based on account type
                # if counterpart_lines.account_id.user_type_id.type == 'receivable':
                #     partner_type = 'customer'
                # else:
                #     partner_type = 'supplier'

                balance_sum = round(sum(line.balance for line in all_lines),10)
                if balance_sum != 0:
                    liquidity_amount = liquidity_lines.amount_currency
                    for line in writeoff_lines:
                        if line.credit:
                            liquidity_lines.credit = (-liquidity_amount - line.credit)
                    for line in writeoff_lines:
                        if line.debit:
                            liquidity_lines.debit = (liquidity_amount - line.debit)

                    move_vals_to_write.update({
                        'currency_id': liquidity_lines.currency_id.id,
                        'partner_id': liquidity_lines.partner_id.id,
                    })
                    payment_vals_to_write.update({
                        'amount': abs(liquidity_amount),
                        'partner_type': partner_type,
                        'currency_id': liquidity_lines.currency_id.id,
                        'destination_account_id': counterpart_lines[0].account_id.id if counterpart_lines else False,
                        'partner_id': liquidity_lines.partner_id.id,
                    })
                    if liquidity_amount > 0.0:
                        payment_vals_to_write.update({'payment_type': 'inbound'})
                    elif liquidity_amount < 0.0:
                        payment_vals_to_write.update({'payment_type': 'outbound'})

            move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
            pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        res = super(AccountPayment, self)._prepare_move_line_default_vals()
        for payment in self:
            invoice = self.env['account.move'].search([('name','=',payment.ref)])
            if self.wht_ids and not invoice:
                for wht in self.wht_ids:
                    if wht.type_tax_use != 'tax' and wht.amount:
                        wht_amount = round(payment.amount * (wht.amount / 100), 2)
                        if payment.payment_type == 'outbound' and wht_amount < 0:
                            wht_amount = wht_amount * -1
                        self.generate_lines(payment, wht_amount, res, wht, invoice)
                    if wht.type_tax_use == 'tax':
                        tax_amount = round(invoice.amount_untaxed * (wht.sale_tax_id.amount / 100), 2)
                        wht_amount = round(tax_amount * (wht.amount / 100), 2)
                        if payment.payment_type == 'outbound' and wht_amount < 0:
                            wht_amount = wht_amount * -1
                        self.generate_lines(payment, wht_amount, res, wht, invoice)
            else:
                if payment.payment_type == 'inbound':
                    if self.override_wht and self.wht_ids:
                        for wht in self.wht_ids:
                            if wht.type_tax_use != 'tax' and wht.amount:
                                wht_amount = round(payment.amount * (wht.amount / 100), 2)
                                if payment.payment_type == 'outbound' and wht_amount < 0:
                                    wht_amount = wht_amount * -1
                                self.generate_lines(payment, wht_amount, res, wht, invoice)
                            if wht.type_tax_use == 'tax':
                                tax_amount = round(invoice.amount_untaxed * (wht.sale_tax_id.amount / 100), 2)
                                wht_amount = round(tax_amount * (wht.amount / 100), 2)
                                if payment.payment_type == 'outbound' and wht_amount < 0:
                                    wht_amount = wht_amount * -1
                                self.generate_lines(payment, wht_amount, res, wht, invoice)
                    else:
                        for line in invoice.invoice_line_ids.filtered(lambda l: l.wht_tax_ids):
                            for wht in line.wht_tax_ids.filtered(lambda w: w.tax_application == 'payment'):
                                percentage = round(payment.amount / invoice.amount_total, 5)
                                if wht.type_tax_use != 'tax' and wht.amount:
                                    wht_amount = round(line.price_total * (wht.amount / 100), 2)
                                    wht_amount_ded = round(wht_amount * percentage, 2)
                                    self.generate_lines(payment, wht_amount_ded, res, wht, invoice)
                                if wht.type_tax_use == 'tax' and wht.sale_tax_id.id in line.tax_ids.ids:
                                    if wht.sale_tax_id.price_include:
                                        amount_after_tax = round(line.price_subtotal / (1 + wht.sale_tax_id.amount / 100), 2)
                                        tax_amount = line.price_subtotal - amount_after_tax
                                    else:
                                        tax_amount = round(line.price_subtotal * (wht.sale_tax_id.amount / 100), 2)
                                    wht_amount = round(tax_amount * (wht.amount / 100), 2)
                                    wht_amount_ded = round(wht_amount * percentage, 2)
                                    self.generate_lines(payment, wht_amount_ded, res, wht, invoice)
                elif payment.payment_type == 'outbound':
                    if self.override_wht and self.wht_ids:
                        for wht in self.wht_ids:
                            if wht.type_tax_use != 'tax' and wht.amount:
                                wht_amount = round(payment.amount * (wht.amount / 100), 2)
                                if payment.payment_type == 'outbound' and wht_amount < 0:
                                    wht_amount = wht_amount * -1
                                self.generate_lines(payment, wht_amount, res, wht, invoice)
                            if wht.type_tax_use == 'tax':
                                tax_amount = round(invoice.amount_untaxed * (wht.sale_tax_id.amount / 100), 2)
                                wht_amount = round(tax_amount * (wht.amount / 100), 2)
                                if payment.payment_type == 'outbound' and wht_amount < 0:
                                    wht_amount = wht_amount * -1
                                self.generate_lines(payment, wht_amount, res, wht, invoice)
                    else:
                        for line in invoice.invoice_line_ids.filtered(lambda l: l.wht_tax_ids):
                            for wht in line.wht_tax_ids.filtered(lambda w: w.tax_application == 'payment'):
                                percentage = round(payment.amount / invoice.amount_total, 5)
                                if wht.type_tax_use != 'tax' and wht.amount:
                                    wht_amount = round(line.price_total * (wht.amount / 100), 2)
                                    wht_amount_ded = round(wht_amount * percentage, 2)
                                    self.generate_lines(payment, wht_amount_ded, res, wht, invoice)
                                if wht.type_tax_use == 'tax' and wht.sale_tax_id.id in line.tax_ids.ids:
                                    if wht.sale_tax_id.price_include:
                                        amount_after_tax = round(line.price_subtotal / (1 + wht.sale_tax_id.amount / 100), 2)
                                        tax_amount = line.price_subtotal - amount_after_tax
                                    else:
                                        tax_amount = round(line.price_subtotal * (wht.sale_tax_id.amount / 100), 2)
                                    wht_amount = round(tax_amount * (wht.amount / 100), 2)
                                    wht_amount_ded = round(wht_amount * percentage, 2)
                                    self.generate_lines(payment, wht_amount_ded, res, wht, invoice)
        return res

