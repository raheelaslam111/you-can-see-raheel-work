# -*- coding: utf-8 -*-
import pdb

from odoo import models, fields, api , _
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero, float_compare
from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare



from werkzeug.urls import url_encode


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    custom_deposit = fields.Boolean(string='Custom Deposit')

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"


    def down_payment_total(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        down_payment_total = 0.0
        for order in sale_orders:
            # for line in order.order_line.filtered(lambda b: b.is_downpayment==True):
            down_payment_total += order.down_payment_total
        return down_payment_total or 0

    def down_payment_applied(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        down_payment_applied = 0.0
        for order in sale_orders:
            # for line in order.order_line.filtered(lambda b: b.is_downpayment == True and b.custom_deposit == True):
            down_payment_applied += order.down_payment_applied
        return down_payment_applied or 0

    def down_payment_remaining(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        down_payment_remaining = 0.0
        for order in sale_orders:
            # for line in order.order_line.filtered(lambda b: b.is_downpayment == True and b.custom_deposit==False):
            down_payment_remaining += order.down_payment_remaining
        return down_payment_remaining or 0

    def apply_down_payment(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        down_payment_remaining = 0.0
        for order in sale_orders:
            # for line in order.order_line.filtered(lambda b: b.is_downpayment == True and b.custom_deposit==False):
            down_payment_remaining += order.down_payment_remaining
        return down_payment_remaining or 0


    down_payment_total = fields.Float(string='Down Payment Total: ',readonly=True,default=down_payment_total)
    down_payment_applied = fields.Float(string='Down Payment Applied: ',readonly=True,default=down_payment_applied)
    down_payment_remaining = fields.Float(string='Down Payment Remaining: ',readonly=True,default=down_payment_remaining)
    apply_down_payment = fields.Float(string='Apply Down Payment',default=apply_down_payment)




    def create_invoices(self):
        # remaining_amount = 0.0
        if self.deduct_down_payments == True and self.advance_payment_method== 'delivered':
            remaining_amount_dict = {}
            credit_inv_line = self.env['account.move.line']
            if self.apply_down_payment>self.down_payment_remaining:
                raise ValidationError(
                    _('The apply down payment amount must not be greater then remaining down payment!'))
            if  self.apply_down_payment<0:
                raise ValidationError(
                    _('The value of the down payment amount must be positive .'))
            if not(self.apply_down_payment>self.down_payment_remaining) and self.deduct_down_payments:
                sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
                deposit_product = self.env['product.product'].search([('name', '=', 'Deposit')], limit=1)
                # pdb.set_trace()
                if len(sale_orders)<2:
                    for order in sale_orders:
                        if self.apply_down_payment !=0:
                            values = {
                                'order_id': order.id,
                                'product_id': deposit_product,
                                'product_uom_qty': 0.0,
                                'price_unit': self.apply_down_payment,
                                'is_downpayment': True,
                                'custom_deposit': True,
                            }
                            order.down_payment_applied += self.apply_down_payment
                            # created_deposit_line = self.env['sale.order.line'].sudo().create(values)

                            self.env.context = dict(self.env.context)
                            self.env.context.update({
                                'order_id': order.id,
                                'product_id': deposit_product.id,
                                'product_uom_qty': 0.0,
                                'price_unit': self.apply_down_payment,
                                # 'is_downpayment': True,
                                'custom_deposit': True,
                            })

            res = super(SaleAdvancePaymentInv, self).create_invoices()
        else:
            res = super(SaleAdvancePaymentInv, self).create_invoices()

        return res




class SaleOrder(models.Model):
    _inherit = 'sale.order'

    down_payment_total = fields.Float(string='Down payment total', compute='down_payment_total_s')
    down_payment_applied = fields.Float(string='Down payment applied',copy=False,readonly=True,compute='get_down_payment_applied')
    down_payment_remaining = fields.Float(string='Down payment remaining', compute='down_payment_remaining_s')


    def get_down_payment_applied(self):
        for rec in self:
            down_payment_applied = 0
            for invoice in rec.invoice_ids.filtered(lambda b: b.state in ('draft', 'posted') and b.move_type not in ('out_refund')):
                for inv_line in invoice.invoice_line_ids.filtered(lambda b: b.product_id.name == 'Deposit' and b.price_subtotal < 0):
                    down_payment_applied += abs(inv_line.price_subtotal)
            for invoice in rec.invoice_ids.filtered(lambda b: b.state in ('draft', 'posted') and b.payment_state not in ('reversed') and b.move_type in ('out_refund')):
                for inv_line in invoice.invoice_line_ids.filtered(lambda b: b.product_id.name == 'Deposit' and b.price_subtotal < 0):
                    down_payment_applied -= abs(inv_line.price_subtotal)
            rec.down_payment_applied = abs(down_payment_applied)

    def down_payment_total_s(self):
        for rec in self:
            down_payment_total = 0.0
            for invoice in rec.invoice_ids.filtered(lambda b: b.state in ('draft', 'posted') and b.move_type not in ('out_refund')):
                for inv_line in invoice.invoice_line_ids.filtered(lambda b: b.product_id.name == 'Deposit' and b.price_subtotal > 0):
                    down_payment_total += abs(inv_line.price_subtotal)
            for invoice in rec.invoice_ids.filtered(lambda b: b.state in ('draft', 'posted') and b.payment_state not in ('reversed') and b.move_type in ('out_refund')):
                for inv_line in invoice.invoice_line_ids.filtered(lambda b: b.product_id.name == 'Deposit' and b.price_subtotal > 0):
                    down_payment_total -= abs(inv_line.price_subtotal)
            rec.down_payment_total = abs(down_payment_total)
            # for line in rec.order_line.filtered(lambda b: b.is_downpayment==True):
            #     down_payment_total += line.price_unit*line.qty_invoiced
            # rec.down_payment_total = down_payment_total



    def partial_downpayment(self):
        records = self.env['sale.order'].search([])
        for rec in records:
            down_payment_applied = 0
            for invoice in rec.invoice_ids.filtered(lambda b: b.state in ('draft','posted') and b.payment_state not in ('reversed')):
                for inv_line in invoice.invoice_line_ids.filtered(lambda b: b.product_id.name == 'Deposit' and b.custom_deposit==False and b.quantity<0):
                    down_payment_applied += inv_line.price_subtotal
            rec.down_payment_applied = abs(down_payment_applied)
                # if rec.down_payment_total and rec.down_payment_remaining:
                #     rec.down_payment_applied = rec.down_payment_total - rec.down_payment_remaining




    def _create_invoices(self, grouped=False, final=False, date=None):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        # 1) Create invoices.
        invoice_vals_list = []
        invoice_item_sequence = 0 # Incremental sequencing to keep the lines order on the invoice.
        for order in self:
            order = order.with_company(order.company_id)
            current_section_vals = None
            down_payments = order.env['sale.order.line']

            invoice_vals = order._prepare_invoice()
            invoiceable_lines = order._get_invoiceable_lines(final)

            if not any(not line.display_type for line in invoiceable_lines):
                raise self._nothing_to_invoice_error()

            invoice_line_vals = []
            down_payment_section_added = False
            print('invoiceable_lines',invoiceable_lines)
            for line in invoiceable_lines:
                if not down_payment_section_added and line.is_downpayment:
                    # Create a dedicated section for the down payments
                    # (put at the end of the invoiceable_lines)
                    invoice_line_vals.append(
                        (0, 0, order._prepare_down_payment_section_line(
                            sequence=invoice_item_sequence,
                        )),
                    )
                    dp_section = True
                    invoice_item_sequence += 1
                invoice_line_vals.append(
                    (0, 0, line._prepare_invoice_line(
                        sequence=invoice_item_sequence,
                    )),
                )

                invoice_item_sequence += 1

            # for partial deposit silverdale work
            if 'custom_deposit' in self.env.context:
                # pdb.set_trace()
                deposit_product = self.env['product.product'].search([('name', '=', 'Deposit')], limit=1)
                down_payments_section_line = {
                    'display_type': 'line_section',
                    'name': _('Down Payments'),
                    'product_id': False,
                    'product_uom_id': False,
                    'quantity': 0,
                    'discount': 0,
                    'price_unit': 0,
                    'account_id': False
                }
                invoice_line_vals.append(
                    (0, 0, down_payments_section_line),
                )
                res = {
                    # 'display_type': deposit_product.name,
                    # 'sequence': ,
                    'name': deposit_product.name,
                    'product_id': deposit_product.id,
                    # 'product_uom_id': deposit_product.product_uom.id,
                    'quantity': -1,
                    'price_unit': self.env.context.get('price_unit'),
                    'custom_deposit': True,
                }
                invoice_line_vals.append(
                    (0, 0, res),
                )

            invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise self._nothing_to_invoice_error()

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['payment_reference'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.

        # As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
        # in a single invoice. Example:
        # SO 1:
        # - Section A (sequence: 10)
        # - Product A (sequence: 11)
        # SO 2:
        # - Section B (sequence: 10)
        # - Product B (sequence: 11)
        #
        # If SO 1 & 2 are grouped in the same invoice, the result will be:
        # - Section A (sequence: 10)
        # - Section B (sequence: 10)
        # - Product A (sequence: 11)
        # - Product B (sequence: 11)
        #
        # Resequencing should be safe, however we resequence only if there are less invoices than
        # orders, meaning a grouping might have been done. This could also mean that only a part
        # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
        if len(invoice_vals_list) < len(self):
            SaleOrderLine = self.env['sale.order.line']
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice['invoice_line_ids']:
                    line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
                    sequence += 1

        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                subtype_id=self.env.ref('mail.mt_note').id
            )
        return moves


    def down_payment_remaining_s(self):
        for rec in self:
            # down_payment_remaining = 0.0
            # for line in rec.order_line.filtered(lambda b: b.is_downpayment==True and b.custom_deposit==False):
            #     # if line.invoice_status == 'to invoice':
            #     down_payment_remaining += line.price_unit
            # rec.down_payment_remaining = down_payment_remaining
            rec.down_payment_remaining = rec.down_payment_total-rec.down_payment_applied

    def _get_invoiceable_lines(self, final=False):
        down_payment_line_ids = []
        invoiceable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for line in self.order_line:
            if line.display_type == 'line_section':
                # Only invoice the section if one of its lines is invoiceable
                pending_section = line
                continue
            if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision):
                continue
            if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
                # if line.is_downpayment:
                #     # Keep down payment lines separately, to put them together
                #     # at the end of the invoice, in a specific dedicated section.
                #     down_payment_line_ids.append(line.id)
                #     continue
                if pending_section:
                    invoiceable_line_ids.append(pending_section.id)
                    pending_section = None
                if not line.is_downpayment == True:
                    invoiceable_line_ids.append(line.id)

        return self.env['sale.order.line'].browse(invoiceable_line_ids + down_payment_line_ids)



class AccountMove(models.Model):
    _inherit = 'account.move'


    def action_switch_invoice_into_refund_credit_note(self):
        if any(move.move_type not in ('in_invoice', 'out_invoice') for move in self):
            raise ValidationError(_("This action isn't available for this document."))

        for move in self:
            reversed_move = move._reverse_move_vals({}, False)
            new_invoice_line_ids = []
            for cmd, virtualid, line_vals in reversed_move['line_ids']:
                if not line_vals['exclude_from_invoice_tab']:
                    new_invoice_line_ids.append((0, 0,line_vals))
            if move.amount_total < 0:
                # Inverse all invoice_line_ids
                for cmd, virtualid, line_vals in new_invoice_line_ids:
                    line_vals.update({
                        'quantity' : -line_vals['quantity'],
                        'amount_currency' : -line_vals['amount_currency'],
                        'debit' : line_vals['credit'],
                        'credit' : line_vals['debit']
                    })
                # silverdale work for credit note during partial payment

            #     for move in self:
            #         if move.sale_order_id:
            #             if 'custom_deposit' in self.env.context:
            #                 move.sale_order_id.down_payment_applied += self.env.context.get('price_unit')
            #                 print(self.env.context.get('price_unit'),'action_switch_invoice_into_refund_credit_note')
            #                 pdb.set_trace()
            # pdb.set_trace()
            move.write({
                'move_type': move.move_type.replace('invoice', 'refund'),
                'invoice_line_ids' : [(5, 0, 0)],
                'partner_bank_id': False,
            })
            move.write({'invoice_line_ids' : new_invoice_line_ids})

    # def action_switch_invoice_into_refund_credit_note(self):
    #     res = super(AccountMove, self).action_switch_invoice_into_refund_credit_note()
    #     # silverdale work for credit note during partial payment
    #     # pdb.set_trace()
    #     for move in self:
    #         if move.sale_order_id:
    #             move.sale_order_id.down_payment_applied += self.env.context.get('price_unit')
    #     return res

    # def write(self, vals):
    #     remaining_amount_dict = {}
    #     for rec in self:
    #             key = (rec.id)
    #             remaining_amount_dict[key] = {'state': rec.state,
    #                                           'payment_state': rec.payment_state,
    #                                           'status': "not_done",
    #                                           }
    #     res = super(AccountMove, self).write(vals)
    #     for rec in self:
    #         if rec.id in remaining_amount_dict:
    #             if rec.state == 'cancel':
    #                 # invoice becomed canceled
    #                 if rec.state != remaining_amount_dict[rec.id].get('state'):
    #                     for line in rec.invoice_line_ids.filtered(lambda b: b.custom_deposit==True):
    #                         if line.move_id.sale_order_id:
    #                             line.move_id.sale_order_id.down_payment_applied -= abs(line.price_subtotal)
    #
    #             # canceled invoice reset to draft
    #             elif rec.state !='cancel' and remaining_amount_dict[rec.id].get('state')== 'cancel':
    #                 for line in rec.invoice_line_ids.filtered(lambda b: b.custom_deposit == True):
    #                     if line.move_id.sale_order_id:
    #                         line.move_id.sale_order_id.down_payment_applied += abs(line.price_subtotal)
    #             # # invoice is reversed by fully credit note
    #             # elif rec.payment_state == 'reversed' and remaining_amount_dict[rec.id].get('payment_state')!= 'reversed':
    #             #     for line in rec.invoice_line_ids.filtered(lambda b: b.custom_deposit == True):
    #             #         if line.move_id.sale_order_id:
    #             #             line.move_id.sale_order_id.down_payment_applied -= abs(line.price_subtotal)
    #     return res



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    custom_deposit = fields.Boolean(string='Custom Deposit')

    # def unlink(self):
    #     for rec in self:
    #         if rec.custom_deposit== True:
    #             rec.move_id.sale_order_id.down_payment_applied -= abs(rec.price_subtotal)
    #
    #     res = super(AccountMoveLine, self).unlink()
    #     return res

    # def write(self, vals):
    #     remaining_amount_dict = {}
    #     for rec in self:
    #         print(rec.price_subtotal)
    #         if rec.custom_deposit == True:
    #             key = (rec.id)
    #             remaining_amount_dict[key] = {'price_subtotal': rec.price_subtotal,
    #                                           'status': "not_done",
    #                                           }
    #     res = super(AccountMoveLine, self).write(vals)
    #     for rec in self:
    #         # for line which is converted in to custom deposit during write
    #         # pdb.set_trace()
    #         # if rec.move_id.sale_order_id and not rec.sale_line_ids and rec.custom_deposit==False and rec.quantity<1:
    #         #     rec.custom_deposit = True
    #         #     rec.move_id.sale_order_id.down_payment_applied+= abs(rec.price_subtotal)
    #         if rec.id in remaining_amount_dict:
    #             if rec.custom_deposit == True:
    #                 if remaining_amount_dict[rec.id].get('status') != 'done':
    #                     if rec.price_subtotal != remaining_amount_dict[rec.id].get('price_subtotal'):
    #                         if rec.price_subtotal < remaining_amount_dict[rec.id].get('price_subtotal'):
    #                             amount_to_be_added = rec.price_subtotal-remaining_amount_dict[rec.id].get('price_subtotal')
    #                             if rec.move_id.sale_order_id:
    #                                 rec.move_id.sale_order_id.down_payment_applied += abs(amount_to_be_added)
    #                                 remaining_amount_dict[rec.id].update({'status':'done'})
    #
    #                         elif rec.price_subtotal > remaining_amount_dict[rec.id].get('price_subtotal'):
    #                             amount_to_be_substracted = remaining_amount_dict[rec.id].get('price_subtotal')-rec.price_subtotal
    #                             if rec.move_id.sale_order_id:
    #                                 rec.move_id.sale_order_id.down_payment_applied -= abs(amount_to_be_substracted)
    #                                 remaining_amount_dict[rec.id].update({'status': 'done'})
    #     return res

    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super(AccountMoveLine, self).create(vals_list)
    #     for rec in res:
    #         if rec.move_id.move_type in ('out_invoice','out_refund'):
    #             if rec.move_id.sale_order_id and rec.product_id.name == 'Deposit' and rec.quantity<0 and rec.custom_deposit==False:
    #                 rec.custom_deposit = True
    #                 rec.move_id.sale_order_id.down_payment_applied -= rec.price_subtotal
    #
    #     return res

