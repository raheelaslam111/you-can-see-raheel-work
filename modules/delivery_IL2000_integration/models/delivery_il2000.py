import logging
import time

from odoo import api, models, fields, _, tools
from odoo.exceptions import UserError
from odoo.tools import pdf



_logger = logging.getLogger(__name__)



class ProviderIL(models.Model):
    _inherit = 'delivery.carrier'

    is_configuration_carrier = fields.Boolean(string='Is Configuration Carrier')
    delivery_type = fields.Selection(selection_add=[
        ('il', "IL2000")
    ], ondelete={'il': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0})})

    il_api_token = fields.Char( groups="base.group_system")
    url_link = fields.Char("Url Link")










