import pdb

from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    partner_email = fields.Char(related='partner_id.email')
    partner_phone = fields.Char(related='partner_id.phone')
    total_count_products = fields.Integer(string='Total Count', compute='_get_total_count_products')
    delivery_number = fields.Char(string='Delivery Number', compute='_get_delivery_number_for_invoice')
    our_work_done = fields.Boolean(string='Our Work is Done', default=False)

    def _get_delivery_number_for_invoice(self):
        for rec in self:
            if rec.invoice_origin:
                so = self.env['sale.order'].search([('name', '=', rec.invoice_origin)], limit=1)
                if so:
                    rec.delivery_number = so.delivery_number
                else:
                    rec.delivery_number = False
            else:
                rec.delivery_number = False

    def _get_total_count_products(self):
        for rec in self:
            total = 0
            for line in self.invoice_line_ids.filtered(lambda line: line.display_type == False and line.product_id.is_shipment_product == False and line.product_id.is_discount_product == False):
                # if line.price_subtotal > 0:
                total += line.quantity
            rec.total_count_products = total

    def get_inv_lines_sorted(self):
        lines_obj = self.env['account.move.line']
        print(self.invoice_line_ids, 'invoice_line_ids')

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


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model_create_multi
    def create(self, vals):
        res = super(AccountMoveLine, self).create(vals)
        if res.move_id.invoice_origin:
            move = self.env['account.move'].search([('id', '=', res.move_id.id)], limit=1)
            move_line = self.env['account.move.line'].search([('move_id', '=', move.id)])
            print(move_line, 'move_line')
            print(move.invoice_line_ids, 'move.invoice_line_ids')
            so = self.env['sale.order'].search([('name', '=', move.invoice_origin)], limit=1)
            if so and move.our_work_done == False:
                if len(so.invoice_ids) > 1:
                    delivery_amount = 0
                    for invoice in so.invoice_ids.filtered(lambda c: c.id != move.id and c.state != 'cancel'):
                        shipment_product_line = invoice.invoice_line_ids.filtered(
                            lambda c: c.product_id.is_shipment_product == True)

                        if len(shipment_product_line) > 0:
                            delivery_amount += shipment_product_line[0].price_unit

                    if any(move.invoice_line_ids.filtered(lambda c: c.product_id.is_shipment_product == True)):
                        delivery_product_line = move.invoice_line_ids.filtered(
                            lambda c: c.product_id.is_shipment_product == True)

                        result = delivery_product_line[0].price_unit - delivery_amount
                        debit_debit = 0
                        credit_credit = 0
                        for r in res:

                            if r.exclude_from_invoice_tab == False:
                                credit_credit += r.price_unit

                            if delivery_product_line[0].id == r.id:
                                move_line = self.env['account.move.line'].search([('id', '=', r.id)], limit=1)

                                move_line.sudo().with_context(check_move_validity=False).write({'price_unit': result,
                                                                                                'credit': result,
                                                                                                'amount_currency': 0 - result,
                                                                                                })

                        debit_line = self.env['account.move.line'].search([('id', 'in', res.mapped('id')), ('exclude_from_invoice_tab', '=', True)],
                                                                          limit=1)
                        debit_line_debit = debit_line.debit - delivery_amount
                        debit_line.sudo().with_context(check_move_validity=False).write({'price_unit': 0 - debit_line_debit,
                                                                                         'debit': debit_line_debit,
                                                                                         'amount_currency': debit_line_debit,
                                                                                         })
                move.our_work_done = True  # pdb.set_trace()

        return res
