# -*- coding: utf-8 -*-
from odoo import models, fields, exceptions, api, _



class Stock(models.Model):
    _inherit = 'stock.warehouse'

    branch_id = fields.Many2one('company.branches',string='Branch',required=True)