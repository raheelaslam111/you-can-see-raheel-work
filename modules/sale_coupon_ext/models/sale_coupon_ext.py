# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import pdb

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang




class SaleOrder(models.Model):
    _inherit = "sale.order"


    def _update_existing_reward_lines(self):
        '''Update values for already applied rewards'''
        def update_line(order, lines, values):
            '''Update the lines and return them if they should be deleted'''
            lines_to_remove = self.env['sale.order.line']
            # Check commit 6bb42904a03 for next if/else
            # Remove reward line if price or qty equal to 0
            if values['product_uom_qty'] and values['price_unit']:

                print(lines.price_unit,'line.price_unit')
                print(values.get('price_unit'),'values.price_unit')
                existing_values = values
                existing_lines_price_unit = lines.price_unit
                existing_lines_order_state = lines.order_id.state

                # pdb.set_trace()
                if line.order_id.state!='sale':
                    # values.update(price_unit=lines.price_unit)
                    lines.write(values)
                previous_discount = 0.0
                for order_line in lines.order_id.order_line.filtered(lambda m: m.product_id==lines.product_id):
                    previous_discount += order_line.price_unit
                print(previous_discount,'privious_discount')
                print(lines.order_id.order_line.filtered(lambda m: m.product_id==lines.product_id),'lines.order_id.order_line.filtered(lambda m: m.product_id==lines.product_id)')
                if existing_values.get('price_unit') != existing_lines_price_unit and existing_lines_price_unit > existing_values.get('price_unit') and existing_lines_order_state=='sale':
                    new_discount = values.get('price_unit')-previous_discount
                    existing_values.update(price_unit=new_discount)
                    existing_values.update({'order_id': lines.order_id.id,'is_reward_line': True,'do_not_compute':True})
                    print('values two',existing_values)
                    sale_order_line = self.env['sale.order.line'].create(existing_values)
            else:
                if program.reward_type != 'free_shipping':
                    # Can't remove the lines directly as we might be in a recordset loop
                    lines_to_remove += lines
                else:
                    values.update(price_unit=0.0)
                    # pdb.set_trace()
                    lines.write(values)
            return lines_to_remove

        self.ensure_one()
        order = self
        applied_programs = order._get_applied_programs_with_rewards_on_current_order()
        for program in applied_programs:
            values = order._get_reward_line_values(program)
            print('VALUES',values)
            lines = order.order_line.filtered(lambda line: line.product_id == program.discount_line_product_id and line.do_not_compute==False)
            print('LINES',lines)
            if program.reward_type == 'discount' and program.discount_type == 'percentage':
                lines_to_remove = lines
                # Values is what discount lines should really be, lines is what we got in the SO at the moment
                # 1. If values & lines match, we should update the line (or delete it if no qty or price?)
                # 2. If the value is not in the lines, we should add it
                # 3. if the lines contains a tax not in value, we should remove it
                for value in values:
                    value_found = False
                    for line in lines:
                        # Case 1.
                        if not len(set(line.tax_id.mapped('id')).symmetric_difference(set([v[1] for v in value['tax_id']]))):
                            value_found = True
                            # Working on Case 3.
                            lines_to_remove -= line
                            lines_to_remove += update_line(order, line, value)
                            print('case 1')
                            continue
                    # Case 2.
                    if not value_found:
                        # pdb.set_trace()
                        order.write({'order_line': [(0, False, value)]})
                        print('case 2')
                # Case 3.
                lines_to_remove.unlink()
            else:
                update_line(order, lines, values[0]).unlink()




class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    do_not_compute = fields.Boolean(default=False)
