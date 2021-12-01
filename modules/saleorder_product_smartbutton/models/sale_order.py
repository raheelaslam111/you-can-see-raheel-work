from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError



class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_email = fields.Char(related='partner_id.email')
    partner_phone = fields.Char(related='partner_id.phone')
    total_count_products = fields.Integer(string='Total Count',compute='_get_total_count_products')
    delivery_number = fields.Char(string='Delivery Number', compute='_get_delivery_number')
    for_compute_discount = fields.Char(sting='For computation', compute='make_discount_section')

    @api.depends('order_line')
    def make_discount_section(self):
        for rec in self:
            rec.for_compute_discount = "Ho gya"
            vals_list = []
            discount_lines = rec.order_line.filtered(lambda l: l.product_id and l.product_id.is_discount_product)
            discount_section = rec.order_line.filtered(lambda l: l.name == 'Discount Items')
            if discount_lines and not discount_section:
                vals = {
                    'display_type': 'line_section',
                    'name': 'Discount Items',
                    'sequence': 1000,
                    'order_id': rec._origin.id,
                }
                vals_list.append([0, 0, vals])
                rec.order_line = vals_list
            # elif not discount_lines and discount_section:
            #     discount_section.unlink()

    def _get_delivery_number(self):
        for rec in self:
            list = ''
            if rec.picking_ids:
                for line in rec.picking_ids:
                    list += line.name+', '
                rec.delivery_number = str(list)
            else:
                rec.delivery_number = False

    def _get_total_count_products(self):
        for rec in self:
            total = 0
            for line in rec.order_line.filtered(lambda line: line.display_type == False and line.is_delivery==False and line.product_id.is_shipment_product==False and line.product_id.is_discount_product==False):
            # for rec in self.order_line:
                total += line.product_uom_qty
            rec.total_count_products = total
