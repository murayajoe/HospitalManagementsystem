from odoo import fields, models, api, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    wht_ids = fields.Many2many(
        'account.wht'
    )
    override_wht = fields.Boolean('Override WHT')

    amount = fields.Monetary(string='Payment Amount')
    wht_amount = fields.Monetary(string='WHT amount', compute='compute_wht_amount')
    after_wh_payment_amount = fields.Monetary(string='Net Payment', compute='compute_wht_amount')


    @api.onchange('override_wht')
    def _onchange_override_wht(self):
        if self.override_wht:
            self.wht_ids = False

    @api.onchange('wht_ids')
    def _onchange_wht_ids(self):
        domain = [('tax_application', '=', 'payment')]
        invoice = self.env['account.move'].search([('name','=',self.communication)])
        tax_lines = invoice.invoice_line_ids.filtered(lambda l: l.tax_ids)
        if tax_lines and invoice.move_type == 'in_invoice':
            domain.append(('type_tax_use', 'in', ('purchase','tax')))
        elif tax_lines and invoice.move_type == 'out_invoice':
            domain.append(('type_tax_use', 'in', ('sale','tax')))
        elif invoice.move_type == 'out_invoice':
            domain.append(('type_tax_use', '=', 'sale'))
        elif invoice.move_type == 'in_invoice':
            domain.append(('type_tax_use', '=', 'purchase'))

        return {'domain': {'wht_ids': domain}}

    # Writing values when creating wht payment
    def _create_payment_vals_from_wizard(self, batch_result):
        res = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)
        if self.wht_ids and self.wht_amount:
            res['override_wht'] = self.override_wht
            res['wht_amount'] = self.wht_amount
            res['wht_ids'] = self.wht_ids.ids
            res['after_wh_payment_amount'] = self.after_wh_payment_amount
        return res

    @api.depends('amount', 'wht_ids')
    def compute_wht_amount(self):
        for payment in self:
            final_amount = 0.00
            invoice = self.env['account.move'].search([('name','=',self.communication)])
            percentage = round(payment.amount / invoice.amount_total, 5) if invoice else 1
            if self.wht_ids:
                if self.payment_type == 'inbound':
                    if self.override_wht and self.wht_ids:
                        for wht in self.wht_ids:
                            if wht.type_tax_use != 'tax' and wht.amount:
                                wht_amount = round(self.amount * (wht.amount / 100), 2)
                                final_amount += wht_amount
                            if wht.type_tax_use == 'tax':
                                for line in invoice.invoice_line_ids.filtered(lambda l: l.tax_ids):
                                    if wht.sale_tax_id.id in line.tax_ids.ids:
                                        if wht.sale_tax_id.price_include:
                                            amount_after_tax = round(
                                                line.price_subtotal / (1 + wht.sale_tax_id.amount / 100),
                                                2)
                                            tax_amount = line.price_subtotal - amount_after_tax
                                        else:
                                            tax_amount = round(line.price_subtotal * (wht.sale_tax_id.amount / 100), 2)
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
                                        amount_after_tax = round(line.price_subtotal / (1 + wht.sale_tax_id.amount / 100),
                                                                 2)
                                        tax_amount = line.price_subtotal - amount_after_tax
                                    else:
                                        tax_amount = round(line.price_subtotal * (wht.sale_tax_id.amount / 100), 2)
                                    wht_amount = round(tax_amount * (wht.amount / 100), 2)
                                    wht_amount_ded = round(wht_amount * percentage, 2)
                                    final_amount += wht_amount_ded
                elif payment.payment_type == 'outbound':
                    if self.override_wht and self.wht_ids:
                        for wht in self.wht_ids:
                            if wht.type_tax_use != 'tax' and wht.amount:
                                wht_amount = round(self.amount * (wht.amount / 100), 2)
                                final_amount += wht_amount
                            if wht.type_tax_use == 'tax':
                                for line in invoice.invoice_line_ids.filtered(lambda l: l.tax_ids):
                                    if wht.sale_tax_id.id in line.tax_ids.ids:
                                        if wht.sale_tax_id.price_include:
                                            amount_after_tax = round(
                                                line.price_subtotal / (1 + wht.sale_tax_id.amount / 100),
                                                2)
                                            tax_amount = line.price_subtotal - amount_after_tax
                                        else:
                                            tax_amount = round(line.price_subtotal * (wht.sale_tax_id.amount / 100), 2)
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
                                        amount_after_tax = round(line.price_subtotal / (1 + wht.sale_tax_id.amount / 100),
                                                                 2)
                                        tax_amount = line.price_subtotal - amount_after_tax
                                    else:
                                        tax_amount = round(line.price_subtotal * (wht.sale_tax_id.amount / 100), 2)
                                    wht_amount = round(tax_amount * (wht.amount / 100), 2)
                                    wht_amount_ded = round(wht_amount * percentage, 2)
                                    final_amount += wht_amount_ded

                payment.wht_amount = final_amount
                payment.after_wh_payment_amount = payment.amount - payment.wht_amount

            if not final_amount:
                payment.wht_amount = 0.00
                payment.after_wh_payment_amount = payment.amount
