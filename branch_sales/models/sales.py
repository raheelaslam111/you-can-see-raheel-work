# -*- coding: utf-8 -*-
from odoo import models, fields, exceptions, api, _



class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_default_branch_id(self):
        return self.env['company.branches'].search([('company_id', '=', self.env.company.id),('id', '=', self.env.user.branch_id.id)], limit=1)

    branch_id = fields.Many2one('company.branches', string='Branch',default=_get_default_branch_id)

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        return res


