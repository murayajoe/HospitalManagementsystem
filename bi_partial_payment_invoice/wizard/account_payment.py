# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import math


class AccontPaymentWizard(models.Model):
    _name = 'account.payment.wizard'
    _description = 'Account Payment Wizard'

    @api.model
    def default_get(self, field_vals):
        result = super(AccontPaymentWizard, self).default_get(field_vals)
        if self.env.context.get('move_id'):
            move_id = self.env['account.move'].browse(self.env.context.get('move_id'))
            line_id = self.env.context.get('line_id')
            move_line_id = self.env['account.move.line'].browse(line_id)
            amount_total = move_line_id.amount_residual
            if not move_id.currency_id == move_id.company_id.currency_id:
                amount_total = move_id.company_id.currency_id._convert(amount_total, move_id.currency_id, move_id.company_id, move_line_id.date)
            result.update({
                'move_id' : move_id.id,
                'move_line_id' : move_line_id.id,
                'amount_total' : abs(amount_total) or 0.00,
            })
        return result

    @api.depends('amount_total', 'amount_to_pay', 'amount_residual')
    def remain_amount_(self):
        for payment in self:
            amount = payment.amount_total - payment.amount_to_pay
            due_amount = payment.amount_residual - payment.amount_to_pay
            payment.amount_remain = amount or 0.00
            payment.amount_due_remain = due_amount or 0.00

    name = fields.Char('Payment Name')
    move_id = fields.Many2one('account.move','Account Move')
    company_id = fields.Many2one('res.company', related='move_id.company_id', store=True, string='Company', readonly=False)
    company_currency_id = fields.Many2one('res.currency', string="Company Currency", related='company_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
    amount_to_pay = fields.Monetary(string='Amount to Pay', default=0.00)
    amount_remain = fields.Monetary(string='Remaining Amount for Payment', store=True, readonly=True, 
        compute='remain_amount_')
    amount_due_remain = fields.Monetary(string='Remaining Amount for Invoice', store=True, readonly=True,
        compute='remain_amount_')
    amount_total = fields.Monetary('Amount Total', default=0.00)
    move_line_id = fields.Many2one('account.move.line','Account Move Line')
    payment_id = fields.Many2one('account.payment', related='move_line_id.payment_id', store=True, string='Payment')
    amount_residual = fields.Monetary(string='Amount Due', store=True, readonly=True,
        related="move_id.amount_residual")
    currency_id = fields.Many2one('res.currency', string="Currency", related='move_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
    amount_currency = fields.Monetary('Amount In Currency')

    def partial_pay(self):
        for payment in self:

            link_move_ids = self.env['account.move']

            remaining_payment = 0.00
            move_line = False

            payment_line_id = payment.move_line_id
            payment_move_id = payment.move_line_id.move_id

            current_balance = payment_line_id.debit - payment_line_id.credit

            if payment.currency_id:
                amount_residual = abs(payment_line_id.amount_residual_currency)
            else:
                amount_residual = abs(payment_line_id.amount_residual)

            company_currency = payment.company_currency_id

            currency = payment.currency_id
            company = payment.company_id

            partner_id = payment.move_line_id.partner_id
            payment_id = payment.move_line_id.payment_id

            if payment_id:
                date = payment_id.date or fields.Date.context_today(self)
            else:
                date = fields.Date.context_today(self)

            account_id = payment_line_id.account_id and payment_line_id.account_id.id

            if currency:
                remaining_payment = payment.currency_id._convert(payment.amount_remain, payment.currency_id, payment.company_id, date)
            else:
                remaining_payment = payment.amount_remain

            remain_payment_move_vals = {}
            line_ids = []

            payment_line_ids = payment_move_id.line_ids.filtered(lambda x: x.partner_id == partner_id)

            if payment.move_id.is_inbound():
                payment_line_ids = payment_line_ids.filtered(lambda x : (x.credit > 0 and x.debit == 0) and not x.reconciled)
            else:
                payment_line_ids = payment_line_ids.filtered(lambda x : (x.credit == 0 and x.debit > 0) and not x.reconciled)
            for line in payment_line_ids:
                if line == payment_line_id:
                    line_ids.append(line.id)
            if line_ids:
                line_ids = list(set(line_ids))
                payment_move_id.with_context(check_move_validity=False,force_delete=True,skip_account_move_synchronization=True,dynamic_unlink=True).write({'line_ids' : [(2, line) for line in line_ids]})

            last_line_number = self.env.user.company_id.last_line_number

            for line in self:
                last_line_number += 1
                line_currency_id = line.currency_id

                if currency:
                    if currency == line_currency_id:
                        amount_to_pay = line_currency_id._convert(line.amount_to_pay, line.currency_id, company, date)
                    else:
                        amount_to_pay = line_currency_id._convert(line.amount_to_pay, currency, company, date)
                else:
                    amount_to_pay = line.amount_to_pay

                if not amount_to_pay:
                    raise UserError(_('No amount for Line %s') % (line.move_id.name))

                if  line.amount_due_remain < 0:
                    total_amount_due_remain = amount_to_pay + line.amount_due_remain
                    total_amount_due_remain = math.floor(total_amount_due_remain * 100) / 100

                    raise UserError(_('You can not add more than remaining amount for invoice %s') % (total_amount_due_remain))


                if  line.amount_remain < 0:
                    total_amount_remain = amount_to_pay + line.amount_remain
                    total_amount_remain = math.floor(total_amount_remain * 100) / 100
                    raise UserError(_('You can not add more than remaining amount for payment %s') % (total_amount_remain))

                if line.currency_id == company_currency:
                    amount_remain = line.amount_to_pay
                else:
                    amount_remain = line_currency_id._convert(amount_to_pay, currency, company, date)

                if payment_id:
                    do_payment_move_vals = payment_id.with_context(
                        amount_remain=amount_remain,
                        last_line_number=last_line_number,
                        currency_id = line.currency_id,
                        partner_id=partner_id)._prepare_move_line_default_vals()

                if not payment_id:
                    if currency and currency != company_currency:
                        amount_to_pay = currency._convert(amount_to_pay, company_currency, company, date)
                        amount_currency = amount_to_pay
                        currency_id = currency.id
                    else:
                        amount_to_pay = amount_to_pay
                        amount_currency = 0.0
                        currency_id = False
                    do_payment_move_vals = payment.with_context(
                        amount_to_pay=amount_to_pay,
                        amount_currency=amount_currency,
                        currency_id=currency_id,
                        last_line_number=last_line_number,
                        partner_id=partner_id,
                        current_balance=current_balance,
                        account_id=account_id)._prepare_move_line_default_vals()

                created_line_id = False
                if len(do_payment_move_vals) >= 1:
                    for vals in do_payment_move_vals:
                        vals.update({'move_id':payment_move_id.id})

                        created_line_id = payment_move_id.with_context(check_move_validity=False,force_delete=True,skip_account_move_synchronization=True).line_ids.create(vals)

                    if line.move_id.is_inbound():
                        lines = payment_move_id.with_context(check_move_validity=False,force_delete=True,skip_account_move_synchronization=True).line_ids.filtered(lambda x : (x.credit > 0 and x.debit == 0) and (x.partner_id == partner_id) and not x.reconciled and created_line_id == x)
                    else:
                        lines = payment_move_id.with_context(check_move_validity=False,force_delete=True,skip_account_move_synchronization=True).line_ids.filtered(lambda x : (x.credit == 0 and x.debit > 0) and (x.partner_id == partner_id) and not x.reconciled and created_line_id == x)

                    lines += line.move_id.line_ids.filtered(lambda line: line.account_id == lines[0].account_id and not line.reconciled)
                    lines.reconcile()
                    # _reconcile_plan
            

            if  remaining_payment:   
                last_line_number += 1
                self.env.user.company_id.write({
                    'last_line_number' : last_line_number
                })
                if payment_id:
                    remain_payment_move_vals = payment_id.with_context(
                        amount_remain=remaining_payment,
                        last_line_number=last_line_number,
                        currency_id = currency or company_currency,
                        partner_id=partner_id)._prepare_move_line_default_vals()

                if not payment_id:
                    if currency and currency != company_currency:
                        amount_remain = currency._convert(remaining_payment, company_currency, company, date)
                        amount_currency = remaining_payment
                        currency_id = currency.id
                    else:
                        amount_remain = remaining_payment
                        amount_currency = 0.0
                        currency_id = False

                    remain_payment_move_vals = payment.with_context(
                        amount_remain=amount_remain,
                        amount_currency=amount_currency,
                        currency_id=currency_id,
                        last_line_number=last_line_number,
                        partner_id=partner_id,
                        current_balance=current_balance,
                        account_id=account_id)._prepare_move_line_default_vals()

                if len(remain_payment_move_vals) >= 1:
                    for vals in remain_payment_move_vals:
                        vals.update({'move_id':payment_move_id.id})    
                    payment_move_id.with_context(check_move_validity=False,force_delete=True,skip_account_move_synchronization=True).line_ids.create(vals)
            else:
                self.env.user.company_id.write({
                    'last_line_number' : last_line_number
                })

        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def _prepare_move_line_default_vals(self):
        for payment in self:
            if self._context.get('amount_to_pay'):
                amount = self._context.get('amount_to_pay')
                in_payment = True
            else:
                amount = self._context.get('amount_remain')
                in_payment = False

            currency_id = self.env.company.currency_id.id
            rec_pay_line_name = payment.name or payment.move_line_id.display_name
            destination_account_id = False
            debit = credit = 0.00

            current_balance = payment.move_line_id.debit - payment.move_line_id.credit

            account_id = payment.move_line_id.account_id.id
            partner_id = self._context.get('partner_id').commercial_partner_id.id

            amount_currency = self._context.get('amount_currency')
            account_id = self._context.get('account_id')
            current_balance = self._context.get('current_balance')


            if current_balance < 0.0:
                credit = amount
                debit = 0.00
                amount_currency = -amount

            if current_balance > 0.0:
                credit = 0.00
                debit = amount
                amount_currency = amount

            all_move_vals = []


            line_vals_list = [

                # Receivable / Payable.
                {
                    'name': rec_pay_line_name,
                    'date_maturity': fields.Date.context_today(self),
                    'amount_currency': amount_currency,
                    'currency_id': currency_id,
                    'debit':debit,
                    'credit': credit,
                    'partner_id': partner_id or False,
                    'account_id': account_id,
                    'in_payment': in_payment,
                    'payment_id': False,
                    'last_line_number' : int(self._context.get('last_line_number', 0)),

                },
            ]
            return line_vals_list    
