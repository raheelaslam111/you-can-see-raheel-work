# -*- coding: utf-8 -*-
import pdb

from odoo import models, fields, exceptions, api, _



class Users(models.Model):
    _inherit = "res.users"

    branch_id = fields.Many2one('company.branches',string='Branch', domain = " [('company_id', '=', company_id)]")


    def _get_default_warehouse_id(self):
        if self.property_warehouse_id:
            return self.property_warehouse_id

        # !!! Any change to the following search domain should probably
        # be also applied in sale_stock/models/sale_order.py/_init_column.
        return self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id),('branch_id', '=', self.env.user.branch_id.id)], limit=1)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    branch_id = fields.Many2one('company.branches',related='user_id.branch_id',string='Branch',
    	help='company branch of the employee selected on related user',store=True)