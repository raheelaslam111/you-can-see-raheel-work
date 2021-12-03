# -*- coding: utf-8 -*-
from odoo import models, fields, exceptions, api, _



class account_journal(models.Model):
    _inherit = "account.journal"

    branch_id = fields.Many2one('company.branches',string='Branch')