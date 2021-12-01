from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, ValidationError



class ProviderGrid(models.Model):
    _inherit = 'delivery.carrier'


    is_ignore_gift_line = fields.Boolean(string='Want to ignore line with price Zero?')
    categ_ids = fields.Many2many('product.category',string='Want to ignore categories')



    def _get_price_available(self, order):
        self.ensure_one()
        self = self.sudo()
        order = order.sudo()
        total = weight = volume = quantity = 0
        total_delivery = 0.0
        for line in order.order_line:
            if line.state == 'cancel':
                continue
            if line.is_delivery:
                total_delivery += line.price_total
            if not line.product_id or line.is_delivery:
                continue
            list = []
            for cat in self.categ_ids:
                list.append(cat.id)
            if self.is_ignore_gift_line == True:
                print(self.categ_ids.ids,line.product_id.categ_id.id)
                if line.price_unit > 0.0 and line.product_id.categ_id.id not in list:
                    print('if')
                    qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
                    weight += (line.product_id.weight or 0.0) * qty
                    volume += (line.product_id.volume or 0.0) * qty
                    quantity += qty
                    total = (order.amount_total or 0.0) - total_delivery

                    total = order.currency_id._convert(
                        total, order.company_id.currency_id, order.company_id, order.date_order or fields.Date.today())
            elif self.categ_ids:
                if line.product_id.categ_id.id not in list:
                    print('else')
                    qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
                    weight += (line.product_id.weight or 0.0) * qty
                    volume += (line.product_id.volume or 0.0) * qty
                    quantity += qty
                    total = (order.amount_total or 0.0) - total_delivery

                    total = order.currency_id._convert(
                        total, order.company_id.currency_id, order.company_id, order.date_order or fields.Date.today())
            else:
                qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
                weight += (line.product_id.weight or 0.0) * qty
                volume += (line.product_id.volume or 0.0) * qty
                quantity += qty
                total = (order.amount_total or 0.0) - total_delivery

                total = order.currency_id._convert(
                    total, order.company_id.currency_id, order.company_id, order.date_order or fields.Date.today())

        return self._get_price_from_picking(total, weight, volume, quantity)



class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    def button_confirm(self):
        self.order_id.set_delivery_line(self.carrier_id, self.delivery_price)
        self.order_id.write({
            'recompute_delivery_price': False,
            'delivery_message': self.delivery_message,
        })
        self.ensure_one()
        return {'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_mode': 'form',
                'res_id': self.order_id.id,
                'target': 'main',
                'context': {
                    'id': self.order_id.id,
                    'active_id': False,
                }
                # 'flags': {'form': {'action_buttons': True}}
                }