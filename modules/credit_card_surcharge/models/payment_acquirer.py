# -*- coding: utf-8 -*-
import pdb

from odoo import models, fields, api,_
from odoo import api, exceptions, fields, models, _, SUPERUSER_ID
from odoo.tools.misc import formatLang
import json



class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def write(self, vals):
        print(vals)
        res = super(AccountPayment, self).write(vals)
        return res

class CreditCardSubcharge(models.Model):
    _inherit = 'payment.acquirer'

    is_surcharge = fields.Boolean(
        string='Add Surcharge',
        required=False)
    set_surcharge = fields.Float(
        string='Surcharge')



class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'



    # @api.model
    # def create(self, vals):
    #     res = super(PaymentTransaction, self).create(vals)
    #     if res.acquirer_id.name == "Helcim":
    #         pdb.set_trace()
    #         charge_amount = (res.acquirer_id.set_surcharge / 100) * res.amount
    #         res.amount = res.amount+charge_amount
    #     return res



    def _get_payment_transaction_received_message(self):
        self.ensure_one()
        amount = formatLang(self.env, self.amount, currency_obj=self.currency_id)
        message_vals = [self.reference, self.acquirer_id.name, amount]
        if self.state == 'pending':
            message = _('The transaction %s with %s for %s is pending.')
        elif self.state == 'authorized':
            message = _('The transaction %s with %s for %s has been authorized. Waiting for capture...')
        elif self.state == 'done':
            message = _('The transaction %s with %s for %s has been confirmed. The related payment is posted: %s')
            message_vals.append(self.payment_id._get_payment_chatter_link())
        elif self.state == 'cancel' and self.state_message:
            message = _('The transaction %s with %s for %s has been cancelled with the following message: %s')
            message_vals.append(self.state_message)
        elif self.state == 'error' and self.state_message:
            message = _('The transaction %s with %s for %s has return failed with the following error message: %s')
            message_vals.append(self.state_message)
        else:
            message = _('The transaction %s with %s for %s has been cancelled.')


        return message % tuple(message_vals)



    def _create_payment(self, add_payment_vals={}):
        ''' Create an account.payment record for the current payment.transaction.
        If the transaction is linked to some invoices, the reconciliation will be done automatically.
        :param add_payment_vals:    Optional additional values to be passed to the account.payment.create method.
        :return:                    An account.payment record.
        '''
        self.ensure_one()

        so = None
        inv = None
        updated_amount=self.amount
        if self.state == 'done':
            if self.acquirer_id.provider == "helcim":
                x = self.reference.split("-")
                so = self.env['sale.order'].search([('name', '=', x[0])], limit=1)
                if so:

                    charge_amount = (self.acquirer_id.set_surcharge / 100) * sum(so.mapped('amount_total'))
                    updated_amount = sum(so.mapped('amount_total')) + charge_amount
                    # self.action_draft()
                    surcharge_line = []
                    product_surcharge = self.env['product.product'].search([('name', '=', 'Online Payment Surcharge')],
                                                                           limit=1)
                    order_line = self.env['sale.order.line'].search(
                        [('product_id', '=', product_surcharge.id), ('order_id', '=', so.id)],
                        limit=1)
                    if not order_line:
                        print(so.state)
                        values = {
                            'product_id': product_surcharge.id,
                            'product_uom_qty': 1.0,
                            'price_unit': charge_amount,
                            'product_uom': product_surcharge.uom_id.id,
                            'order_id': so.id,
                            'qty_delivered': 1,
                            'name': product_surcharge.name,
                        }
                        surcharge_line.append([0, 0, values])
                        order_line = self.env['sale.order.line'].create(values)
                    # so.order_line = surcharge_line
                    # so.custom_function_surcharge_saleorder(acquirer=self.acquirer_id)
                else:
                    x = self.reference.split("-")
                    invoice_number = ""
                    if len(x) > 1:
                        invoice_number = x[0] + "-" + x[1]
                    inv = self.env['account.move'].search([('name', '=', invoice_number)], limit=1)
                    if inv:
                        # inv.custom_function_surcharge(acquirer=self.acquirer_id)
                        # pdb.set_trace()
                        charge_amount = (self.acquirer_id.set_surcharge / 100) * sum(inv.mapped('amount_residual'))
                        updated_amount = sum(inv.mapped('amount_residual')) + charge_amount
                        surcharge_line = []
                        product_surcharge = self.env['product.product'].search(
                            [('name', '=', 'Online Payment Surcharge')], limit=1)
                        order_line = self.env['account.move.line'].search(
                            [('product_id', '=', product_surcharge.id), ('move_id', '=', inv.id)],
                            limit=1)
                        if not order_line:
                            reconciled_info_values  = inv.sudo()._get_reconciled_info_JSON_values()

                            inv.button_draft()
                            values = {
                                'product_id': product_surcharge.id,
                                'quantity': 1,
                                'price_unit': charge_amount,
                                'move_id': inv.id,
                            }
                            surcharge_line.append([0, 0, values])
                            # order_line = self.env['account.move.line'].create(values)
                            inv.sudo().invoice_line_ids = surcharge_line

                            inv.action_post()

                            # This is for outstanding balance, we don't need it at the moment
                            # if inv.sudo().invoice_outstanding_credits_debits_widget != "false":
                            #     outstandings = inv.sudo().invoice_outstanding_credits_debits_widget
                            #     outstandings = json.loads(outstandings)
                            #     outstandings = outstandings['content']
                            #     for outstanding in outstandings:
                            #         inv.js_assign_outstanding_line(outstanding.get('id'))

                            payment_id_list = []
                            if reconciled_info_values != "false":
                                for reconciled_info_value in reconciled_info_values:
                                    #this is for partial payment.
                                    if reconciled_info_value.get('payment_id') not in payment_id_list:
                                        payment_id_list.append(reconciled_info_value.get('payment_id'))
                                        inv.js_assign_outstanding_line(reconciled_info_value.get('payment_id'))


                            inv._compute_amount()

        payment_vals = {
            'amount': updated_amount,
            'payment_type': 'inbound' if self.amount > 0 else 'outbound',
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.commercial_partner_id.id,
            'partner_type': 'customer',
            'journal_id': self.acquirer_id.journal_id.id,
            'company_id': self.acquirer_id.company_id.id,
            'payment_method_id': self.env.ref('payment.account_payment_method_electronic_in').id,
            'payment_token_id': self.payment_token_id and self.payment_token_id.id or None,
            'payment_transaction_id': self.id,
            'ref': self.reference,
            **add_payment_vals,
        }
        payment = self.env['account.payment'].create(payment_vals)
        payment.action_post()

        # Track the payment to make a one2one.
        self.payment_id = payment

        if self.invoice_ids:
            self.invoice_ids.filtered(lambda move: move.state == 'draft')._post()

            (payment.line_ids + self.invoice_ids.line_ids)\
                .filtered(lambda line: line.account_id == payment.destination_account_id and not line.reconciled)\
                .reconcile()

        return payment


