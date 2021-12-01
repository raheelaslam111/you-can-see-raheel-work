# -*- coding: utf-8 -*-
import pdb

from odoo import models, api, fields,_
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
from datetime import date, timedelta


class MRPProduction(models.Model):
    _inherit = 'mrp.production'

    packaging_date = fields.Date(string="Packaging Date")

    latest_expected_availability = fields.Date(compute='get_expected_availability_date')
    expected_av_noav = fields.Char(compute='get_expected_availability_date', string='Expected availability/Unavailable')

    # def _compute_state(self):
    #     previous_state = self.state
    #     res = super(MRPProduction, self)._compute_state()
    #     if previous_state != self.state and self.state == "done":
    #         if self.sale_order_id:
    #             template = self.env['mail.template'].search(
    #                 [('model', '=', 'mrp.production'), ('name', '=', 'Notify Sales Person When MO Done..')], limit=1)
    #             template.with_context(user_id=self.sale_order_id.team_id.user_id, ).send_mail(self.id, force_send=True)
    #             for member in self.sale_order_id.team_id.member_ids:
    #                     # template.partner_to = self.sale_order_id.team_id.member_ids.ids
    #                     template.with_context(user_id=member,).send_mail(self.id, force_send=True)
    #     return res

    # def write(self, vals):
    #     previous_state = self.state
    #     res = super(MRPProduction, self).create(vals)
    #     pdb.set_trace()
    #     if previous_state != self.state and self.state == "done":
    #         if self.sale_order_id:
    #             template = self.env['mail.template'].search(
    #                 [('model', '=', 'mrp.production'), ('name', '=', 'Notify Sales Person When MO Done..')], limit=1)
    #             template.with_context(user_id=self.sale_order_id.team_id.user_id, ).send_mail(self.id, force_send=True)
    #             for member in self.sale_order_id.team_id.member_ids:
    #                     # template.partner_to = self.sale_order_id.team_id.member_ids.ids
    #                     template.with_context(user_id=member,).send_mail(self.id, force_send=True)
    #     return res

    def get_expected_availability_date(self):
        for rec in self:
            if rec.reservation_state == 'confirmed':
                expected_dates = rec.move_raw_ids.filtered(lambda
                                                               m: m.forecast_availability >= m.product_qty and m.forecast_expected_date and m.reserved_availability == 0).sorted(
                    lambda s: s.forecast_expected_date, reverse=True)
                # expected_dates = expected_dates_initial.filtered(lambda m: m.forecast_expected_date > m.date_deadline).mapped('forecast_expected_date')
                # and m.reserved_availability > 0
                # and m.forecast_expected_date > m.date_deadline
                # expected_dates = expected_dates_initial.filtered(lambda m: m.forecast_expected_date).mapped('forecast_expected_date')
                # pdb.set_trace()
                # sorted_dat = sorted(expected_dates, reverse=True)
                # pdb.set_trace()
                # date = self.nearest(items = expected_dates)

                if expected_dates:
                    rec.latest_expected_availability = expected_dates[0].forecast_expected_date
                else:
                    rec.latest_expected_availability = False
                expected_availibility = 0
                # not_available = len(rec.move_raw_ids.filtered(lambda m: m.forecast_availability==0.00))

                not_available = rec.move_raw_ids.filtered(
                    lambda m: not (m.forecast_availability >= m.product_qty) and m.reserved_availability == 0)

                rec.expected_av_noav = str(len(expected_dates)) + '/' + str(len(not_available))
            else:
                rec.latest_expected_availability = False
                rec.expected_av_noav = False

    def change_mo_states_to_ready(self):
        for rec in self:
            if rec.reservation_state == 'assigned':
                if any(rec.move_raw_ids.filtered(lambda m: not m.forecast_availability >= m.product_qty)):
                    rec.reservation_state = 'confirmed'


    def button_mark_done(self):

        if not self.packaging_date:
            return {
                'name': _('Set Packaging Date'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mrp.packaging.date.wizard',
                'target': 'new',
            }

        return super(MRPProduction,self).button_mark_done()

    @api.onchange('origin')
    def _onchange_origin(self):
        if self.origin:
            warehouse_id = self.env['sale.order'].search([('name', '=', self.origin)]).warehouse_id.id
            picking_type_id = self.env['stock.picking.type'].search([
                ('code', '=', 'mrp_operation'),
                ('warehouse_id', '=', warehouse_id),
            ], limit=1).id
            self.picking_type_id = picking_type_id
        else:
            self.picking_type_id = self._get_default_picking_type()

    @api.model_create_multi
    def create(self, values):
        res = super(MRPProduction,self).create(values)
        for record in res:
            if record.date_planned_start:
                if record.picking_ids:
                    # Do not change the scheduled date of pickings that are already done or cancelled
                    for picking in record.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
                        picking.scheduled_date = record.date_planned_start
        return res

    def write(self, vals):
        previous_scheduled_date = self.date_planned_start
        res = super(MRPProduction, self).write(vals)
        if self.date_planned_start != previous_scheduled_date:
            if self.picking_ids:
                # Do not change the scheduled date of pickings that are already done or cancelled
                for picking in self.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
                    picking.mo_scheduled_date = self.date_planned_start
        return res


    def action_confirm(self):
        self._check_company()
        for production in self:
            if production.bom_id:
                production.consumption = production.bom_id.consumption
            if not production.move_raw_ids:
                raise UserError(_("Add some materials to consume before marking this MO as to do."))
            # In case of Serial number tracking, force the UoM to the UoM of product
            if production.product_tracking == 'serial' and production.product_uom_id != production.product_id.uom_id:
                production.write({
                    'product_qty': production.product_uom_id._compute_quantity(production.product_qty, production.product_id.uom_id),
                    'product_uom_id': production.product_id.uom_id
                })
                for move_finish in production.move_finished_ids.filtered(lambda m: m.product_id == production.product_id):
                    move_finish.write({
                        'product_uom_qty': move_finish.product_uom._compute_quantity(move_finish.product_uom_qty, move_finish.product_id.uom_id),
                        'product_uom': move_finish.product_id.uom_id
                    })

            production.move_raw_ids._adjust_procure_method()
            # pdb.set_trace()
            # print('finished',production.move_finished_ids)
            # print('raw',production.move_raw_ids)
            # for line in production.move_raw_ids:
            #     print('MRP',line.production_id,line.created_production_id,line.raw_material_production_id)
            # for line in production.move_finished_ids:
            #     print('MRP',line.production_id,line.created_production_id,line.raw_material_production_id)
            # self.env.context = dict(self.env.context)
            # if
            # self.env.context.update({
            #     'mrp_production_id': self.id,
            #     'mrp_production': self,
            # })
            # abc = (production.move_raw_ids | production.move_finished_ids)
            (production.move_raw_ids | production.move_finished_ids)._action_confirm()
            production.workorder_ids._action_confirm()
            # run scheduler for moves forecasted to not have enough in stock
            production.move_raw_ids._trigger_scheduler()
            for rec in self.picking_ids:
                rec.mrp_production_id = self.id
        return True

    @api.depends('procurement_group_id')
    def _compute_picking_ids(self):
        for order in self:
            order.picking_ids = self.env['stock.picking'].search([
                ('group_id', '=', order.procurement_group_id.id), ('group_id', '!=', False),
            ])
            for rec in order.picking_ids:
                rec.mrp_production_id = order.id
            order.delivery_count = len(order.picking_ids)


    # def action_confirm(self):
    #     self.env.context = dict(self.env.context)
    #     self.env.context.update({
    #         'mrp_production_id': self.id,
    #         'mrp_production': self,
    #     })
    #     res = super(MRPProduction, self).action_confirm()
    #     return res

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        """ return create values for new picking that will be linked with group
        of moves in self.
        """
        for rec in self:
            print(rec.id,rec.name,rec.production_id,rec.created_production_id,rec.raw_material_production_id)
        origins = self.filtered(lambda m: m.origin).mapped('origin')
        # print('origins',origins)
        origins = list(dict.fromkeys(origins)) # create a list of unique items
        # Will display source document if any, when multiple different origins
        # are found display a maximum of 5
        if len(origins) == 0:
            origin = False
        else:
            origin = ','.join(origins[:5])
            if len(origins) > 5:
                origin += "..."
        partners = self.mapped('partner_id')
        partner = len(partners) == 1 and partners.id or False
        # pdb.set_trace()
        if 'mrp_production_id' in self.env.context:
            return {
                'mrp_production_id': self.env.context['mrp_production_id'],
                'origin': origin,
                'company_id': self.mapped('company_id').id,
                'user_id': False,
                'move_type': self.mapped('group_id').move_type or 'direct',
                'partner_id': partner,
                'picking_type_id': self.mapped('picking_type_id').id,
                'location_id': self.mapped('location_id').id,
                'location_dest_id': self.mapped('location_dest_id').id,
            }
        else:
            return {
                'origin': origin,
                'company_id': self.mapped('company_id').id,
                'user_id': False,
                'move_type': self.mapped('group_id').move_type or 'direct',
                'partner_id': partner,
                'picking_type_id': self.mapped('picking_type_id').id,
                'location_id': self.mapped('location_id').id,
                'location_dest_id': self.mapped('location_dest_id').id,
            }



class StockPicking(models.Model):
    _inherit = 'stock.picking'

    mo_scheduled_date = fields.Datetime(string='Mo scheduled date')
    mrp_production_id = fields.Many2one('mrp.production')

    @api.depends('move_lines.state', 'move_lines.date', 'move_type','mo_scheduled_date','mrp_production_id')
    def _compute_scheduled_date(self):
        for picking in self:
            # print(picking.move_type)
            # Do not change the scheduled date of pickings that are already done or cancelled
            if picking.state not in ('done', 'cancel'):
                moves_dates = picking.move_lines.filtered(lambda move: move.state not in ('done', 'cancel')).mapped('date')
                if picking.move_type == 'direct':
                    production_order = self.env['mrp.production'].search([('name', '=', picking.origin)], limit=1)
                    if production_order:
                        picking.scheduled_date = production_order.date_planned_start or fields.Datetime.now()
                    elif picking.mrp_production_id:
                        picking.scheduled_date = picking.mrp_production_id.date_planned_start or fields.Datetime.now()
                    else:
                        picking.scheduled_date = min(moves_dates, default=picking.scheduled_date or fields.Datetime.now())
                else:
                    production_order = self.env['mrp.production'].search([('name', '=', picking.origin)], limit=1)
                    if production_order:
                        picking.scheduled_date = production_order.date_planned_start or fields.Datetime.now()
                    elif picking.mrp_production_id:
                        picking.scheduled_date = picking.mrp_production_id.date_planned_start or fields.Datetime.now()
                    else:
                        picking.scheduled_date = max(moves_dates, default=picking.scheduled_date or fields.Datetime.now())
