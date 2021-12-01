from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError




class Product(models.Model):
    _inherit = 'product.product'

    is_shipment_product = fields.Boolean(string='Is Shipment Product',default=False)
    is_discount_product = fields.Boolean(string='Is discount Product',default=False)
