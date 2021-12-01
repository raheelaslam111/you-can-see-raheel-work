import pdb
from xml.dom import minidom
from base64 import b64decode
from odoo.exceptions import ValidationError
from lxml import etree
from odoo.http import request
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from pytz import timezone


class NMSXmlReport(models.AbstractModel):
    _name = "report.nms_file_management.report_nms_uedf_docs"

    @api.model
    def _get_report_values(self, docids, data=None):
        uedf = self.env['stock.production.lot']
        uedf_data = uedf.search([('disposition_code', '=', 'id does not exist'), ('id', 'in', docids), ('state', '!=', 'inbound')])
        if uedf_data:
            sequence = self.env['ir.sequence'].next_by_code('Runnumbernms')
            name, date = self._get_uedf_xml_filename(sequence=sequence)
            file_name = name
            serial_type = uedf_data[0].product_id.product_tmpl_id.h_type
            product_check_list = []
            for line in uedf_data:
                boost_file = self.env['boost.file'].search([('name', '=', file_name),('udef_type', '=', 'udef_activation')])
                if not boost_file:
                    boost_file = self.env['boost.file'].create({'name': file_name,
                                                                'udef_type': 'udef_activation'})
                line.file_name = boost_file.id
                line.udfd_status = None
                if line.product_id.id not in product_check_list:
                    product_check_list.append(line.product_id.id)
            if len(product_check_list) > 1:
                raise ValidationError(
                    _('You have selected records of multiple products! Please, select records of one product.'))
            return {
                'uedf_data': uedf_data,
                'sequence': sequence,
                'serial_type': serial_type,
                'date': date,
            }
        else:
            raise ValidationError(_('Please make sure the selected records have correct criteria with respect to Disposition Code.'))

    def _get_uedf_xml_filename(self,sequence):
        current_date = datetime.now(timezone('US/Mountain'))
        holidays = self.env['cell.holidays'].search([])
        if len(holidays) >= 1:
            if current_date.date() in [h.date for h in holidays]:
                current_date += timedelta(days=1)
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

        file_name = "spdish_" + yyyy + mm + dd + "_" + sequence
        date = yyyy + '-' + mm + '-' + dd
        request.env.context = dict(self.env.context)
        request.env.context.update({
            'file_name': file_name,
        })
        self.env.context = dict(self.env.context)
        self.env.context.update({
            'file_name': file_name,
        })
        return file_name, date

    def generate_report(self, ir_report, docids, data=None):
        """
        Generate and validate XML report. Use incoming `ir_report` settings
        to setup encoding and XMl declaration for result `xml`.

        Methods:
         * `_get_rendering_context` `ir.actions.report` - get report variables.
         It will call `_get_report_values` of report's class if it's exist.
         * `render_template` of `ir.actions.report` - get report content
         * `validate_report` - check result content

        Args:
         * ir_report(`ir.actions.report`) - report definition instance in Odoo
         * docids(list) - IDs of instances for those report will be generated
         * data(dict, None) - variables for report rendering

        Returns:
         * str - result content of report
         * str - `"xml"`

        Extra Info:
         * Default encoding is `UTF-8`
        """
        # collect variable for rendering environment
        if not data:
            data = {}
        data.setdefault("report_type", "text")
        data = ir_report._get_rendering_context(docids, data)

        # render template
        result_bin = ir_report._render_template(ir_report.report_name, data)

        # prettify result content
        # normalize indents
        parsed_result_bin = minidom.parseString(result_bin)
        result = parsed_result_bin.toprettyxml(indent=" " * 4)

        # remove empty lines
        utf8 = "UTF-8"
        result = "\n".join(
            line for line in result.splitlines() if line and not line.isspace()
        ).encode(utf8)

        content = etree.tostring(
            etree.fromstring(result),
            encoding=ir_report.xml_encoding or utf8,
            xml_declaration=ir_report.xml_declaration,
            pretty_print=True,
        )

        # validate content
        xsd_schema_doc = ir_report.xsd_schema
        self.validate_report(xsd_schema_doc, content)
        # pdb.set_trace()
        return content, "xml"

    @api.model
    def validate_report(self, xsd_schema_doc, content):
        """
        Validate final report content against value of `xsd_schema` field
        ("XSD Validation Schema") of `ir.actions.report` via `etree` lib.

        Args:
         * xsd_schema_doc(byte-string) - report validation schema
         * content(str) - report content for validation

        Raises:
         * odoo.exceptions.ValidationError - Syntax of final report is wrong

        Returns:
         * bool - True
        """
        if xsd_schema_doc:
            # create validation parser
            decoded_xsd_schema_doc = b64decode(xsd_schema_doc)
            parsed_xsd_schema = etree.XML(decoded_xsd_schema_doc)
            xsd_schema = etree.XMLSchema(parsed_xsd_schema)
            parser = etree.XMLParser(schema=xsd_schema)

            try:
                # check content
                etree.fromstring(content, parser)
            except etree.XMLSyntaxError as error:
                raise ValidationError(error.msg)
        return True


