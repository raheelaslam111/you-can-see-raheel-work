import pdb
import json
from odoo import _, api, fields, models
import requests
import base64


class AvIqAPISettings(models.Model):
    _name = 'api.settings'
    _description = 'API Settings'

    name = fields.Char(string='API Name')
    user_name = fields.Char(string='User Name')
    password = fields.Char(string='Password')
    clientid = fields.Char(string="Client Id", required=True)
    uid = fields.Char(string='UID')
    
