from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError




class ProductSelectGiftWizard(models.TransientModel):
    _name = 'product.select.gift.wizard'
    _description = 'product.select.gift.wizard'



    product_ids = fields.Many2many('product.product',string='Products')
    order_id = fields.Many2one('sale.order',string='Sale Order',context={'group_by': ['categ_id']})
    delivery_rating_success = fields.Boolean(related='order_id.delivery_rating_success', copy=False)
    delivery_set = fields.Boolean(related='order_id.delivery_set')
    recompute_delivery_price = fields.Boolean(related='order_id.recompute_delivery_price',
                                              string='Delivery cost should be recomputed')
    is_all_service = fields.Boolean(related='order_id.is_all_service', string="Service Product")
    order_line = fields.One2many(related='order_id.order_line', string='Order Lines')


    def gift_saleorder_line(self):
        if not self.order_id:
            raise ValidationError(_('You can not add products from here!'))
        if not any(self.order_id.order_line.filtered(lambda n: n.display_type == 'line_section' )):
            self.add_section()
        for line in self.product_ids:
            values = {
                'product_id' : line.id,
                'price_unit': 0.00,
                'order_id': self.order_id.id
            }
            order_line = self.env['sale.order.line'].create(values)
        return {'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_mode': 'form',
                'res_id': self.order_id.id,
                'target': 'main',
                'context': {
                    'id': self.order_id.id,
                    'active_id': False,
                }
                }



    def add_section(self):
        order_lines = []
        val = (0, 0, {
            'display_type': 'line_section',
            'name': 'Gift Items',
        })
        order_lines.append(val)
        self.order_id.update({'order_line': order_lines})




