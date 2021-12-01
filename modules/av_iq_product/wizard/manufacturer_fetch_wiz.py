import pdb

from odoo import models, fields, api
import datetime


class ReviewFetchWiz(models.TransientModel):
    _name = 'manufacturer.fetch.wiz'
    _description = 'manufacturer.fetch.wiz'

    name = fields.Char(string="name")
    select_source = fields.Many2one(
        comodel_name='manufacturer.main',
        string='Select Source',
        required=False)

    def fetch_reviews(self):
        self.select_source.fetch_reviews()
