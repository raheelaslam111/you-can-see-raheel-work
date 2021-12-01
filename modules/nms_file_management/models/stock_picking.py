# -*- coding: utf-8 -*-
import pdb

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def multi_reports_ASN_through_action(self):
        picking = self.env['stock.picking'].search([('id', '=', self.env.context['active_id'])])

        uedf_data = self.env['stock.move.line']
        if picking.picking_type_id.code == 'outgoing':
            for line in picking.move_line_ids_without_package:
                # nms_bounce = self.env['stock.production.lot'].search([('id', '=', line.lot_id.id)])
                # if line.lot_id.disposition_code=='0' and line.lot_id.fin_eligibility_date:
                    # if line.lot_id.fin_eligibility_date<fields.date.today() and line.lot_id.lock_status=='0':
                if line.lot_id:
                    if line.lot_id.disposition_code=='0' and line.lot_id.lock_status in ['1','2','3']:
                        uedf_data += line
                        pdb.set_trace()
                    elif line.lot_id.fin_eligibility_date and line.lot_id.disposition_code=='0' and line.lot_id.lock_status=='0':
                        if line.lot_id.disposition_code=='0' and line.lot_id.lock_status=='0' and line.lot_id.fin_eligibility_date<fields.date.today():
                            uedf_data+=line
                            pdb.set_trace()

                    elif line.lot_id.disposition_code=='id does not exist' and line.lot_id.udfd_status=='processed':
                        uedf_data+=line
                        pdb.set_trace()
        else:
            raise ValidationError(_(
                'Please select the operation type of Delivery!.'))


        # uedf_data_search = self.env['stock.production.lot'].search([('id', 'in', nms_ids), ('disposition_code', '=', '0')])
        # uedf_data_search = uedf_data_search.filtered(lambda b: b.fin_eligibility_date)

        # uedf_data = uedf_data_search.filtered(
        #     lambda b: b.lock_status == '0' and not (b.fin_eligibility_date > fields.date.today()))
        if not uedf_data:
            raise ValidationError(_(
                'Please make sure the selected records have correct criteria with respect to Financial Eligibility and Disposition Code.'))

        data_dict = {}
        for line in uedf_data:
            if line.product_id.id:
                key = (line.product_id.id)
                if key in data_dict:
                    # values = {
                    data_dict[key].get('product_list').append(int(line.id)),
                # }
                # data_dict[key].update(values)
                else:
                    data_dict[key] = {
                        'product_id': line.product_id.id,
                        'product_list': [int(line.id)],
                    }
        all_reports = self.env['udf.asn.report.multi']
        for data in data_dict:
            bbb = self.env.ref('nms_file_management.uedf_xml_report_asn').report_action(None, data=None)

            report = self.env["ir.actions.report"]._get_report_from_name('nms_file_management.report_nms_uedf_asn_docs')

            context = dict(self.env.context)
            # pdb.set_trace()
            print(data_dict[data].get('product_list'))
            output_content = \
                report.with_context(context)._render_qweb_xml(data_dict[data].get('product_list'), data=context)[0]
            final_file = base64.b64encode(output_content)
            file_name = None
            if 'file_name' in self.env.context:
                file_name = "%s.xml" % (self.env.context['file_name'])
            # file_name = "nms_bounce_dish_to_tmo_" + sequence + "_" + str(len(nms_imei_list)) + "_" + yyyy + mm + dd + '.txt'
            report = self.env['udf.asn.report.multi'].create({'downloadable_attachment': final_file,
                                                              'name': file_name})
            all_reports += report

        final_report = self.env['udf.asn.report.multi.wizard'].create({'attachment_ids': [(6, 0, all_reports.ids)],
                                                                       })

        res = {
            'name': _('Download udf asn file multi'),
            'res_model': 'udf.asn.report.multi.wizard',
            'view_mode': 'form',
            # 'context': {
            #     'default_downloadable_attachment': final_file,
            # },
            'res_id': final_report.id,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
        return res



class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'


    udfd_status = fields.Selection(
        string='UEDF Status',
        selection=[
                   ('requested', 'ASN Requested Before'),
                   ('processed', 'UEDF Processed'),
                   ('rejected', 'UEDF Rejected')
                   ],
        required=False,compute='compute_udfd_status')
    file_name = fields.Many2one(
        comodel_name='boost.file',
        string='UDEF File',
        required=False)
    uedf_date = fields.Datetime(related='file_name.processed_date',string='UEDF Datetime')

    def compute_udfd_status(self):
        for rec in self:
            if rec.file_name.processed_status == "processed" and rec.file_name.is_processed==True:
                rec.udfd_status = 'processed'
            elif rec.file_name.processed_status == "rejected" and rec.file_name.is_processed==True:
                rec.udfd_status = 'rejected'
            else:
                rec.udfd_status = 'requested'
