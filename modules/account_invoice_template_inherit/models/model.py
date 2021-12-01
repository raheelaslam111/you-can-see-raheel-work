import pdb

from odoo import _, api, fields, models



class AccountMove(models.Model):
    _inherit = "account.move"

    partner_email = fields.Char(related='partner_id.email')
    partner_phone = fields.Char(related='partner_id.phone')

    def get_inv_lines_sorted(self):
        lines_obj = self.env['account.move.line']
        print(self.invoice_line_ids,'invoice_line_ids')

        # if lines have gift section
        section_line = self.invoice_line_ids.filtered(lambda line: line.display_type == 'line_section')
        if section_line:
            lines_price_not_zero = self.invoice_line_ids.filtered(
                lambda line: line.display_type != 'line_section' and line.price_unit != 0)
            if lines_price_not_zero:

                # sorted_lines_not_zero = lines_price_not_zero.sorted(key=lambda item: (int(item.product_id.name.partition(' ')[0]) if item[0].isdigit() else float('inf')))
                # sorted_lines_not_zero = lines_price_not_zero.sorted(key=lambda l: (l.product_id.name) if not int(l.product_id.name).isdigit() else float('inf'))
                sorted_lines_not_zero = lines_price_not_zero.sorted(key=lambda l: (l.product_id.name.lower()))
                for r in sorted_lines_not_zero:
                    lines_obj += r
            section_line = self.invoice_line_ids.filtered(lambda line: line.display_type == 'line_section')
            if section_line:
                for r in section_line:
                    lines_obj += r
            lines_price_zero = self.invoice_line_ids.filtered(
                lambda line: line.display_type != 'line_section' and line.price_unit < 1)
            if lines_price_zero:
                sorted_lines_price_zero = lines_price_zero.sorted(key=lambda l: (l.product_id.name.lower()))
                for r in sorted_lines_price_zero:
                    lines_obj += r


            print(lines_obj, 'lines_obj')
            return lines_obj
        else:
            return self.invoice_line_ids.sorted(key=lambda l: (l.product_id.name))

