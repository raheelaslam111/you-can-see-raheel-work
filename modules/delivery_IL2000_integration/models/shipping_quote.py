import pdb

from odoo import _, api, fields, models, tools
import requests
import json
from odoo.exceptions import ValidationError


api_url = ''
api_token = ''
payload = {}
files = {}

headers = {
    'Authorization': api_token,
    'Content-Type': 'application/json'
}

# class ShippingQuote(models.Model):
#     _name='shipping.quote'
#     _description='ADD api data '
#
#     name = fields.Char("Name")
#     so_ref  = fields.Char("Source Document")
#     quote_ids =fields.One2many('shipping.quote.line', 'shipping_quote_id',string="Shiping Quotes List")
#     state = fields.Selection([('draft', 'Draft'), ('quote_received', 'Quote Received')], string='Status', default='quote_received')


class ShippingQuoteLine(models.Model):
    _name = 'shipping.quote.line'
    _description = 'new model to create and record shipment details from IL2000'
    _inherit = [ 'mail.thread', 'mail.activity.mixin',]

    name = fields.Char("Name")
    so_ref  = fields.Char("Source Document")
    ref = fields.Char("Delivery Order Ref")
    logistic_provider = fields.Char("Logistic Provider")
    rate = fields.Float("Rate")
    rate_cur = fields.Char()
    # shipping_quote_id = fields.Many2one('shipping.quote')
    shipping_weight = fields.Float('Weight')
    weight_uom = fields.Char()
    shipid = fields.Char("Shipment ID")
    rate_ids = fields.One2many(
        'shipping.quote.line.rates', 'shipping_quote_id', string="Carriers Rates")
    state = fields.Selection([('received', 'Quotes Received'),
                              ('accepted', 'Accepted'),
                              ('rejected', 'Rejected')], default='received')
    delivery_date = fields.Date("Delivery Date")
    stock_id = fields.Many2one('stock.picking', string='Delivery Order')
    stock_picking_id = fields.Many2one('stock.picking')
    bol_no = fields.Char("BoL No ")

    @api.constrains('rate_ids')
    def _check_selected_rate(self):
        for rec in self:
            if len(rec.rate_ids.filtered(lambda b: b.selected_rate == 'True' and b.quote_state == 'accepted')) > 1:
                raise ValidationError(
                    _("You can select only one Quotation Rate!"))

    def accept_quote_function(self):
        self.state = 'accepted'
        if len(self.rate_ids.filtered(lambda b: b.selected_rate == True)) == 0:
            raise ValidationError(
                _("You have to select the one carrier rate!"))
        delivery_order = self.env['stock.picking'].search(
            [('name', '=', self.ref)], limit=1)
        self.stock_id = delivery_order.id
        carrier = self.rate_ids.filtered(lambda b: b.selected_rate == True)
        for carrier in carrier:
            product = self.env['product.product'].search(
                [('name', '=', 'IL '+carrier.carriername)], limit=1)
            if not product:
                product = self.env['product.product'].create(
                    {
                        'name': 'IL '+carrier.carriername,
                        'sale_ok': True,
                        'purchase_ok': True,
                        'type': 'service',
                        'lst_price': 0.0,
                        'standard_price': 0.0,
                    }
                )
            delivery_carrier = self.env['delivery.carrier'].search(
                [('is_configuration_carrier', '=', True)], limit=1)
            self.stock_id.carrier_id = delivery_carrier.id
           
            self.stock_id.carrier_tracking_ref = self.shipid
            self.stock_id.accept_state = 'accepted'
            freight_percentage =self.env['ir.config_parameter'].sudo().get_param('delivery_IL2000_integration.freight_percentage') or False
            freight_flag = self.env['ir.config_parameter'].sudo().get_param('delivery_IL2000_integration.freight_flag') or 'False'
            temp=0
            if freight_flag == 'True' and freight_percentage:
                # raise ValidationError("Please turn on Freight Markup Settings!")
                temp=float(freight_percentage)

            fp = ((float(carrier.rate) * temp) / 100) + float(carrier.rate)
            sale_order = self.env['sale.order'].search(
                [('name', '=', self.stock_id.origin)], limit=1)
            if sale_order:
                order_line = self.env['sale.order.line'].create(
                    {
                        'product_id': product.id,
                        'is_delivery': True,
                        'product_uom_qty': 1.0,
                        'price_unit': fp if fp > 0 else carrier.rate,
                        'name': product.name,
                        'order_id': sale_order.id,
                    }
                )
                sale_order.carrier_id = delivery_carrier.id
            self.stock_id.freight_price = fp if fp > 0 else carrier.rate
            self.stock_id.carrier_price = fp if fp > 0 else carrier.rate
            self.stock_id.carrier_tracking_ref = self.shipid

            order_currency = self.stock_id.sale_id.currency_id or self.stock_id.company_id.currency_id
            msg = _(
                "Shipment accepted by carrier %(carrier_name)s for shipping with tracking number %(ref)s<br/>Cost: %(price).2f %(currency)s",
                carrier_name=self.stock_id.carrier_id.name,
                ref=self.stock_id.carrier_tracking_ref,
                price=self.stock_id.carrier_price,
                currency=order_currency.name
            )
            self.stock_id.message_post(body=msg)


        shipping_quote_line = self.env['shipping.quote.line'].search(
            [('id', '!=', self.id), ('stock_picking_id', '=', self.stock_picking_id.id)])
        for line in shipping_quote_line:
            line.state = 'rejected'
            line.stock_id = False

    def unlink(self):
        if self.state == 'accepted':
            raise ValidationError(
                "Not Allowed to Delete Shipment with Accepted Status")
        elif self.state == 'rejected':
            raise ValidationError(
                "Not Allowed to Delete Shipment with Rejected Status")

        res = super(ShippingQuoteLine, self).unlink()
        return res

    def get_shippment_rates(self):
        carrier = self.env['delivery.carrier'].search(
            [('name', '=', 'IL2000')])
        if carrier:
            api_url = str(carrier.url_link)+'/'+str(self.shipid)+'/rates'
            api_token = str(carrier.il_api_token)

            headers['Authorization'] = api_token
            response = requests.request(
                "GET", api_url, headers=headers, data=payload)
            response_data = json.loads(response.text)
            print("respoonse rate ",response_data)
            # pdb.set_trace()
            if response.status_code == 200:
                for res in response_data['rates']:
                    is_exist = False
                    for rate in self.rate_ids:
                        if res['carrierID'] == rate.carrier_id:
                            is_exist = True
                            rate.carrier_id = res['carrierID']
                            rate.carriername = res['carrierName']
                            rate.rate = int(res['rate'])
                            rate.transit_time = res['transitTime']
                            break

                    if not is_exist:
                        shipping_quote_rates = self.env['shipping.quote.line.rates'].create({
                            'carrier_id': res['carrierID'],
                            'carriername': res['carrierName'],
                            'rate': int(res['rate']),
                            'transit_time': res['transitTime'],
                            'shipping_quote_id': self.id

                        })
            else:
                raise ValidationError("Response failed for fetch rate....! \n Please check your IL2000 configuration or \n issue due to IL2000 website server down ")


