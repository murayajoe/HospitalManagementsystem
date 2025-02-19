# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import re
from odoo.osv import expression
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from datetime import date, timedelta
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split


class ResCompany(models.Model):
    _inherit = 'res.company'

    last_move_number = fields.Integer('Last Move Number', default=1)
    last_line_number = fields.Integer('Last Line Number', default=0)


class ResUsers(models.Model):
    _inherit = 'res.users'

    account_id = fields.Many2one('account.account', 'Bank Account')


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    manual_partner_id = fields.Many2one('res.partner', string='Manual Partner')


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    ref_text = fields.Text(string='Voucher Reference')
    report_user_id = fields.Many2one('res.users', string='Responsible',
                                     required=False, compute="compute_user_date")
    report_date = fields.Date(required=False, string="Date ",
                              index=True, copy=False, compute="compute_user_date")

    def get_view_id(self, view_id=False):
        trial = self.env.ref(view_id).sudo().read()[0]
        return trial

    def compute_user_date(self):
        for record in self:
            today = datetime.today()
            user = self.env.user.id
            record.update({
                'report_date': today,
                'report_user_id': user
            })

    @api.constrains('line_ids', 'journal_id')
    def _validate_move_modification(self):
        if 'posted' in self.mapped('line_ids.payment_id.state'):
            pass

    def button_draft(self):
        exchange_move_ids = set()
        if self:
            self.env['account.full.reconcile'].flush_model(['exchange_move_id'])
            self.env['account.partial.reconcile'].flush_model(['exchange_move_id'])
            self._cr.execute(
                """
                    SELECT DISTINCT sub.exchange_move_id
                    FROM (
                        SELECT exchange_move_id
                        FROM account_full_reconcile
                        WHERE exchange_move_id IN %s

                        UNION ALL

                        SELECT exchange_move_id
                        FROM account_partial_reconcile
                        WHERE exchange_move_id IN %s
                    ) AS sub
                """,
                [tuple(self.ids), tuple(self.ids)],
            )
            exchange_move_ids = set([row[0] for row in self._cr.fetchall()])

        AccountMoveLine = self.env['account.move.line']
        excluded_move_ids = []

        if self._context.get('suspense_moves_mode'):
            excluded_move_ids = AccountMoveLine.search(
                AccountMoveLine._get_suspense_moves_domain() + [('move_id', 'in', self.ids)]).mapped('move_id').ids

        for move in self:
            if move.id in exchange_move_ids: 
                # if move in move.line_ids.mapped('full_reconcile_id.exchange_move_id'):
                raise UserError(_('You cannot reset to draft an exchange difference journal entry.'))
            if move.tax_cash_basis_rec_id:
                raise UserError(_('You cannot reset to draft a tax cash basis journal entry.'))
            if move.restrict_mode_hash_table and move.state == 'posted' and move.id not in excluded_move_ids:
                raise UserError(_('You cannot modify a posted entry of this journal because it is in strict mode.'))
            # We remove all the analytics entries for this journal
            move.mapped('line_ids.analytic_line_ids').unlink()

        if not self._context.get('no_remove'):
            self.mapped('line_ids').remove_move_reconcile()
        self.write({'state': 'draft'})


        
    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        # args = args or []

        state = ['posted']
        payment_state = ['not_paid', 'in_payment', 'partial']

        if self._context.get('partner_id') and self._context.get('type'):
            partner_id = int(self._context.get('partner_id'))

            currency_id = self._context.get('currency_id')

            if not currency_id:
                currency_id = self.env.company.currency_id.id

            if self._context.get('type') == 'payin':
                move_type = 'out_invoice'
            else:
                move_type = 'in_invoice'

            domain = (domain or []) + [('partner_id', '=', partner_id), ('move_type', '=', move_type),
                                       ('state', 'in', state), ('payment_state', 'in', payment_state)]

        res = super(AccountMoveInherit, self)._name_search(name, domain, operator, limit, order)
        return res


