import logging
import pdb
import pprint
from datetime import datetime
from odoo.addons.payment.models.payment_acquirer import ValidationError
import hashlib
import hmac
import werkzeug
from odoo import http
from odoo.http import request
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _
import json
from odoo.tools.float_utils import float_repr
from odoo.addons.payment.controllers.portal import WebsitePayment
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.payment_helcim.controllers.main import HelcimController

_logger = logging.getLogger(__name__)



class HelcimControllerinherit(HelcimController):

    @http.route(['/helcim/modal'], type='json', auth="public", methods=['POST'], website=True)
    def helcim_modal(self, **kwargs):
        type = None
        order = None
        if 'orderId' in kwargs and kwargs['orderId'] and not isinstance(kwargs['orderId'], int) and not kwargs[
            'invoice']:
            if 'orderId' in kwargs and kwargs['orderId'] and 'orders' in kwargs['orderId']:
                order_id = [value for value in kwargs['orderId'].split('/') if value.isdigit()]
                if len(order_id) > 0:
                    order = request.env['sale.order'].sudo().search([('id', '=', int(order_id[0]))])
                type = 'order'

        elif 'orderId' in kwargs and isinstance(kwargs['orderId'], int):
            order = request.env['sale.order'].sudo().search([('id', '=', int(kwargs['orderId']))])
            type = 'order'

        elif 'invoice' in kwargs and kwargs['invoice']:
            invoice = kwargs['invoice'].split('/')
            if len(invoice) > 2:
                invoice_id = [value for value in invoice[3].split('?') if value.isdigit()]
                if len(invoice_id) > 0:
                    order = request.env['account.move'].sudo().search([('id', '=', int(invoice_id[0]))])
                    type = 'invoice'
                # else:
                #     order = request.env['account.move'].search([('id', '=', int(invoice_id[0]))])

        elif 'link_url' in kwargs and kwargs['link_url']:
            invoice = kwargs['link_url'].split('=')
            if invoice and len(invoice) > 1:
                invoice_id = invoice[1].split('&')[0]
                if invoice_id:
                    order = request.env['account.move'].sudo().search([('payment_reference', '=', invoice_id)])
                    if order:
                        type = 'invoice'
                    else:
                        order = request.env['sale.order'].sudo().search([('name', '=', invoice_id)])
                        type = 'order'



        else:
            order = request.website.sale_get_order()
        print("order details", order)
        if 'acquirer_id' in kwargs:
            acquirere_id = int(kwargs['acquirer_id'])
        else:
            acquirere_id = request.website.get_helcim_payment_acquirere_id()
        acquirere = request.env['payment.acquirer'].sudo().browse(int(acquirere_id))
        saleorder = order

        amount = 0
        if order._name == 'account.move':
            if acquirere.is_surcharge:
                charge_amount = (acquirere.set_surcharge / 100) * sum(order.mapped('amount_residual'))
                amount = order.amount_residual + charge_amount
        else:
            if acquirere.is_surcharge:
                charge_amount = (acquirere.set_surcharge / 100) * sum(order.mapped('amount_total'))
                amount = order.amount_total+charge_amount
        # pdb.set_trace()

        if acquirere.helcim_js_token and acquirere.helcim_account_id and acquirere.helcim_terminal_id and acquirere.helcim_api_token and saleorder:
            vals = {
                'return_url': '/shop/payment/validate',
                'reference': order.id,
                'order_type': type,
                'sale_order': saleorder,
                'amount_total': '%.2f' % float(amount) or 0.0,
                'currency': order.currency_id,
                'acquirer_details': acquirere,
                'customer': order.partner_id,

            }

            return request.env['ir.ui.view'].sudo()._render_template("payment_helcim.helcim_template_modal", vals)
        else:
            _logger.error('The Helcim API Credentials or Records missing!')
            return False

    # @http.route(['/helcim/modal'], type='json', auth="public", methods=['POST'], website=True)
    # def helcim_modal(self,**kwargs):
    #     type = None
    #     order = None
    #     surcharge = 0
    #     # pdb.set_trace()
    #     if 'orderId' in kwargs and kwargs['orderId'] and not isinstance(kwargs['orderId'], int) and not kwargs['invoice']:
    #         if 'orderId' in kwargs and kwargs['orderId'] and 'orders' in kwargs['orderId']  :
    #             order_id = [value for value in kwargs['orderId'].split('/') if value.isdigit()]
    #             if len(order_id)>0:
    #                 order = request.env['sale.order'].sudo().search([('id','=',int(order_id[0]))])
    #                 if len(order.order_line.filtered(lambda line: line.name == 'Online Payment Surcharge')) == 0:
    #                     if 'acquirer_id' in kwargs:
    #                         acquirere_id = int(kwargs['acquirer_id'])
    #                     else:
    #                         acquirere_id = request.website.get_helcim_payment_acquirere_id()
    #                     acquirer = request.env['payment.acquirer'].sudo().browse(int(acquirere_id))
    #                     print(order)
    #                     print(order.state)
    #                     call = order._custom_function_surcharge_saleorder(acquirer=acquirer)
    #             type = 'order'
    #
    #     elif 'orderId' in kwargs and isinstance(kwargs['orderId'], int):
    #         order = request.env['sale.order'].sudo().search([('id', '=', int(kwargs['orderId']))])
    #         if len(order.order_line.filtered(lambda line: line.name == 'Online Payment Surcharge')) == 0:
    #             if 'acquirer_id' in kwargs:
    #                 acquirere_id = int(kwargs['acquirer_id'])
    #             else:
    #                 acquirere_id = request.website.get_helcim_payment_acquirere_id()
    #             acquirer = request.env['payment.acquirer'].sudo().browse(int(acquirere_id))
    #             print(order)
    #             print(order.state)
    #             call = order._custom_function_surcharge(acquirer=acquirer)
    #         type = 'order'
    #
    #     elif 'invoice' in kwargs and kwargs['invoice']:
    #         invoice = kwargs['invoice'].split('/')
    #         if len(invoice)>2:
    #             invoice_id = [value for value in invoice[3].split('?') if value.isdigit()]
    #             if len(invoice_id)>0:
    #                 order = request.env['account.move'].sudo().search([('id', '=', int(invoice_id[0]))])
    #                 type = 'invoice'
    #                 # if len(order.invoice_line_ids.filtered(lambda line: line.name == 'Online Payment Surcharge')) == 0:
    #                 #     if 'acquirer_id' in kwargs:
    #                 #         acquirere_id = int(kwargs['acquirer_id'])
    #                 #     else:
    #                 #         acquirere_id = request.website.get_helcim_payment_acquirere_id()
    #                 #     acquirer = request.env['payment.acquirer'].sudo().browse(int(acquirere_id))
    #                 #     print(order)
    #                 #     print(order.state)
    #                 #     call = order._custom_function_surcharge(acquirer=acquirer)
    #
    #             else:
    #                 order = request.env['account.move'].search([('id', '=', int(invoice_id[0]))])
    #                 # if len(order.invoice_line_ids.filtered(lambda line: line.name == 'Online Payment Surcharge')) == 0:
    #                 #     if 'acquirer_id' in kwargs:
    #                 #         acquirere_id = int(kwargs['acquirer_id'])
    #                 #     else:
    #                 #         acquirere_id = request.website.get_helcim_payment_acquirere_id()
    #                 #     acquirer = request.env['payment.acquirer'].sudo().browse(int(acquirere_id))
    #                 #     # print(acquirer.name)
    #                 #     print(order)
    #                 #     print(order.state)
    #                 #     call = order._custom_function_surcharge(acquirer=acquirer)
    #
    #
    #     elif 'link_url' in kwargs and kwargs['link_url']:
    #         invoice = kwargs['link_url'].split('=')
    #         if invoice and len(invoice)>1:
    #             invoice_id = invoice[1].split('&')[0]
    #             if invoice_id:
    #                 order = request.env['account.move'].sudo().search([('payment_reference','=',invoice_id)])
    #                 if order:
    #                     type = 'invoice'
    #                     # if len(order.invoice_line_ids.filtered(lambda line: line.name == 'Online Payment Surcharge')) == 0:
    #                     #     if 'acquirer_id' in kwargs:
    #                     #         acquirere_id = int(kwargs['acquirer_id'])
    #                     #     else:
    #                     #         acquirere_id = request.website.get_helcim_payment_acquirere_id()
    #                     #     acquirer = request.env['payment.acquirer'].sudo().browse(int(acquirere_id))
    #                     #     print(order)
    #                     #     print(order.state)
    #                     #     call = order._custom_function_surcharge(acquirer=acquirer)
    #
    #                 else:
    #                     order = request.env['sale.order'].sudo().search([('name','=',invoice_id)])
    #                     if len(order.order_line.filtered(lambda line: line.name == 'Online Payment Surcharge')) == 0:
    #                         if 'acquirer_id' in kwargs:
    #                             acquirere_id = int(kwargs['acquirer_id'])
    #                         else:
    #                             acquirere_id = request.website.get_helcim_payment_acquirere_id()
    #                         acquirer = request.env['payment.acquirer'].sudo().browse(int(acquirere_id))
    #                         print(order)
    #                         print(order.state)
    #                         call = order._custom_function_surcharge(acquirer=acquirer)
    #                     type = 'order'
    #
    #
    #
    #     else:
    #         order = request.website.sale_get_order()
    #     print("order details", order)
    #     if 'acquirer_id' in kwargs:
    #         acquirere_id = int(kwargs['acquirer_id'])
    #     else:
    #         acquirere_id = request.website.get_helcim_payment_acquirere_id()
    #     acquirere = request.env['payment.acquirer'].sudo().browse(int(acquirere_id))
    #     saleorder = order
    #
    #     if  acquirere.helcim_js_token and  acquirere.helcim_account_id and  acquirere.helcim_terminal_id and  acquirere.helcim_api_token and saleorder:
    #         vals = {
    #             'return_url': '/shop/payment/validate',
    #             'reference': order.id,
    #             'order_type': type,
    #             'sale_order': saleorder,
    #             'amount_total': '%.2f' % order.amount_total or 0.0,
    #             'currency': order.currency_id,
    #             'acquirer_details': acquirere,
    #             'customer': order.partner_id,
    #
    #         }
    #
    #         return request.env['ir.ui.view'].sudo()._render_template("payment_helcim.helcim_template_modal", vals)
    #     else:
    #         _logger.error('The Helcim API Credentials or Records missing!')
    #         return False







