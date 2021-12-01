# -*- coding: utf-8 -*-
import pdb

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        surcharge_line = res.order_line.filtered(lambda line: line.name == 'Online Payment Surcharge')
        if surcharge_line:
            surcharge_line[0].unlink()
        return res

    def custom_function_surcharge_saleorder(self,acquirer):
        # for rec in self:

        if acquirer.is_surcharge:
            print(acquirer.is_surcharge,'acquirer.is_surcharge')
            charge_amount = (acquirer.set_surcharge / 100) * sum(self.mapped('amount_total'))
            updated_amount = sum(self.mapped('amount_total')) + charge_amount
            # self.button_draft()
            surcharge_line = []
            product_surcharge = self.env['product.product'].search([('name', '=', 'Online Payment Surcharge')], limit=1)
            values = {
                'product_id': product_surcharge.id,
                'product_uom_qty': 1.0,
                'price_unit': charge_amount,
                'product_uom': product_surcharge.uom_id.id,
                'order_id': self.id,
                'qty_delivered': 1,
                'name': product_surcharge.name,
            }
            surcharge_line.append([0, 0, values])
            order_line = self.env['sale.order.line'].sudo().create(values)
            self.order_line = surcharge_line
        self._amount_all()
        # pdb.set_trace()
        # return

class AccountMove(models.Model):
    _inherit = "account.move"

    amount_after_charge = fields.Float(string='Amount After Charge')
    set_surcharge = fields.Float(string='Surcharge')

    # @api.model
    # def create(self, vals):
    #     res = super(AccountMove, self).create(vals)
    #     surcharge_line = res.invoice_line_ids.filtered(lambda line: line.product_id.name == 'Online Payment Surcharge')
    #     if surcharge_line:
    #         raise ValidationError(_('Have to delete surcharge line before duplicate record.'))
    #         # surcharge_line[0].unlink()
    #     return res

    def copy(self, default=None):
        res = super(AccountMove, self).copy(default=default)
        surcharge_line = res.invoice_line_ids.filtered(lambda line: line.product_id.name == 'Online Payment Surcharge')
        res['invoice_line_ids'] = res.invoice_line_ids - surcharge_line
        return res


    def custom_function_surcharge(self,acquirer):
        for rec in self:
            if acquirer.is_surcharge:
                print(acquirer.is_surcharge,'acquirer.is_surcharge')
                charge_amount = (acquirer.set_surcharge / 100) * sum(rec.mapped('amount_residual'))
                updated_amount = sum(self.mapped('amount_residual')) + charge_amount
                rec.button_draft()
                surcharge_line = []
                product_surcharge = self.env['product.product'].search([('name', '=', 'Online Payment Surcharge')], limit=1)
                values = {
                    'product_id': product_surcharge.id,
                    'quantity': 1,
                    'price_unit': charge_amount,
                }
                surcharge_line.append([0, 0, values])
                rec.invoice_line_ids = surcharge_line
                rec.action_post()
            rec._compute_amount()
        return

    # def _create_payment_transaction(self, vals):
    #     '''Similar to self.env['payment.transaction'].create(vals) but the values are filled with the
    #     current invoices fields (e.g. the partner or the currency).
    #     :param vals: The values to create a new payment.transaction.
    #     :return: The newly created payment.transaction record.
    #     '''
    #     # Ensure the currencies are the same.
    #     currency = self[0].currency_id
    #     if any(inv.currency_id != currency for inv in self):
    #         raise ValidationError(_('A transaction can\'t be linked to invoices having different currencies.'))
    #
    #     # Ensure the partner are the same.
    #     partner = self[0].partner_id
    #     if any(inv.partner_id != partner for inv in self):
    #         raise ValidationError(_('A transaction can\'t be linked to invoices having different partners.'))
    #
    #     # Try to retrieve the acquirer. However, fallback to the token's acquirer.
    #     acquirer_id = vals.get('acquirer_id')
    #     acquirer = None
    #     payment_token_id = vals.get('payment_token_id')
    #
    #     if payment_token_id:
    #         payment_token = self.env['payment.token'].sudo().browse(payment_token_id)
    #
    #         # Check payment_token/acquirer matching or take the acquirer from token
    #         if acquirer_id:
    #             acquirer = self.env['payment.acquirer'].browse(acquirer_id)
    #             if payment_token and payment_token.acquirer_id != acquirer:
    #                 raise ValidationError(_('Invalid token found! Token acquirer %s != %s') % (
    #                 payment_token.acquirer_id.name, acquirer.name))
    #             if payment_token and payment_token.partner_id != partner:
    #                 raise ValidationError(_('Invalid token found! Token partner %s != %s') % (
    #                 payment_token.partner.name, partner.name))
    #         else:
    #             acquirer = payment_token.acquirer_id
    #
    #     # Check an acquirer is there.
    #     if not acquirer_id and not acquirer:
    #         raise ValidationError(_('A payment acquirer is required to create a transaction.'))
    #
    #     if not acquirer:
    #         acquirer = self.env['payment.acquirer'].browse(acquirer_id)
    #
    #     # Check a journal is set on acquirer.
    #     if not acquirer.journal_id:
    #         raise ValidationError(_('A journal must be specified for the acquirer %s.', acquirer.name))
    #
    #     if not acquirer_id and acquirer:
    #         vals['acquirer_id'] = acquirer.id
    #     updated_amount =0
    #     if len(self.invoice_line_ids.filtered(lambda line: line.name == 'Online Payment Surcharge')) == 0:
    #         if acquirer.is_surcharge:
    #             charge_amount = (acquirer.set_surcharge/100) * sum(self.mapped('amount_residual'))
    #             updated_amount = sum(self.mapped('amount_residual')) + charge_amount
    #         #     self.button_draft()
    #         #     surcharge_line = []
    #         #     product_surcharge = self.env['product.product'].search([('name', '=', 'Online Payment Surcharge')], limit=1)
    #         #     if not product_surcharge:
    #         #         product_surcharge = self.env['product.product'].create({'name': 'Online Payment Surcharge',
    #         #                                                                 'sale_ok': True,
    #         #                                                                 'purchase_ok': True})
    #         #     values = {
    #         #         'product_id': product_surcharge.id,
    #         #         'quantity': 1,
    #         #         'price_unit': charge_amount,
    #         #     }
    #         #     surcharge_line.append([0, 0, values])
    #         #     self.invoice_line_ids = surcharge_line
    #         #     self.action_post()
    #         #     self.amount_after_charge = updated_amount
    #         #     self.set_surcharge = charge_amount
    #         # self._compute_amount()
    #     pdb.set_trace()
    #     vals.update({
    #         'amount': updated_amount,
    #         'currency_id': currency.id,
    #         'partner_id': partner.id,
    #         'invoice_ids': [(6, 0, self.ids)],
    #     })
    #
    #     # vals.update({
    #     #     'amount': updated_amount,
    #     # })
    #
    #     transaction = self.env['payment.transaction'].create(vals)
    #
    #     # Process directly if payment_token
    #     if transaction.payment_token_id:
    #         transaction.s2s_do_transaction()
    #
    #     return transaction

    # def _compute_amount(self):
    #     res = super(AccountMove, self)._compute_amount()
    #     for rec in self:
    #         if rec.amount_after_charge > 0.0:
    #             rec.amount_total = rec.amount_after_charge
    #             rec.amount_residual = rec.amount_after_charge
