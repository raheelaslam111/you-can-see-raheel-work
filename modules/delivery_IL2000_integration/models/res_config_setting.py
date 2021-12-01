import pdb

from odoo import models, fields, api


class MResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    freight_flag  =  fields.Boolean(string='Freight Markup',config_parameter='delivery_IL2000_integration.freight_flag',required=False)
    freight_percentage  = fields.Char(config_parameter='delivery_IL2000_integration.freight_percentage')
