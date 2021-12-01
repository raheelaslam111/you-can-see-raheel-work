from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError




class ProductSelectWizard(models.TransientModel):
    _name = 'product.select.wizard'
    _description = 'product.select.wizard'


    # def _default_order_id(self):
    #     return self.env.context.get('active_id')
    # , default = _default_order_id

    # def _get_outputs(self):
    #     return self.env['product.product'].search([('id', 'in',self._context.get('active_ids'))])



    product_ids = fields.Many2many('product.product',string='Products',store=True)
    order_id = fields.Many2one('sale.order',string='Sale Order')

    delivery_rating_success = fields.Boolean(related='order_id.delivery_rating_success',copy=False)
    delivery_set = fields.Boolean(related='order_id.delivery_set')
    recompute_delivery_price = fields.Boolean(related='order_id.recompute_delivery_price',string='Delivery cost should be recomputed')
    is_all_service = fields.Boolean(related='order_id.is_all_service',string="Service Product")
    order_line = fields.One2many(related='order_id.order_line', string='Order Lines')


    def create_saleorder_line(self):
        if not self.order_id:
            raise ValidationError(_('You can not add products from here!'))
        for line in self.product_ids:
            print(line.lst_price,'list price',line.id,'line.id')
            values = {
                'product_id' : line.id,
                'price_unit': line.lst_price,
                'order_id': self.order_id.id
            }
            order_line = self.env['sale.order.line'].create(values)
            print(order_line.price_unit,order_line.product_id)
        self.order_id.recompute_coupon_lines()
        view_id = self.env.ref('delivery.choose_delivery_carrier_view_form').id
        if self.order_id.env.context.get('carrier_recompute'):
            name = _('Update shipping cost')
            carrier = self.order_id.carrier_id
        else:
            name = _('Add a shipping method')
            carrier = (
                    self.order_id.with_company(self.order_id.company_id).partner_shipping_id.property_delivery_carrier_id
                    or self.order_id.with_company(
                self.order_id.company_id).partner_shipping_id.commercial_partner_id.property_delivery_carrier_id
            )
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'choose.delivery.carrier',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_order_id': self.order_id.id,
                'default_carrier_id': carrier.id,
            }
        }