from odoo import models, fields, api



class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def create(self, vals):
        res = super(AccountMoveLine, self).create(vals)
        if res.price_unit > 0.0:
            res.sequence = 1
        if res.product_id.is_discount_product:
            is_add = False
            for line in res.move_id.invoice_line_ids:
                if line.name == 'Discount Items':
                    is_add = True
            if not is_add:
                self.create({
                    'display_type': 'line_section',
                    'name': 'Discount Items',
                    'sequence': 1000,
                    'move_id': res.move_id.id,
                })
            res.sequence = 10000
        return res