class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    @api.depends('matched_debit_ids', 'matched_credit_ids')
    def compute_partial_matching_number(self):
        for line in self:
            partial_matching_number = []
            if line.matched_credit_ids:
                for credit in line.matched_credit_ids:
                    partial_matching_number.append('PM' + str(credit.id))
            if line.matched_debit_ids:
                for debit in line.matched_debit_ids:
                    partial_matching_number.append('PM' + str(debit.id))
            line.partial_matching_number = ', '.join(partial_matching_number)

    partial_matching_number = fields.Char(string='Partial matching', compute='compute_partial_matching_number',
                                          store=True)
    in_payment = fields.Boolean('In Payment')
    last_line_number = fields.Integer('Last Line Number', default=0)
    last_amount = fields.Float('Last Amount', default=0.00)

    def _check_reconciliation(self):
        for line in self:
            if line.matched_debit_ids or line.matched_credit_ids:
                raise UserError(_("You cannot do this modification on a reconciled journal entry. "
                                  "You can just change some non legal fields or you must unreconcile first.\n"
                                  "Journal Entry (id): %s (%s)", line.move_id.name, line.move_id.id))

    @api.ondelete(at_uninstall=False)
    def _unlink_except_posted(self):
        # Prevent deleting lines on posted entries
        if not self._context.get('force_delete') and any(m.state == 'posted' for m in self.move_id):
            raise UserError(_('You cannot delete an item linked to a posted entry.'))

    # @api.model
    # def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     args = args or []
    #
    #     if self._context.get('payment_wizard_out'):
    #         currency_id = self._context.get('currency_id')
    #
    #         if not currency_id:
    #             currency_id = False
    #
    #         args += [('full_reconcile_id', '=', False),
    #                  ('balance', '!=', 0),
    #                  ('account_id.reconcile', '=', True),
    #                  ('reconciled', '=', False),
    #                  ('in_payment', '=', False),
    #                  ('move_id.move_type', '!=', 'entry'),
    #                  ('move_id.state', '=', 'posted'),
    #                  ]
    #
    #     if self._context.get('payment_wizard_in'):
    #         currency_id = self._context.get('currency_id')
    #
    #         if not currency_id:
    #             currency_id = False
    #
    #         args += [('full_reconcile_id', '=', False),
    #                  ('balance', '!=', 0),
    #                  ('account_id.reconcile', '=', True),
    #                  ('reconciled', '=', False),
    #                  ('in_payment', '=', False),
    #                  ('move_id.move_type', '!=', 'entry'),
    #                  ('move_id.state', '=', 'posted'),
    #                  ]
    #
    #     if self._context.get('partner_id') and self._context.get('partner_type'):
    #         partner_id = int(self._context.get('partner_id'))
    #
    #         args = [('move_id.state', '=', 'posted'),
    #                 ('partner_id', '=', partner_id),
    #                 ('reconciled', '=', False), '|',
    #                 ('amount_residual', '!=', 0.0),
    #                   ('amount_residual_currency', '!=', 0.0)
    #                 ]
    #
    #         if self._context.get('partner_type') == 'customer':
    #             account_ids = self.env['account.account'].search([
    #                 ('company_id', '=', self.env.user.company_id.id),
    #                 ('account_type', '=', 'asset_receivable')])
    #
    #             args.extend([('credit', '>', 0), ('debit', '=', 0), ('partner_id', '=', partner_id),
    #                          ('account_id', 'in', account_ids.ids or [])])
    #             return self._search(args, limit=limit, access_rights_uid=name_get_uid)
    #         else:
    #             account_ids = self.env['account.account'].search([
    #                 ('company_id', '=', self.env.user.company_id.id),
    #                 ('account_type', '=', 'liability_payable')])
    #
    #             args.extend([('credit', '=', 0), ('debit', '>', 0), ('partner_id', '=', partner_id),
    #                          ('account_id', 'in', account_ids.ids or [])])
    #             return self._search(args, limit=limit, access_rights_uid=name_get_uid)
    #     return super()._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        # domain = domain or []
        if self._context.get('payment_wizard_out'):
            currency_id = self._context.get('currency_id')

            if not currency_id:
                currency_id = False

            name_domain = [('full_reconcile_id', '=', False),
                     ('balance', '!=', 0),
                     ('account_id.reconcile', '=', True),
                     ('reconciled', '=', False),
                     ('in_payment', '=', False),
                     ('move_id.move_type', '!=', 'entry'),
                     ('move_id.state', '=', 'posted'),
                     ]
            domain = expression.AND([name_domain, domain])

        if self._context.get('payment_wizard_in'):
            currency_id = self._context.get('currency_id')

            if not currency_id:
                currency_id = False

            name_domain = [('full_reconcile_id', '=', False),
                     ('balance', '!=', 0),
                     ('account_id.reconcile', '=', True),
                     ('reconciled', '=', False),
                     ('in_payment', '=', False),
                     ('move_id.move_type', '!=', 'entry'),
                     ('move_id.state', '=', 'posted'),
                     ]
            domain = expression.AND([name_domain, domain])

        if self._context.get('partner_id') and self._context.get('partner_type'):
            partner_id = int(self._context.get('partner_id'))

            name_domain = [('move_id.state', '=', 'posted'),
                       ('partner_id', '=', partner_id),
                       ('reconciled', '=', False), '|',
                       ('amount_residual', '!=', 0.0),
                       ('amount_residual_currency', '!=', 0.0)
                       ]
            domain = expression.AND([name_domain, domain])
            if self._context.get('partner_type') == 'customer':
                account_ids = self.env['account.account'].search([
                    ('company_id', '=', self.env.user.company_id.id),
                    ('account_type', '=', 'asset_receivable')])
                name_domain=[('partner_id', '=', partner_id),('account_id', 'in', account_ids.ids or []),('credit', '>', 0), ('debit', '=', 0)]
                domain.extend(name_domain)
                return self._search(domain, limit=limit, order=order)

            else:
                account_ids = self.env['account.account'].search([
                    ('company_id', '=', self.env.user.company_id.id),
                    ('account_type', '=', 'liability_payable')])
                domain.extend([('credit', '=', 0), ('debit', '>', 0),('partner_id', '=', partner_id),('account_id', 'in', account_ids.ids or [])])
                # return self._search(domain, limit, order)
                return self._search(domain, limit=limit, order=order)
        return super()._name_search(name, domain, operator, limit, order)

   

