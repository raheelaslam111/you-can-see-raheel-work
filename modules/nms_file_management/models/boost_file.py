from odoo import models, fields, api, _
import io
import base64
import tempfile
from datetime import datetime
from datetime import timedelta


class BoostFile(models.Model):
    _name = 'boost.file'
    name = fields.Char(
        string='UDEF File',
        required=False)
    nms_file_imei = fields.One2many(comodel_name='stock.production.lot', inverse_name='file_name', string='NMS file',
                                    required=False)
    sku = fields.Char(string="SKU", required=False, )
    is_processed = fields.Boolean(string="Is Processed", )
    processed_date = fields.Datetime(string="Processed Date", required=False, )
    processed_status = fields.Selection(string="Status",
                                        selection=[('processed', 'PROCESSED'), ('rejected', 'REJECTED'), ],
                                        required=False, )
    udef_type = fields.Selection(string="UEDF File Type",
                                 selection=[('uedf_asn', ' UEDF ASN'), ('udef_activation', 'UEDF Activation '), ],
                                 required=False, )

    @api.onchange('processed_status')
    def onchange_method(self):
        if self.processed_status == "processed" or self.processed_status== 'reject':
            for record in self.nms_file_imei:
                lot = self.env['stock.production.lot'].search([('id','=',record.ids[0])])
                if lot:
                    lot.udfd_status = self.processed_status
