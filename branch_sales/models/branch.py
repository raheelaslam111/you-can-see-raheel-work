# -*- coding: utf-8 -*-
from odoo import models, fields, exceptions, api, _



class ResCompany(models.Model):

    _inherit = "res.company"

    branch_ids = fields.One2many('company.branches','company_id',string='Branches')



class CompanyBranches(models.Model):
    _name = "company.branches"
    _description="Company Branches"

    name = fields.Char(string='Branch Name')
    company_id = fields.Many2one('res.company',string='Company')
    country_id = fields.Many2one('res.country', string="Country")
    city = fields.Char(string="City")
    street = fields.Char("Street")
    street2 = fields.Char("Street2")
    zip = fields.Char("Zip")
    state_id = fields.Many2one('res.country.state', string="State")
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    website = fields.Char("Website")