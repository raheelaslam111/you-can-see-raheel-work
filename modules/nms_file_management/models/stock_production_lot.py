# -*- coding: utf-8 -*-
import pdb

from odoo import models, fields, api, _
import base64
from pytz import timezone
import tempfile
from datetime import timedelta
from datetime import datetime
from odoo.exceptions import ValidationError


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    disposition_code = fields.Selection(selection=[
        ('0', 'Acceptable'),
        ('1', 'Lost or Stolen (Unacceptable)'),
        ('2', 'Fraud (Unacceptable)'),
        ('3', 'Unprovisionable (Unacceptable))'),
        ('id does not exist', 'Requires an Activation Only UEDF')
    ], string='Disposition Code', tracking=True, )
    activation_status = fields.Selection(selection=[
        ('Y', 'Yes'),
        ('N', 'No')
    ], string='Activation Status', tracking=True)
    activation_date = fields.Date(string="Activation Date", tracking=True)
    deactivation_date = fields.Date(string="De-activation Date", tracking=True)
    lock_status = fields.Selection(selection=[
        ('0', 'Locked'),
        ('1', 'Unlocked'),
        ('2', 'Unlocked'),
        ('3', 'Unlocked'),
    ], string='Lock Status', tracking=True)
    fin_eligibility_date = fields.Date(string="Financial Eligibility Date", tracking=True)
    phone_owner = fields.Many2one('res.partner', string="Customer", ondelete='set null', tracking=True)
    valid_tac = fields.Char(string="Valid TAC", tracking=True)
    sku = fields.Char(string="SKU", tracking=True)
    file_name = fields.Many2one(
        comodel_name='boost.file',
        string='UDEF File',
        required=False)

    def action_import_nms(self):
        return {
            'name': _('Import NMS File'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'nms.file.import',
            'res_id': False,
            'target': 'new',
        }

    @api.model
    def multi_reports_Activation_through_action(self):
        nms_bounce = self.env['stock.production.lot'].browse(self._context.get('active_ids', [])).mapped('id')
        uedf_data_search = self.env['stock.production.lot'].search(
            [('id', 'in', nms_bounce), ('disposition_code', '=', 'id does not exist'),
             ('state', '=', 'received')])

        uedf_data = uedf_data_search
        if not uedf_data:
            raise ValidationError(_('UEDF cannot be done for some of the IMEIs since they are not in the state that '
                                    'required UEDF Activation.'))
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
        all_reports = self.env['udf.activation.report.multi']
        for data in data_dict:
            # bbb = self.env.ref('nms_file_management.uedf_xml_report').report_action(None, data=None)

            report = self.env["ir.actions.report"]._get_report_from_name('nms_file_management.report_nms_uedf_docs')

            context = dict(self.env.context)
            output_content = \
                report.with_context(context)._render_qweb_xml(data_dict[data].get('product_list'), data=context)[0]
            final_file = base64.b64encode(output_content)
            file_name = None
            if 'file_name' in self.env.context:
                file_name = "%s.xml" % (self.env.context['file_name'])

            report = self.env['udf.activation.report.multi'].create({'downloadable_attachment': final_file,
                                                                     'name': file_name})
            all_reports += report

        final_report = self.env['activation.report.multi'].create({'attachment_ids': [(6, 0, all_reports.ids)],
                                                                   })

        res = {
            'name': _('Download udf asn file multi'),
            'res_model': 'activation.report.multi',
            'view_mode': 'form',
            # 'context': {
            #     'default_downloadable_attachment': final_file,
            # },
            'res_id': final_report.id,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
        return res

    @api.model
    def export_nms(self):
        nms_bounce = self.env['stock.production.lot'].browse(self._context.get('active_ids', []))
        nms_imei_list = []
        for nms in nms_bounce:
            lot = self.env['stock.production.lot'].search([('imei', '=', nms.imei), ('nms_status', '=', 'ready')],
                                                          limit=1)
            if lot:
                # if nms.imei ==nms.lot_id.imei:
                #     nms_imei_list.append(nms.imei)
                nms_imei_list.append(nms.imei)

        file = tempfile.NamedTemporaryFile(suffix='.txt')
        file_open = open(file.name, 'w')

        iterator = len(nms_imei_list)
        for n in nms_imei_list:
            iterator -= 1
            if iterator == 0:
                file_open.write(str(n))
            else:
                file_open.write(str(n) + '\n')

        file_open.close()
        with open(file.name, 'rb') as pdf_document:
            output_content = pdf_document.read()

        pdf_document.close()

        final_file = base64.b64encode(output_content)

        # for filename
        sequence = self.env['ir.sequence'].next_by_code('Nmsboundattachment')
        us_mountain = timezone('US/Mountain')
        # current_date = fields.datetime.today()
        user_timezone = self.env.user.tz
        if not user_timezone:
            user_timezone = us_mountain
        else:
            user_timezone = timezone(user_timezone)
        current_date = datetime.now(user_timezone)

        if current_date.hour >= 17:
            current_date += timedelta(days=1)
        if current_date.weekday() == 5:
            current_date += timedelta(days=2)
        if current_date.weekday() == 6:
            current_date += timedelta(days=1)
        yyyy = str(current_date.year)
        mm = str(current_date.month)
        if int(mm) <= 9:
            mm = '0' + mm
        dd = str(current_date.day)
        if int(dd) <= 9:
            dd = '0' + dd
        us_mountain = timezone('US/Mountain')
        file_name = "nms_bounce_dish_to_tmo_" + sequence + "_" + str(len(nms_imei_list)) + "_" + yyyy + mm + dd + '.txt'
        report = self.env['nms.bounce.attachment.download'].create({'downloadable_attachment': final_file,
                                                                    'name': file_name})
        for imei in nms_imei_list:
            nms_record = self.env['stock.production.lot'].search([('imei', '=', imei)])
            if nms_record:
                nms_record.nms_status = 'sent'
        if nms_imei_list:
            return {
                'name': _('Download nms bounce file'),
                'res_model': 'nms.bounce.attachment.download',
                'view_mode': 'form',
                'context': {
                    'default_downloadable_attachment': final_file,
                },
                'res_id': report.id,
                'target': 'new',
                'type': 'ir.actions.act_window',
            }
        else:
            raise ValidationError("NMS has already been sent or received")