class ShippingQuoteLineRates(models.Model):
    _name = 'shipping.quote.line.rates'

    _description = 'record shipment rate'

    carrier_id = fields.Integer()
    carriername = fields.Char("Carrier Name")
    # logistic_provider  = fields.Char("Logistic Provider")
    rate = fields.Float("Rate")
    transit_time = fields.Char("Transit Time")
    # rate_cur  = fields.Char()
    shipping_quote_id = fields.Many2one('shipping.quote.line')
    quote_state = fields.Selection(related='shipping_quote_id.state')
    # shipping_weight  = fields.Float('Weight')
    # weight_uom  = fields.Char()
    selected_rate = fields.Boolean(string='Selected Rate')

    @api.onchange('selected_rate')
    def check_selected_rate_with_state(self):
        for rec in self:
            if rec.quote_state != 'received':
                raise ValidationError(
                    _("You can only select Rate in Receive state!"))
            elif len(rec.shipping_quote_id.rate_ids.filtered(lambda b: b.selected_rate == True)) > 1:
                raise ValidationError(
                    _("You can select only one Quotation Rate!"))
                # rec.selected_rate = False

    class SaleOrdermy(models.Model):

        _inherit = 'sale.order'

        il_delivery_type = fields.Selection(related="carrier_id.delivery_type")

        def fetch_shipping_quotes(self):
            return {
                'domain': [('so_ref', '=', self.name)],
                'name': _('Shipping Quote Requested List'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'shipping.quote.line',
                'view_id': False,
                'type': 'ir.actions.act_window'
            }
