import pdb
import json
from odoo import _, api, fields, models
import requests
import logging
from odoo.exceptions import UserError, ValidationError


class categories_main(models.Model):
    _name = 'categories.main'
    _description = 'categories_main'
    _rec_name = 'user_name'

    api_id = fields.Many2one('api.settings', string='API')
    user_name = fields.Char(string='User Name', related="api_id.user_name", store=True)
    password = fields.Char(string='Password', related="api_id.password", store=True)
    clientid = fields.Char(string="Client Id", related="api_id.clientid", store=True)
    uid = fields.Char(string='UID', related="api_id.uid", store=True)

    url = fields.Char(String="URL", required=True)
    categories_lines_ids = fields.One2many('categories.lines','categories_main_id',string='Categories Lines',ondelete='cascade')

    def fetch_categories(self):

        if self.user_name and self.password:
            url = str(self.url)+"?clientid="+str(self.clientid)+"&uid="+str(self.uid)
            auth = (str(self.user_name), str(self.password))
            headers = {'Content-Type': 'application/json'}

            response = requests.request("GET", url=url, headers=headers,auth=auth)

            if response.status_code != 200:
                raise ValidationError(_('Connection is down/Not-Established while getting Categories.'))

            y = json.loads(response.text)


            category_list = []
            for x in y:
                categories = self.env['categories.lines'].search([('category_id', '=', x['CATEGORY_ID']), ('categories_main_id', '=', self.id)])

                if categories:
                    values = {
                        'category': x['CATEGORY_DISPLAY_NAME'],
                        'product_count': x['PRODUCTCOUNT'],
                    }
                    categories.write(values)
                else:
                    values = {
                        'category_id': x['CATEGORY_ID'],
                        'category': x['CATEGORY_DISPLAY_NAME'],
                        'product_count': x['PRODUCTCOUNT'],
                        'categories_main_id': self.id
                    }
                    self.env['categories.lines'].create(values)


class Categorylines(models.Model):
    _name = 'categories.lines'
    _description = 'Category lines'
    _rec_name = 'category'

    category_id = fields.Integer(string="CATEGORY_ID")
    category = fields.Char(string="CATEGORY DISPLAY NAME")
    product_count = fields.Char(string="PRODUCT COUNT")
    categories_main_id = fields.Many2one('categories.main',string='categories_main_id')
    api_id = fields.Many2one('api.settings', string='API', related='categories_main_id.api_id', store=True)
