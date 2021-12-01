
from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError,UserError
import requests
import json
from datetime import date, datetime


api_url = ''
api_token = ''

headers = {
    'Authorization': api_token,
    'Content-Type': 'application/json'
}


class StockPickingIl(models.Model):
    _inherit = 'stock.picking'


    freight_price = fields.Float(string="Freight Price")
    shipping_quote_line_ids = fields.One2many('shipping.quote.line','stock_id',string='Shipping Quote Line')
    accept_state  = fields.Selection([('received', 'Quotes Received'),
                               ('accepted','Accepted'),
                               ('rejected','Rejected')],default='')

    def send_to_shipper(self):
        self.ensure_one()
        if self.carrier_id.delivery_type != 'il':
            res = self.carrier_id.send_shipping(self)[0]

            if self.carrier_id.free_over and self.sale_id and self.sale_id._compute_amount_total_without_delivery() >= self.carrier_id.amount:
                res['exact_price'] = 0.0
            self.carrier_price = res['exact_price'] * (1.0 + (self.carrier_id.margin / 100.0))
            if res['tracking_number']:
                self.carrier_tracking_ref = res['tracking_number']
            order_currency = self.sale_id.currency_id or self.company_id.currency_id
            msg = _(
                "Shipment sent to carrier %(carrier_name)s for shipping with tracking number %(ref)s<br/>Cost: %(price).2f %(currency)s",
                carrier_name=self.carrier_id.name,
                ref=self.carrier_tracking_ref,
                price=self.carrier_price,
                currency=order_currency.name
            )
            self.message_post(body=msg)
            self._add_delivery_cost_to_so()

    def request_shipping_quote(self):

        carrier= self.env['delivery.carrier'].search([('is_configuration_carrier','=',True)],limit=1)

        if carrier:
            api_url = str(carrier.url_link)
            api_token = str(carrier.il_api_token)
            if carrier.url_link == 'Null' or carrier.il_api_token == 'Null':
                raise ValidationError(
                    "Please first Add Carrier IL2000 credientials")
            products = []
            for move_line in self.move_ids_without_package:
                if not move_line.product_id.weight:
                    raise ValidationError("Please check products weights without weights IL2000 not allowed to request for shipping quotation")
                products.append({
                    "isFee": False,
                    "nmfc": None,
                    "nmfcClass": 55,
                    "isHazmat": False,
                    "numberHandlingUnitsInLineItem": 1,
                    "handlingUnitType": None,
                    "numberOfPieces": int(move_line.product_uom_qty),
                    "weight": move_line.product_id.weight,
                    "serialNumber": str(move_line.product_id.barcode),
                    "poNumberOfLineItem": None,
                    "length": 1,
                    "width": 1,
                    "height": 1,
                    "isStackable": False,
                    "productCode": str(move_line.product_id.default_code),
                    "description": str(move_line.product_id.name)
                })
            if not self.partner_id:
                raise UserError(_("Please Select Contact "))

            payload = json.dumps({
                "shipmentType": "LTL",
                "plantId": 627,
                "bolNumber": None,
                "poNumber": "VERBAL",
                "proNumber": str(self.origin)+'-'+str(self.name),
                "terms": "PP",
                "consignee": {
                    "careOf": None,
                    "postalCode": str(self.partner_id.zip) if self.partner_id.zip else None,
                    "customerPlantIdentifier": "LUMBERTON",
                    "name": str(self.partner_id.name) if self.partner_id.name else None,
                    "address": str(self.partner_id.street) if self.partner_id.street else None,
                    "address2": str(self.partner_id.street2) if self.partner_id.street2 else None,
                    "address3": None,
                    "city": str(self.partner_id.city) if self.partner_id.city else None,
                    "stateOrProvince": str(self.partner_id.state_id.name) if self.partner_id.state_id.name else None,
                    "contact": str(self.partner_id.name) if self.partner_id.name else None ,
                    "country": str(self.partner_id.country_id.name) if self.partner_id.country_id.name else None
                },
                "shipper": {
                    "careOf": None,
                    "postalCode": str(self.env.company.zip) if str(self.env.company.zip) else None,
                    "phone": str(self.env.company.phone) if self.env.company.phone else None,
                    "customerPlantIdentifier": None,
                    "name": str(self.env.company.name) if str(self.env.company.name) else None,
                    "address": str(self.env.company.street) if str(self.env.company.street) else None,
                    "address2": str(self.env.company.street2) if str(self.env.company.street2) else None,
                    "city": str(self.env.company.city) if str(self.env.company.city) else None,
                    "stateOrProvince": str(self.env.company.state_id.name) if str(self.env.company.state_id.name) else None,
                    "contact": str(self.env.company.phone) if self.env.company.phone else None,
                    "country": str(self.env.company.country_id.name) if str(self.env.company.country_id.name) else None
                },
                "billTo": {
                    "careOf": None,
                    "postalCode": str(self.env.company.zip) if str(self.env.company.zip) else None,
                    "phone": str(self.env.company.phone) if self.env.company.phone else None,
                    "customerPlantIdentifier": "Virginia Beach",
                    "name": str(self.env.company.name) if str(self.env.company.name) else None,
                    "address": str(self.env.company.street) if str(self.env.company.street) else None,
                    "address2": str(self.env.company.street2) if str(self.env.company.street2) else None,
                    "city": str(self.env.company.city) if str(self.env.company.city) else None,
                    "stateOrProvince": str(self.env.company.state_id.name) if str(self.env.company.state_id.name) else None,
                    "contact": str(self.env.company.phone) if self.env.company.phone else None,
                    "country": str(self.env.company.country_id.name) if str(self.env.company.country_id.name) else None
                },
                "carrierScac": "SEFL",
                "quoteId": self.origin,
                "totalHandlingUnits": 1,
                "specialInstructions": None,
                "shipmentCost": 0,
                "customerCost": 0,
                "shipmentValue": self.sale_id.amount_total,
                "lineItems": [
                    {
                        "isFee": False,
                        "nmfc": None,
                        "nmfcClass": 55,
                        "isHazmat": False,
                        "numberHandlingUnitsInLineItem": 1,
                        "handlingUnitType": None,
                        "numberOfPieces": 1,
                        "weight": 1,
                        "serialNumber": None,
                        "poNumberOfLineItem": None,
                        "length": 1,
                        "width": 1,
                        "height": 1,
                        "isStackable": False,
                        "productCode": "ZZZ",
                        "description": "REPLACE ME"
                    }
                ],
                "shipDate": str(self.date_deadline.strftime("%Y"))+'-'+str(self.date_deadline.strftime("%m"))+'-'+str(self.date_deadline.strftime("%d")),
                "referenceFields": [],
            })
            payload = json.loads(payload)
            payload["lineItems"] = products
            payload = json.dumps(payload)
            headers['Authorization'] = api_token
            response = requests.request(
                "POST", api_url, headers=headers, data=payload)

            if response.status_code == 201:
                
                response_data = json.loads(response.text)

           
       
                ship_quote = self.env['shipping.quote.line'].create(
                    {'name': self.name, 'stock_picking_id': self.id, 'ref': self.name,
                        'logistic_provider': carrier.name, 'shipping_weight': self.shipping_weight,
                        'weight_uom': self.weight_uom_name, 'rate': 0, 'shipid': response_data['id'],
                        'delivery_date': response_data["shipdate"],
                        'bol_no':response_data['bolnumber'],
                        'so_ref':self.origin,
                        }
                )
                ship_quote.get_shippment_rates()
                    # self.ship_quote_id = ship_quote.id

                return {
                    'domain': [('stock_picking_id', '=', self.id)],
                    'name': 'Shipping Quote Requested',
                    'type': 'ir.actions.act_window',
                    'res_model': 'shipping.quote.line',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'view_id': False,
                }
            else:
                raise ValidationError("Response Failed \n Please check contact details or check IL2000 configuration ")
        else:
            raise ValidationError("There is no configuration Carrier Selected! Please select 'IL2000' as a configuration Carrier in Shipping method")
    def request_shipping_quote_list(self):

        return {
            'domain': [('name', '=', self.name)],
            'name': _('Shipping Quote Requested List'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'shipping.quote.line',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }
