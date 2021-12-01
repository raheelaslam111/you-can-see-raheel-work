# -*- coding: utf-8 -*-
import tempfile
import binascii
import xlrd
from datetime import date, datetime
from odoo import models, fields, exceptions, api, _
from odoo.exceptions import ValidationError


import logging

_logger = logging.getLogger(__name__)

try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class NMSFileImport(models.TransientModel):
    _name = "nms.file.import"
    _description = 'NNMS Import Utility'

    file = fields.Binary('File')

    def nms_import_file(self):
        fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.file))
        fp.seek(0)
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)

        header = sheet.row_values(0)  # header contain all column values from sheet header
        if len(header) < 10:
            raise ValidationError('NMS import file must have 10 columns atleast.')

        self.coloum_header_match(h0=header[0],
                                 h1=header[1],
                                 h2=header[2],
                                 h3=header[3],
                                 h4=header[4],
                                 h5=header[5],
                                 h6=header[6],
                                 h7=header[7],
                                 h8=header[8],
                                 h9=header[9]
                                 )
        row_count = 0
        for row_num in range(1, sheet.nrows):
            row = sheet.row_values(row_num)
            row_count +=1

            cell_activation_date = sheet.cell(row_num, 4)
            cell_deactivation_date = sheet.cell(row_num, 5)
            cell_fin_eligibility_date = sheet.cell(row_num, 7)
            actual_activation_date = actual_deactivation_date = actual_fin_eligibility_date = False

            if cell_activation_date.ctype == 3:  # Date
                date_value_4 = xlrd.xldate_as_tuple(cell_activation_date.value, workbook.datemode)
                actual_activation_date = date(*date_value_4[:3]).strftime('%Y-%m-%d')

            if cell_deactivation_date.ctype == 3:  # Date
                date_value_5 = xlrd.xldate_as_tuple(cell_deactivation_date.value, workbook.datemode)
                actual_deactivation_date = date(*date_value_5[:3]).strftime('%Y-%m-%d')

            if cell_fin_eligibility_date.ctype == 3:  # Date
                date_value_7 = xlrd.xldate_as_tuple(cell_fin_eligibility_date.value, workbook.datemode)
                actual_fin_eligibility_date = date(*date_value_7[:3]).strftime('%Y-%m-%d')

            esn_imei = esn_disposition_code = esn_activation_status = esn_activation_date = esn_deactivation_date = esn_lock_status = esn_fin_eligibility_date = esn_phone_owner = esn_valid_tac =False
            if row[0]:
                sheet_esn = int(row[0]) if type(row[0]) == int or type(row[0]) == float else None
                if isinstance(sheet_esn, int) and len(str(sheet_esn)) == 15:
                    esn_imei = str(int(row[0]))
                else:
                    raise ValidationError('esn {} should only contain 15 digits on row {}'.format(str(row[0]),row_count))
            if row[2] != '':
                if type(row[2]) == str:
                    if row[2].lower() == 'id does not exist':
                        esn_disposition_code = row[2].lower()
                    else:
                        raise ValidationError(_('Value not in correct format " %s " in row "%s"' % (row[2], row_count)))
                else:
                    esn_disposition_code = str(int(row[2]))
            if row[3]:
                if str(row[3].upper()) in ['Y', 'N']:
                    esn_activation_status = str(row[3].upper())
                else:
                    raise ValidationError(_('Value not in correct format " %s " in row "%s"' % (row[3], row_num)))
            if actual_activation_date:
                esn_activation_date = datetime.fromisoformat(actual_activation_date).date()
            if actual_deactivation_date:
                esn_deactivation_date = datetime.fromisoformat(actual_deactivation_date).date()
            if row[6] != '':
                sheet_lock_status = int(row[6]) if type(row[6]) == int or type(row[6]) == float else None
                if isinstance(sheet_lock_status, int):
                    esn_lock_status = str(int(row[6]))
                else:
                    raise ValidationError('lock_status {} should contain only numbers on row {}'.format(str(row[6]), row_count))
            if actual_fin_eligibility_date:
                esn_fin_eligibility_date = datetime.fromisoformat(actual_fin_eligibility_date).date()
            if row[8]:
                esn_phone_owner = str(row[8])
            if row[9]:
                esn_valid_tac = str(row[9])
            lot_id = self.env['stock.production.lot'].search([('imei', '=', esn_imei)])
            customer = self.env['res.partner'].search([('name', '=', esn_phone_owner)], limit=1)
            if esn_imei and esn_imei == lot_id.imei:
                lot_id.write({
                    'disposition_code': esn_disposition_code,
                    'activation_status': esn_activation_status,
                    'activation_date': esn_activation_date,
                    'deactivation_date':esn_deactivation_date,
                    'lock_status': esn_lock_status,
                    'fin_eligibility_date': esn_fin_eligibility_date,
                    'phone_owner': customer,
                    'valid_tac': esn_valid_tac,
                    'nms_status': 'received'
                })

        return {'type': 'ir.actions.client', 'tag': 'reload', }

        # this function is used to check all coloumn headers and match his names.

    def coloum_header_match(self, h0, h1, h2, h3, h4, h5, h6, h7, h8, h9):

        if not h0.casefold() == str('esn').casefold():
            raise ValidationError('Column header {} does not match the format \n First column should contain "esn"'.format(h0))

        elif not h1.casefold() == str('model_number').casefold():
            raise ValidationError('Column header "{}" does not match the format \n Second column should contain "model_number"'.format(h1))

        elif not h2.casefold() == str('disposition_code').casefold():
            raise ValidationError('Column header "{}" does not match the format \n Third column should contain "disposition_code"'.format(h2))

        elif not h3.casefold() == str('activation_status').casefold():
            raise ValidationError('Column header "{}" does not match the format \n Fourth column should contain "activation_status"'.format(h3))

        elif not h4.casefold() == str('activation_date').casefold():
            raise ValidationError('Column header "{}" does not match the format \n Fifth column should contain "activation_date"'.format(h4))

        elif not h5.casefold() == str('deactivation_date').casefold():
            raise ValidationError('Column header "{}" does not match the format \n Sixth column should contain "deactivation_date"'.format(h5))

        elif not h6.casefold() == str('lock_status').casefold():
            raise ValidationError('Column header "{}" does not match the format \n Column seven should contain "lock_status"'.format(h6))

        elif not h7.casefold() == str('fin_eligibility_date').casefold():
            raise ValidationError('Column header "{}" does not match the format \n Column eight should contain "fin_eligibility_date"'.format(h7))

        elif not h8.casefold() == str('phone_owner').casefold():
            raise ValidationError('Column header "{}" does not match the format \n Column nine should contain "phone_owner"'.format(h8))

        elif not h9.casefold() == str('Valid_TAC').casefold():
            raise ValidationError('Column header "{}" does not match the format \n Column nine should contain "Valid_TAC"'.format(h9))