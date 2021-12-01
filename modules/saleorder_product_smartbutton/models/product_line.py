import pdb

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError



class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        if res.price_unit > 0.0:
            res.sequence = 1
        if res.product_id.is_discount_product:
            res.sequence = 10000
        return res

    # if self.is_ignore_gift_line == True or (self.categ_ids and len(
    #         self.categ_ids.filtered(lambda c: c.id == line.product_id.categ_id.id)) < 1):
    #     print('yes')
    #     if line.price_unit > 0.0 and len(self.categ_ids.filtered(lambda c: c.id == line.product_id.categ_id.id)) < 1:
    #         print(len(self.categ_ids.filtered(lambda c: c.id == line.product_id.categ_id.id)))