# -*- coding: utf-8 -*-
import pdb

from odoo import models, fields, api, _
import io
import base64
import tempfile
import os
from odoo.exceptions import UserError, ValidationError
import csv



class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    is_send_to_dish = fields.Boolean('Send to dish')



class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def get_fo(self, num):
        fo = [int(d) for d in num]
        fo = f"0000-0{fo[0]}-{fo[1]}{fo[2]}-{fo[3]}{fo[4]}"
        return fo


    @api.model
    def export_nms_csv(self):
        # data = self.env['stock.move.line']
        # moves = self.env['stock.picking'].search([('id', 'in', self._context.get('active_ids'))])
        # for rec in moves:
        #     for line in rec.move_line_ids_without_package:
        #         data += line

        file = tempfile.NamedTemporaryFile(suffix='.csv')

        file_open = open(file.name, 'w')
        # with os.fdopen(file, "w", encoding='utf8', errors='surrogateescape',newline='') as f:
        writer = csv.writer(file_open)

        try:
            writer.writerow(['ARZM','PO','FO','Line','Model','Product Description','Qty',
                             'Cartons','Date Shipped','City','State','Carrier','Tracking/Pro Number','Supplier Name',
                             'Supplier Address','Supplier City','Supplier State','Pallets','Weight','UEDF File Name',
                             'UEDF Date Time'])
            b = ['ARZM', 'PO', 'FO', 'Line', 'Model', 'Product Description', 'Qty',
                 'Cartons', 'Date Shipped', 'City', 'State', 'Carrier', 'Tracking/Pro Number', 'Supplier Name',
                 'Supplier AddressSupplier City', 'Supplier City', 'Supplier State', 'Pallets', 'Weight',
                 'UEDF File Name',
                 'UEDF Date Time']
            print(b)

            moves = self.env['stock.picking'].search([('id', 'in', self._context.get('active_ids'))])
            data_dict = {}
            for move in moves:
                for line in move.move_line_ids_without_package:
                    if line.parent_package.id:
                        key = (line.parent_package.id)
                        if key in data_dict:
                            data_dict[key].get('stock_move_lines').append(line),
                            values = {
                                'total_qty_done': data_dict[key].get('total_qty_done') + line.qty_done,
                            }
                            data_dict[key].update(values)
                        else:
                            data_dict[key] = {
                                'parent_package': line.parent_package,
                                'total_qty_done': line.qty_done,
                                'picking_id': line.picking_id,
                                'file_name': line.file_name,
                                'default_code': line.product_id.default_code,
                                'product_id': line.product_id,
                                'product_description': line.product_id.name,
                                'stock_move_lines': [line],
                            }



            for row in data_dict:
                data_list = []
                data_list.append('0158-1001' or "")
                so = self.env['sale.order'].search([('name','=',data_dict[row].get('picking_id').origin)],limit=1)
                if so:
                    data_list.append(so.client_order_ref or "")
                else:
                    data_list.append("")
                data_list.append(data_dict[row].get('picking_id').name or "")
                data_list.append('')
                data_list.append(data_dict[row].get('default_code') or "")
                data_list.append(data_dict[row].get('product_id').name or "")
                data_list.append(data_dict[row].get('total_qty_done') or "")


                # child_packages_line_lenth = 0
                # if row.parent_package and row.parent_package.child_packages:
                #     for child in row.parent_package.child_packages:
                #         child_packages_line_lenth += len(child.quant_ids)

                parent_child_packages_lenth = 0
                if data_dict[row].get('parent_package') and data_dict[row].get('parent_package').child_packages:
                    parent_child_packages_lenth = len(data_dict[row].get('parent_package').child_packages)


                data_list.append(str(parent_child_packages_lenth) or "")
                data_list.append(str(data_dict[row].get('picking_id').scheduled_date) or "")
                data_list.append(data_dict[row].get('picking_id').partner_id.city or "")
                data_list.append(data_dict[row].get('picking_id').partner_id.state_id.name or "")
                data_list.append(data_dict[row].get('picking_id').carrier_id.name or "")
                data_list.append(data_dict[row].get('picking_id').carrier_tracking_ref or "")
                data_list.append('Cellpoint')
                data_list.append(data_dict[row].get('picking_id').company_id.street or "")
                data_list.append(data_dict[row].get('picking_id').company_id.city or "")
                data_list.append(data_dict[row].get('picking_id').company_id.state_id.name or "")
                data_list.append("1")
                data_list.append(data_dict[row].get('picking_id').weight or "")
                if data_dict[row].get('file_name'):
                    data_list.append(data_dict[row].get('file_name').name+'.xml' or "")
                else:
                    data_list.append("")
                if data_dict[row].get('file_name').processed_date:
                    data_list.append(data_dict[row].get('file_name').processed_date.date() or "")
                else:
                    data_list.append("")


                writer.writerow(data_list)

                for rec in data_dict[row].get('stock_move_lines'):
                    rec.is_send_to_dish = True
                    rec.lot_id.state = 'shipped'
        except Exception as e:
            print('Error in writing row:', e)
            raise ValidationError(_(
                '(Error in writing row: %s)', e))
        file_open.close()

        with open(file.name, 'rb') as csv_document:
            output_content = csv_document.read()
        csv_document.close()


        final_file = base64.b64encode(output_content)
        report = self.env['nms.csv.attachment.download'].create({'downloadable_attachment': final_file,
                                                                    'name': 'ASN-1.csv'})
        return {
            'name': _('Download nms csv file'),
            'res_model': 'nms.csv.attachment.download',
            'view_mode': 'form',
            'context': {
                'default_downloadable_attachment': final_file,
            },
            'res_id': report.id,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

class nms_csv_attachment_download(models.TransientModel):
    _name = 'nms.csv.attachment.download'
    _description = 'nms.csv.attachment.download'

    name = fields.Char(string='Name', default='ASN-1.csv')
    downloadable_attachment = fields.Binary(string='Attachment', readonly=True)

    # def _assign_lot_serial_number(self):
    #     lot_id = self.env['stock.production.lot'].search([('imei', '=', self.imei)])
    #     if lot_id:
    #         self.lot_id = lot_id
    #     else:
    #         return True