class AccountPartialReconcileInherit(models.Model):
    _inherit = "account.partial.reconcile"

    def unlink(self):
        for reconcile in self:
            if self._context.get('from_js'):
                if reconcile.debit_move_id.move_id.is_inbound():
                    if reconcile.credit_move_id.in_payment:
                        if reconcile.credit_move_id.move_id:
                            current_move_id = reconcile.credit_move_id.move_id
                            move_id = reconcile.debit_move_id.move_id

                            move_curreny = move_id.currency_id
                            payment_currency = current_move_id.currency_id

                            payment_id = reconcile.credit_move_id.payment_id

                            credit = reconcile.credit_move_id.credit
                            last_line_number = reconcile.credit_move_id.last_line_number

                            partner_id = reconcile.credit_move_id.partner_id
                            currency_id = reconcile.credit_move_id.currency_id

                            move_name = reconcile.debit_move_id.name
                            current_balance = reconcile.debit_move_id.debit - reconcile.debit_move_id.credit

                            account_id = reconcile.debit_move_id.account_id.id

                            do_payment_move_vals = {}
                            remove_lines = []

                            remove_lines.append(reconcile.credit_move_id.id)

                            result = super(AccountPartialReconcileInherit, self).unlink()

                            if current_move_id.line_ids.filtered(
                                    lambda x: not x.in_payment and not x.reconciled and (x.partner_id == partner_id)):
                                for line in current_move_id.line_ids.filtered(
                                        lambda x: not x.in_payment and not x.reconciled and (
                                                x.partner_id == partner_id)):
                                    if line.credit > 0:
                                        credit += line.credit
                                        remove_lines.append(line.id)

                            current_move_id.with_context(check_move_validity=False, force_delete=True,
                                                         skip_account_move_synchronization=True).write({
                                'line_ids': [(2, line) for line in remove_lines]
                            })

                            last_line_number = self.env.user.company_id.last_line_number
                            last_line_number += 1

                            self.env.user.company_id.write({
                                'last_line_number': last_line_number
                            })

                            if payment_id:
                                if payment_id.currency_id != currency_id:
                                    credit = currency_id._convert(credit, payment_id.currency_id, payment_id.company_id,
                                                                  fields.Date.context_today(self))
                                elif (payment_id.currency_id == currency_id) and (
                                        move_id.company_currency_id != currency_id):
                                    credit = move_id.company_currency_id._convert(credit, currency_id,
                                                                                  payment_id.company_id,
                                                                                  fields.Date.context_today(self))
                                else:
                                    credit = credit

                                do_payment_move_vals = payment_id.with_context(
                                    amount_remain=credit,
                                    last_line_number=last_line_number,
                                    partner_id=partner_id)._prepare_move_line_default_vals()

                            else:
                                if (move_curreny == payment_currency) and (
                                        payment_currency != move_id.company_currency_id):
                                    credit = credit
                                    amount_currency = move_id.company_currency_id._convert(credit, move_curreny,
                                                                                           move_id.company_id,
                                                                                           fields.Date.context_today(
                                                                                               self))
                                    currency_id = payment_currency.id
                                elif (move_curreny != payment_currency):
                                    credit = credit
                                    amount_currency = move_curreny._convert(credit, payment_currency,
                                                                            move_id.company_id,
                                                                            fields.Date.context_today(self))
                                    currency_id = payment_currency.id
                                else:
                                    credit = credit
                                    amount_currency = 0.0
                                    currency_id = False

                                do_payment_move_vals = self.with_context(
                                    amount_remain=credit,
                                    amount_currency=amount_currency,
                                    current_balance=current_balance,
                                    currency_id=currency_id,
                                    account_id=account_id,
                                    move_name=move_name,
                                    last_line_number=last_line_number,
                                    partner_id=partner_id)._prepare_move_line_default_vals()

                            if len(do_payment_move_vals) >= 1:

                                for vals in do_payment_move_vals:
                                    vals.update({'move_id': current_move_id.id})
                                    current_move_id.line_ids.with_context(check_move_validity=False, force_delete=True,
                                                                          skip_account_move_synchronization=True).create(
                                        vals)

                            return result

                if reconcile.credit_move_id.move_id.is_outbound():
                    if reconcile.debit_move_id.in_payment:
                        if reconcile.debit_move_id.move_id:
                            current_move_id = reconcile.debit_move_id.move_id
                            move_id = reconcile.credit_move_id.move_id

                            move_curreny = move_id.currency_id
                            payment_currency = current_move_id.currency_id

                            payment_id = reconcile.debit_move_id.payment_id
                            partner_id = reconcile.debit_move_id.partner_id

                            debit = reconcile.debit_move_id.debit

                            last_line_number = reconcile.debit_move_id.last_line_number
                            currency_id = reconcile.debit_move_id.move_id.currency_id

                            current_balance = reconcile.credit_move_id.debit - reconcile.credit_move_id.credit

                            account_id = reconcile.credit_move_id.account_id.id
                            move_name = reconcile.credit_move_id.name

                            do_payment_move_vals = {}
                            remove_lines = []

                            remove_lines.append(reconcile.debit_move_id.id)

                            result = super(AccountPartialReconcileInherit, self).unlink()

                            if current_move_id.line_ids.filtered(
                                    lambda x: not x.in_payment and not x.reconciled and (x.partner_id == partner_id)):
                                for line in current_move_id.line_ids.filtered(
                                        lambda x: not x.in_payment and not x.reconciled and (
                                                x.partner_id == partner_id)):
                                    if line.debit > 0:
                                        debit += line.debit
                                        remove_lines.append(line.id)

                            current_move_id.with_context(check_move_validity=False, force_delete=True,
                                                         skip_account_move_synchronization=True).write({
                                'line_ids': [(2, line) for line in remove_lines]
                            })

                            last_line_number = self.env.user.company_id.last_line_number
                            last_line_number += 1
                            self.env.user.company_id.write({
                                'last_line_number': last_line_number
                            })

                            if payment_id:
                                if payment_id.currency_id != currency_id:
                                    debit = currency_id._convert(debit, payment_id.currency_id, payment_id.company_id,
                                                                 fields.Date.context_today(self))
                                elif (payment_id.currency_id == currency_id) and (
                                        move_id.company_currency_id != currency_id):
                                    debit = move_id.company_currency_id._convert(debit, currency_id,
                                                                                 payment_id.company_id,
                                                                                 fields.Date.context_today(self))
                                else:
                                    debit = debit

                                do_payment_move_vals = payment_id.with_context(
                                    amount_remain=debit,
                                    last_line_number=last_line_number,
                                    partner_id=partner_id)._prepare_move_line_default_vals()
                            else:

                                if (move_curreny == payment_currency) and (
                                        payment_currency != move_id.company_currency_id):
                                    debit = debit
                                    amount_currency = move_id.company_currency_id._convert(debit, move_curreny,
                                                                                           move_id.company_id,
                                                                                           fields.Date.context_today(
                                                                                               self))
                                    currency_id = payment_currency.id
                                elif (move_curreny != payment_currency):
                                    debit = debit
                                    amount_currency = move_curreny._convert(debit, payment_currency, move_id.company_id,
                                                                            fields.Date.context_today(self))
                                    currency_id = payment_currency.id
                                else:
                                    debit = debit
                                    amount_currency = 0.0
                                    currency_id = False

                                do_payment_move_vals = self.with_context(
                                    amount_remain=debit,
                                    amount_currency=amount_currency,
                                    current_balance=current_balance,
                                    currency_id=currency_id,
                                    account_id=account_id,
                                    move_name=move_name,
                                    last_line_number=last_line_number,
                                    partner_id=partner_id)._prepare_move_line_default_vals()

                            if len(do_payment_move_vals) >= 1:
                                for vals in do_payment_move_vals:
                                    vals.update({'move_id': current_move_id.id})
                                    current_move_id.line_ids.create(vals)

                            current_move_id.action_post()

                            return result
        return super(AccountPartialReconcileInherit, self).unlink()
