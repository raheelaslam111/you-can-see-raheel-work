import pdb
import json
from odoo import _, api, fields, models
import requests
from odoo.exceptions import UserError, ValidationError

class manufacturer_main(models.Model):
    _name = 'manufacturer.main'
    _description = 'manufacturer_main'
    _rec_name = 'user_name'

    api_id = fields.Many2one('api.settings', string='API')
    user_name = fields.Char(string='User Name', related="api_id.user_name", store=True)
    password = fields.Char(string='Password', related="api_id.password", store=True)
    clientid = fields.Char(string="Client Id", related="api_id.clientid", store=True)
    uid = fields.Char(string='UID', related="api_id.uid", store=True)
    url = fields.Char(String="URL", required=True)
    manufacturer_lines_ids = fields.One2many('manufacturer.lines','manufacturer_main_id',string='Manufacturer Lines',ondelete='cascade')

    def fetch_manufacturer(self):
        if self.user_name and self.password:
            url = str(self.url)+"?clientid="+str(self.clientid)+"&uid="+str(self.uid)
            auth = (str(self.user_name), str(self.password))
            headers = {'Content-Type': 'application/json'}

            response = requests.request("GET", url=url, headers=headers,auth=auth)
            if response.status_code != 200:
                raise ValidationError(_('Connection is down/Not-Established while getting manufacturers.'))

            y = json.loads(response.text)

            for x in y:
                manufacturers = self.env['manufacturer.lines'].search([('manufacturer_id', '=', x['MANUFACTURER_ID']),('manufacturer_main_id', '=', self.id)])
                if manufacturers:
                    values = {
                        'manufacturer': x['MANUFACTURER'],
                        'product_count': x['PRODUCTCOUNT'],
                    }
                    manufacturers.write(values)
                else:
                    values = {
                        'manufacturer_id' : x['MANUFACTURER_ID'],
                        'manufacturer': x['MANUFACTURER'],
                        'product_count': x['PRODUCTCOUNT'],
                        'manufacturer_main_id': self.id
                    }
                    manufacturers = self.env['manufacturer.lines'].create(values)


class ManufacturerLines(models.Model):
    _name = 'manufacturer.lines'
    _description = 'manufacturer.lines'
    _rec_name = 'manufacturer'

    manufacturer_id = fields.Integer(string="MANUFACTURER_ID")
    manufacturer = fields.Char(string="MANUFACTURER")
    product_count = fields.Char(string="PRODUCT COUNT")
    manufacturer_main_id = fields.Many2one('manufacturer.main',string='manufacturer_main_id')
    api_id = fields.Many2one('api.settings', string='API', related='manufacturer_main_id.api_id', store=True)
