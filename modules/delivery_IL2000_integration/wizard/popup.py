from odoo import api, fields, models




class popupmessageshow(models.TransientModel):
    _name = 'popup.message'
    _description = 'Shipping Quote Requested'

    name = fields.Char(string='Name')