class NMSASNXmlReport(models.AbstractModel):
    _name = "report.nms_file_management.report_nms_uedf_asn_docs"

    @api.model
    def _get_report_values(self, docids, data=None):
        sequence = self.env['ir.sequence'].next_by_code('Runnumberudfnms')
        factory_order_seq = self.env['ir.sequence'].next_by_code('Factoryorderseq')
        list_fact_seq = list(factory_order_seq)
        fact_seq_final = ''.join(list_fact_seq[0:4])+'-'+''.join(list_fact_seq[4:8])+'-'+''.join(list_fact_seq[8:10])
        file_name,date = self._get_uedf_nms_xml_filename(sequence=sequence)
        uedf_data = self.env['stock.move.line'].search([('id', 'in', docids)])
        # uedf_data_search = uedf_data_search.filtered(lambda b: b.fin_eligibility_date)

        # uedf_data = uedf_data_search.filtered(lambda b: b.lock_status=='0' and not (b.fin_eligibility_date>fields.date.today()))
        if not uedf_data:
            raise ValidationError(_('There is no stock move line system found!.'))

        context = dict(self.env.context)
        picking = self.env['stock.picking'].search([('id', '=', context.get('active_id'))])
        name = False
        origin = False
        if picking:
            name = picking.name
            fact_seq_final = picking.get_fo(name.split('/')[2])
            if picking.origin:
                sale_order = self.env['sale.order'].search([('name','=',picking.origin)],limit=1)
                origin = sale_order.client_order_ref

        product_check_list = []
        for line in uedf_data:
            boost_file = self.env['boost.file'].search([('name', '=', file_name),('udef_type','=','uedf_asn')])
            if not boost_file:
                boost_file = self.env['boost.file'].create({'name': file_name,
                                                            'udef_type': 'uedf_asn'})
            line.file_name = boost_file.id
            if line.lot_id.product_id.id not in product_check_list:
                # line.state='sent'

                # line.lot_id.nms_status = 'sent'
                product_check_list.append(line.lot_id.product_id.id)
        if len(product_check_list)>1:
            raise ValidationError(_('You selected records of multiple products! Select the records of same products.'))

        data_dict_lpn_carton = {}
        for line in uedf_data:
            if line.package_id.id:
                key = (line.package_id.id)
                if key in data_dict_lpn_carton:
                    # values = {
                    data_dict_lpn_carton[key].get('product_line_list').append(line),
                # }
                # data_dict[key].update(values)
                else:
                    data_dict_lpn_carton[key] = {
                        'package_id': line.package_id.id,
                        'package_name': line.package_id.name,
                        'parent_package_name': line.parent_package.name,
                        'product_line_list': [line],
                    }
        total_count = 0
        for data in data_dict_lpn_carton:
            for line in data_dict_lpn_carton[data].get('product_line_list'):
                total_count +=1


        product_id = self.env['product.product']
        if uedf_data and uedf_data[0].product_id:
            product_id += uedf_data[0].product_id
        if product_id:
            return {
                'uedf_data': data_dict_lpn_carton,
                'sequence': sequence,
                'list_fact_seq': picking.name,
                'current_date': date,
                'product_id': product_id or False,
                'origin': origin,
                'name': name,
                'total_count': total_count,
            }
        else:
            raise ValidationError(_('No product is found!.'))

    def _get_uedf_nms_xml_filename(self,sequence):
        current_date = datetime.now(timezone('US/Mountain'))
        holidays = self.env['cell.holidays'].search([])
        if len(holidays) >= 1:
            if current_date.date() in [h.date for h in holidays]:
                current_date += timedelta(days=1)
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

        file_name = "spdish_" + yyyy + mm + dd + "_" + sequence
        date = yyyy+'-' + mm+'-'+dd
        request.env.context = dict(self.env.context)
        request.env.context.update({
            'file_name': file_name,
        })
        self.env.context = dict(self.env.context)
        self.env.context.update({
            'file_name': file_name,
        })
        return file_name, date

    def generate_report(self, ir_report, docids, data=None):
        """
        Generate and validate XML report. Use incoming `ir_report` settings
        to setup encoding and XMl declaration for result `xml`.

        Methods:
         * `_get_rendering_context` `ir.actions.report` - get report variables.
         It will call `_get_report_values` of report's class if it's exist.
         * `render_template` of `ir.actions.report` - get report content
         * `validate_report` - check result content

        Args:
         * ir_report(`ir.actions.report`) - report definition instance in Odoo
         * docids(list) - IDs of instances for those report will be generated
         * data(dict, None) - variables for report rendering

        Returns:
         * str - result content of report
         * str - `"xml"`

        Extra Info:
         * Default encoding is `UTF-8`
        """
        # collect variable for rendering environment
        if not data:
            data = {}
        data.setdefault("report_type", "text")
        data = ir_report._get_rendering_context(docids, data)

        # render template
        result_bin = ir_report._render_template(ir_report.report_name, data)

        # prettify result content
        # normalize indents
        parsed_result_bin = minidom.parseString(result_bin)
        result = parsed_result_bin.toprettyxml(indent=" " * 4)

        # remove empty lines
        utf8 = "UTF-8"
        result = "\n".join(
            line for line in result.splitlines() if line and not line.isspace()
        ).encode(utf8)

        content = etree.tostring(
            etree.fromstring(result),
            encoding=ir_report.xml_encoding or utf8,
            xml_declaration=ir_report.xml_declaration,
            pretty_print=True,
        )

        # validate content
        xsd_schema_doc = ir_report.xsd_schema
        self.validate_report(xsd_schema_doc, content)
        # pdb.set_trace()
        return content, "xml"

    @api.model
    def validate_report(self, xsd_schema_doc, content):
        """
        Validate final report content against value of `xsd_schema` field
        ("XSD Validation Schema") of `ir.actions.report` via `etree` lib.

        Args:
         * xsd_schema_doc(byte-string) - report validation schema
         * content(str) - report content for validation

        Raises:
         * odoo.exceptions.ValidationError - Syntax of final report is wrong

        Returns:
         * bool - True
        """
        if xsd_schema_doc:
            # create validation parser
            decoded_xsd_schema_doc = b64decode(xsd_schema_doc)
            parsed_xsd_schema = etree.XML(decoded_xsd_schema_doc)
            xsd_schema = etree.XMLSchema(parsed_xsd_schema)
            parser = etree.XMLParser(schema=xsd_schema)

            try:
                # check content
                etree.fromstring(content, parser)
            except etree.XMLSyntaxError as error:
                raise ValidationError(error.msg)
        return True