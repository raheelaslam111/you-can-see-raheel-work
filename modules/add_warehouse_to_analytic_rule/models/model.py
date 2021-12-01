import pdb

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools import float_compare, float_round
from odoo.tools.float_utils import float_compare, float_is_zero


class AccountAnalyticDefault(models.Model):
    _inherit = "account.analytic.default"

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', store=True)

    # , domain = "['|', ('company_id', '=', False), ('company_id', '=', company_id)]"

    @api.model
    def account_get(self, product_id=None, partner_id=None, account_id=None, user_id=None, date=None, company_id=None, warehouse_id=None):
        domain = []
        if product_id:
            domain += ['|', ('product_id', '=', product_id)]
        domain += [('product_id', '=', False)]
        if partner_id:
            domain += ['|', ('partner_id', '=', partner_id)]
        domain += [('partner_id', '=', False)]
        if account_id:
            domain += ['|', ('account_id', '=', account_id)]
        domain += [('account_id', '=', False)]
        if company_id:
            domain += ['|', ('company_id', '=', company_id)]
        domain += [('company_id', '=', False)]
        if user_id:
            domain += ['|', ('user_id', '=', user_id)]
        domain += [('user_id', '=', False)]
        if warehouse_id:
            domain += ['|', ('warehouse_id', '=', warehouse_id)]
        domain += [('warehouse_id', '=', False)]
        if date:
            domain += ['|', ('date_start', '<=', date), ('date_start', '=', False)]
            domain += ['|', ('date_stop', '>=', date), ('date_stop', '=', False)]
        best_index = -1
        res = self.env['account.analytic.default']
        for rec in self.search(domain):
            index = 0
            if rec.product_id: index += 1
            if rec.partner_id: index += 1
            if rec.account_id: index += 1
            if rec.company_id: index += 1
            if rec.user_id: index += 1
            if rec.warehouse_id: index += 1
            if rec.date_start: index += 1
            if rec.date_stop: index += 1
            if index > best_index:
                res = rec
                best_index = index
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    #     @api.model
    #     def create(self, vals):
    #         res = super(SaleOrder, self).create(vals)
    #         if res.warehouse_id:
    #             account_analytic_default = self.env['account.analytic.default'].search([('warehouse_id', '=', res.warehouse_id.id)], limit=1)
    #             res.analytic_account_id = account_analytic_default.analytic_id.id or False
    #         return res

    @api.onchange('warehouse_id')
    def _set_warehouse_analytic_account(self):
        analytic_account_id = False
        if self.warehouse_id:
            # account_analytic_default = self.env['account.analytic.default'].search([('warehouse_id', '=', self.warehouse_id.id)], limit=1)
            account_analytic_default = self.env['account.analytic.default'].account_get(
                partner_id=self.partner_id.commercial_partner_id.id,
                company_id=self.company_id.id,
                warehouse_id=self.warehouse_id.id
            )
            self.analytic_account_id = account_analytic_default.analytic_id.id or False



class StockMove(models.Model):

    _inherit = 'stock.move'

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        self.ensure_one()
        AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        if move_lines:
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': description,
                'stock_move_id': self.id,
                'stock_valuation_layer_ids': [(6, None, [svl_id])],
                'move_type': 'entry',
                'invoice_origin': self.origin,
                'is_valuation': 'valuation',
            })
            new_account_move._post()



class AccountMove(models.Model):
    _inherit = 'account.move'

    # origin_so = fields.Char(string='Sale Order Ref.')
    is_valuation = fields.Selection([('valuation', 'Stock Valuation'), ('normal', 'Normal')],string='Valuation',default='normal')

    def action_post(self):
        if (self.move_type == 'in_invoice'):
            for line in self.invoice_line_ids:
                if not line.analytic_account_id:
                    raise ValidationError(_("Product Analytical Account is Required"))

        return super(AccountMove, self).action_post()

    def _auto_create_asset(self):
        create_list = []
        invoice_list = []
        auto_validate = []
        for move in self:
            if not move.is_invoice():
                continue

            for move_line in move.line_ids.filtered(lambda line: not (move.move_type in ('out_invoice', 'out_refund') and line.account_id.user_type_id.internal_group == 'asset')):
                if (
                        move_line.account_id
                        and (move_line.account_id.can_create_asset)
                        and move_line.account_id.create_asset != "no"
                        and not move.reversed_entry_id
                        and not (move_line.currency_id or move.currency_id).is_zero(move_line.price_total)
                        and not move_line.asset_ids
                        and move_line.price_total > 0
                ):
                    if not move_line.name:
                        raise UserError(_('Journal Items of {account} should have a label in order to generate an asset').format(account=move_line.account_id.display_name))
                    if move_line.account_id.multiple_assets_per_line:
                        # decimal quantities are not supported, quantities are rounded to the lower int
                        units_quantity = max(1, int(move_line.quantity))
                    else:
                        units_quantity = 1
                    vals = {
                        'name': move_line.name,
                        'company_id': move_line.company_id.id,
                        'currency_id': move_line.company_currency_id.id,
                        'account_analytic_id': move_line.analytic_account_id.id,
                        'analytic_tag_ids': [(6, False, move_line.analytic_tag_ids.ids)],
                        'original_move_line_ids': [(6, False, move_line.ids)],
                        'state': 'draft',
                    }

                    model_id = move_line.account_id.asset_model
                    if model_id:
                        vals.update({
                            'model_id': model_id.id,
                        })
                    auto_validate.extend([move_line.account_id.create_asset == 'validate'] * units_quantity)
                    invoice_list.extend([move] * units_quantity)
                    create_list.extend([vals] * units_quantity)

        assets = self.env['account.asset'].create(create_list)

        for asset, vals, invoice, validate in zip(assets, create_list, invoice_list, auto_validate):
            if 'model_id' in vals:
                asset._onchange_model_id()
                if validate:
                    asset.validate()
            if invoice:
                asset_name = {
                    'purchase': _('Asset'),
                    'sale': _('Deferred revenue'),
                    'expense': _('Deferred expense'),
                }[asset.asset_type]
                msg = _('%s created from invoice') % (asset_name)
                msg += ': <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>' % (invoice.id, invoice.name)
                asset.message_post(body=msg)
        for c_asset in assets:
            for move in self:
                required_line = move.line_ids.filtered(lambda line: not (move.move_type in (
                    'out_invoice', 'out_refund') and line.account_id.user_type_id.internal_group == 'asset') and line.name == c_asset.name)
                if required_line:
                    c_asset.account_analytic_id = required_line.analytic_account_id.id
                    print(c_asset.account_analytic_id, 'c_asset')
        for c in assets:
            print(c.account_analytic_id, 'c')
        return assets

    @api.model
    def _prepare_move_for_asset_depreciation(self, vals):
        missing_fields = set(['asset_id', 'move_ref', 'amount', 'asset_remaining_value', 'asset_depreciated_value']) - set(vals)
        if missing_fields:
            raise UserError(_('Some fields are missing {}').format(', '.join(missing_fields)))
        asset = vals['asset_id']
        account_analytic_id = asset.account_analytic_id
        analytic_tag_ids = asset.analytic_tag_ids
        depreciation_date = vals.get('date', fields.Date.context_today(self))
        company_currency = asset.company_id.currency_id
        current_currency = asset.currency_id
        prec = company_currency.decimal_places
        amount_currency = vals['amount']
        amount = current_currency._convert(amount_currency, company_currency, asset.company_id, depreciation_date)
        # Keep the partner on the original invoice if there is only one
        partner = asset.original_move_line_ids.mapped('partner_id')
        partner = partner[:1] if len(partner) <= 1 else self.env['res.partner']
        if asset.original_move_line_ids and asset.original_move_line_ids[0].move_id.move_type in ['in_refund', 'out_refund']:
            amount = -amount
            amount_currency = -amount_currency
        move_line_1 = {
            'name': asset.name,
            'partner_id': partner.id,
            'account_id': asset.account_depreciation_id.id,
            'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'analytic_account_id': account_analytic_id.id if asset.asset_type in ('purchase', 'expense', 'sale') else False,
            'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type == 'sale' else False,
            'currency_id': current_currency.id,
            'amount_currency': -amount_currency,
        }
        move_line_2 = {
            'name': asset.name,
            'partner_id': partner.id,
            'account_id': asset.account_depreciation_expense_id.id,
            'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'analytic_account_id': account_analytic_id.id if asset.asset_type in ('purchase', 'expense') else False,
            'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type in ('purchase', 'expense') else False,
            'currency_id': current_currency.id,
            'amount_currency': amount_currency,
        }
        move_vals = {
            'ref': vals['move_ref'],
            'partner_id': partner.id,
            'date': depreciation_date,
            'journal_id': asset.journal_id.id,
            'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
            'asset_id': asset.id,
            'asset_remaining_value': vals['asset_remaining_value'],
            'asset_depreciated_value': vals['asset_depreciated_value'],
            'amount_total': amount,
            'name': '/',
            'asset_value_change': vals.get('asset_value_change', False),
            'move_type': 'entry',
            'currency_id': current_currency.id,
        }
        return move_vals

    def _stock_account_prepare_anglo_saxon_in_lines_vals(self):
        ''' Prepare values used to create the journal items (account.move.line) corresponding to the price difference
         lines for vendor bills.

        Example:

        Buy a product having a cost of 9 and a supplier price of 10 and being a storable product and having a perpetual
        valuation in FIFO. The vendor bill's journal entries looks like:

        Account                                     | Debit | Credit
        ---------------------------------------------------------------
        101120 Stock Interim Account (Received)     | 10.0  |
        ---------------------------------------------------------------
        101100 Account Payable                      |       | 10.0
        ---------------------------------------------------------------

        This method computes values used to make two additional journal items:

        ---------------------------------------------------------------
        101120 Stock Interim Account (Received)     |       | 1.0
        ---------------------------------------------------------------
        xxxxxx Price Difference Account             | 1.0   |
        ---------------------------------------------------------------

        :return: A list of Python dictionary to be passed to env['account.move.line'].create.
        '''
        lines_vals_list = []
        price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')

        for move in self:
            if move.move_type not in ('in_invoice', 'in_refund', 'in_receipt') or not move.company_id.anglo_saxon_accounting:
                continue

            move = move.with_company(move.company_id)
            for line in move.invoice_line_ids.filtered(lambda line: line.product_id.type == 'product' and line.product_id.valuation == 'real_time'):

                # Filter out lines being not eligible for price difference.
                if line.product_id.type != 'product' or line.product_id.valuation != 'real_time':
                    continue

                # Retrieve accounts needed to generate the price difference.
                debit_pdiff_account = line.product_id.property_account_creditor_price_difference \
                                or line.product_id.categ_id.property_account_creditor_price_difference_categ
                debit_pdiff_account = move.fiscal_position_id.map_account(debit_pdiff_account)
                if not debit_pdiff_account:
                    continue

                if line.product_id.cost_method != 'standard' and line.purchase_line_id:
                    po_currency = line.purchase_line_id.currency_id
                    po_company = line.purchase_line_id.company_id

                    # Retrieve stock valuation moves.
                    valuation_stock_moves = self.env['stock.move'].search([
                        ('purchase_line_id', '=', line.purchase_line_id.id),
                        ('state', '=', 'done'),
                        ('product_qty', '!=', 0.0),
                    ])
                    if move.move_type == 'in_refund':
                        valuation_stock_moves = valuation_stock_moves.filtered(lambda stock_move: stock_move._is_out())
                    else:
                        valuation_stock_moves = valuation_stock_moves.filtered(lambda stock_move: stock_move._is_in())

                    if valuation_stock_moves:
                        valuation_price_unit_total = 0
                        valuation_total_qty = 0
                        for val_stock_move in valuation_stock_moves:
                            # In case val_stock_move is a return move, its valuation entries have been made with the
                            # currency rate corresponding to the original stock move
                            valuation_date = val_stock_move.origin_returned_move_id.date or val_stock_move.date
                            svl = val_stock_move.with_context(active_test=False).mapped('stock_valuation_layer_ids').filtered(lambda l: l.quantity)
                            layers_qty = sum(svl.mapped('quantity'))
                            layers_values = sum(svl.mapped('value'))
                            valuation_price_unit_total += line.company_currency_id._convert(
                                layers_values, move.currency_id,
                                move.company_id, valuation_date, round=False,
                            )
                            valuation_total_qty += layers_qty

                        if float_is_zero(valuation_total_qty, precision_rounding=line.product_uom_id.rounding or line.product_id.uom_id.rounding):
                            raise UserError(_('Odoo is not able to generate the anglo saxon entries. The total valuation of %s is zero.') % line.product_id.display_name)
                        valuation_price_unit = valuation_price_unit_total / valuation_total_qty
                        valuation_price_unit = line.product_id.uom_id._compute_price(valuation_price_unit, line.product_uom_id)

                    elif line.product_id.cost_method == 'fifo':
                        # In this condition, we have a real price-valuated product which has not yet been received
                        valuation_price_unit = po_currency._convert(
                            line.purchase_line_id.price_unit, move.currency_id,
                            po_company, move.date, round=False,
                        )
                    else:
                        # For average/fifo/lifo costing method, fetch real cost price from incoming moves.
                        price_unit = line.purchase_line_id.product_uom._compute_price(line.purchase_line_id.price_unit, line.product_uom_id)
                        valuation_price_unit = po_currency._convert(
                            price_unit, move.currency_id,
                            po_company, move.date, round=False
                        )

                else:
                    # Valuation_price unit is always expressed in invoice currency, so that it can always be computed with the good rate
                    price_unit = line.product_id.uom_id._compute_price(line.product_id.standard_price, line.product_uom_id)
                    valuation_price_unit = line.company_currency_id._convert(
                        price_unit, move.currency_id,
                        move.company_id, fields.Date.today(), round=False
                    )


                price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                if line.tax_ids and line.quantity:
                    # We do not want to round the price unit since :
                    # - It does not follow the currency precision
                    # - It may include a discount
                    # Since compute_all still rounds the total, we use an ugly workaround:
                    # multiply then divide the price unit.
                    price_unit *= line.quantity
                    price_unit = line.tax_ids.with_context(round=False, force_sign=move._get_tax_force_sign()).compute_all(
                        price_unit, currency=move.currency_id, quantity=1.0, is_refund=move.move_type == 'in_refund')['total_excluded']
                    price_unit /= line.quantity

                price_unit_val_dif = price_unit - valuation_price_unit
                price_subtotal = line.quantity * price_unit_val_dif

                # We consider there is a price difference if the subtotal is not zero. In case a
                # discount has been applied, we can't round the price unit anymore, and hence we
                # can't compare them.
                if (
                    not move.currency_id.is_zero(price_subtotal)
                    and float_compare(line["price_unit"], line.price_unit, precision_digits=price_unit_prec) == 0
                ):

                    # Add price difference account line.
                    vals = {
                        'name': line.name[:64],
                        'move_id': move.id,
                        'currency_id': line.currency_id.id,
                        'product_id': line.product_id.id,
                        'product_uom_id': line.product_uom_id.id,
                        'quantity': line.quantity,
                        'price_unit': price_unit_val_dif,
                        'price_subtotal': line.quantity * price_unit_val_dif,
                        'account_id': debit_pdiff_account.id,
                        'analytic_account_id': line.analytic_account_id.id,
                        'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                        'exclude_from_invoice_tab': True,
                        'is_anglo_saxon_line': True,
                    }
                    vals.update(line._get_fields_onchange_subtotal(price_subtotal=vals['price_subtotal']))
                    lines_vals_list.append(vals)

                    # Correct the amount of the current line.
                    vals = {
                        'name': line.name[:64],
                        'move_id': move.id,
                        'currency_id': line.currency_id.id,
                        'product_id': line.product_id.id,
                        'product_uom_id': line.product_uom_id.id,
                        'quantity': line.quantity,
                        'price_unit': -price_unit_val_dif,
                        'price_subtotal': line.quantity * -price_unit_val_dif,
                        'account_id': line.account_id.id,
                        'analytic_account_id': line.analytic_account_id.id,
                        'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                        'exclude_from_invoice_tab': True,
                        'is_anglo_saxon_line': True,
                    }
                    vals.update(line._get_fields_onchange_subtotal(price_subtotal=vals['price_subtotal']))
                    lines_vals_list.append(vals)
        return lines_vals_list

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        ''' Prepare values used to create the journal items (account.move.line) corresponding to the Cost of Good Sold
        lines (COGS) for customer invoices.

        Example:

        Buy a product having a cost of 9 being a storable product and having a perpetual valuation in FIFO.
        Sell this product at a price of 10. The customer invoice's journal entries looks like:

        Account                                     | Debit | Credit
        ---------------------------------------------------------------
        200000 Product Sales                        |       | 10.0
        ---------------------------------------------------------------
        101200 Account Receivable                   | 10.0  |
        ---------------------------------------------------------------

        This method computes values used to make two additional journal items:

        ---------------------------------------------------------------
        220000 Expenses                             | 9.0   |
        ---------------------------------------------------------------
        101130 Stock Interim Account (Delivered)    |       | 9.0
        ---------------------------------------------------------------

        Note: COGS are only generated for customer invoices except refund made to cancel an invoice.

        :return: A list of Python dictionary to be passed to env['account.move.line'].create.
        '''

        lines_vals_list = []
        for move in self:
            if not move.is_sale_document(include_receipts=True) or not move.company_id.anglo_saxon_accounting:
                continue

            for line in move.invoice_line_ids:

                # Filter out lines being not eligible for COGS.
                if line.product_id.type != 'product' or line.product_id.valuation != 'real_time':
                    continue

                # Retrieve accounts needed to generate the COGS.
                accounts = (
                    line.product_id.product_tmpl_id
                    .with_company(line.company_id)
                    .get_product_accounts(fiscal_pos=move.fiscal_position_id)
                )
                debit_interim_account = accounts['stock_output']
                credit_expense_account = accounts['expense'] or self.journal_id.default_account_id
                if not debit_interim_account or not credit_expense_account:
                    continue

                # Compute accounting fields.
                sign = -1 if move.move_type == 'out_refund' else 1
                price_unit = line._stock_account_get_anglo_saxon_price_unit()
                balance = sign * line.quantity * price_unit

                # Add interim account line.
                print('b')


                lines_vals_list.append({
                    'name': line.name[:64],
                    'move_id': move.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'quantity': line.quantity,
                    'price_unit': price_unit,
                    'debit': balance < 0.0 and -balance or 0.0,
                    'credit': balance > 0.0 and balance or 0.0,
                    'account_id': debit_interim_account.id,
                    'analytic_account_id': line.analytic_account_id.id,
                    'exclude_from_invoice_tab': True,
                    'is_anglo_saxon_line': True,
                })

                # Add expense account line.
                print('x')

                lines_vals_list.append({
                    'name': line.name[:64],
                    'move_id': move.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'quantity': line.quantity,
                    'price_unit': -price_unit,
                    'debit': balance > 0.0 and balance or 0.0,
                    'credit': balance < 0.0 and -balance or 0.0,
                    'account_id': credit_expense_account.id,
                    'analytic_account_id': line.analytic_account_id.id,
                    'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                    'exclude_from_invoice_tab': True,
                    'is_anglo_saxon_line': True,
                })
        print('z')

        return lines_vals_list


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', string='Warehouse', related='picking_type_id.warehouse_id', readonly=False)

    @api.onchange('warehouse_id')
    def _set_warehouse(self):
        warehouse_id = self.warehouse_id.id if self.warehouse_id else False
        if warehouse_id:
            account_analytic_default = self.env['account.analytic.default'].account_get(
                company_id=self.company_id.id,
                warehouse_id=self.warehouse_id.id
            )
        if self.order_line:
            for line in self.order_line:
                line.warehouse_id = warehouse_id
                if warehouse_id:
                    line.account_analytic_id = account_analytic_default.analytic_id.id if account_analytic_default and account_analytic_default.analytic_id else False


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', string='Warehouse')
    warehouse_dev = fields.Boolean(
        string='Warehouse_dev', compute='compute_warehouse',
        required=False)

    @api.depends('order_id')
    def compute_warehouse(self):
        # assign value to warehouse in PO line
        for rec in self:
            if rec.order_id and rec.order_id.picking_type_id:
                rec.warehouse_id = rec.order_id.picking_type_id.warehouse_id.id
                rec.warehouse_dev = True
            else:
                rec.warehouse_dev = False

    #     @api.model
    #     def create(self, vals):
    #         res = super(PurchaseOrderLine, self).create(vals)
    #         if res.order_id and res.order_id.picking_type_id and res.order_id.picking_type_id.warehouse_id:
    #             account_analytic_default = self.env['account.analytic.default'].search(
    #                 [('warehouse_id', '=', res.order_id.picking_type_id.warehouse_id.id)], limit=1)
    #             res.account_analytic_id = account_analytic_default.analytic_id.id or False
    #         return res

    # def write(self, vals):
    #     res = super(PurchaseOrderLine, self).write(vals)
    #     if self.order_id.picking_type_id.warehouse_id:
    #         account_analytic_default = self.env['account.analytic.default'].search(
    #             [('warehouse_id', '=', self.order_id.picking_type_id.warehouse_id.id)], limit=1)
    #         print(account_analytic_default.analytic_id)
    #         self.account_analytic_id = account_analytic_default.analytic_id.id or False
    #     return res

    @api.onchange('warehouse_id', 'order_id')
    def _set_warehouse_analytic_account(self):
        analytic_account_id = False
        if self.warehouse_id:
            account_analytic_default = self.env['account.analytic.default'].account_get(
                company_id=self.company_id.id,
                warehouse_id=self.warehouse_id.id
            )
            account_analytic_id = account_analytic_default.analytic_id.id or False
        # if not analytic_account_id:
        self.account_analytic_id = account_analytic_id


class AccountMoveLinemy(models.Model):
    _inherit = 'account.move.line'

    # origin_so = fields.Char(string='Sale Order Ref.')
    is_valuation = fields.Selection(related='move_id.is_valuation',string='Is Valuation',store=True)
    invoice_origin = fields.Char(related='move_id.invoice_origin',store=True)

    # purchase_line_id = fields.Many2one('purchase.order.line', 'Purchase Order Line', ondelete='set null', index=True)
    # purchase_order_id = fields.Many2one('purchase.order', 'Purchase Order', related='purchase_line_id.order_id', readonly=True)

    #     @api.model_create_multi
    #     def create(self, vals):
    #         # print(vals)
    #         res = super(AccountMoveLinemy, self).create(vals)
    #         # print(res)
    #         if res.purchase_line_id:
    #             if res.purchase_line_id.account_analytic_id:
    #                 res.analytic_account_id = res.purchase_line_id.account_analytic_id.id or False
    #             elif res.purchase_line_id.order_id.picking_type_id and res.purchase_line_id.order_id.picking_type_id.warehouse_id:
    #                 account_analytic_default = self.env['account.analytic.default'].search(
    #                     [('warehouse_id', '=', res.purchase_line_id.order_id.picking_type_id.warehouse_id.id)], limit=1)
    #                 res.analytic_account_id = account_analytic_default.analytic_id.id or False
    #         if res.sale_line_ids:
    #             if res.sale_line_ids[0] and res.sale_line_ids[0].order_id.analytic_account_id:
    #                 res.analytic_account_id = res.sale_line_ids[0].order_id.analytic_account_id.id or False
    #             elif res.sale_line_ids[0] and res.sale_line_ids[0].order_id.warehouse_id:
    #                 account_analytic_default = self.env['account.analytic.default'].search([('warehouse_id', '=', res.sale_line_ids[0].order_id.warehouse_id.id)], limit=1)
    #                 res.analytic_account_id = account_analytic_default.analytic_id.id or False
    #
    #         if res.move_id  and res.move_id.stock_move_id:
    #             warehouse_id = res.move_id.stock_move_id.location_dest_id.x_studio_warehouse
    #             account_analytic_default = self.env['account.analytic.default'].search([('warehouse_id', '=', warehouse_id.id)], limit=1)
    #             res.analytic_account_id = account_analytic_default.analytic_id.id or False
    #         return res

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                          index=True, compute="_compute_analytic_account", inverse='_set_analytic_account', store=True, readonly=False, check_company=True, copy=True)
    user_selected_analytic_account = fields.Many2one('account.analytic.account', string='Analytic Account(dev)')
    bypass_analytic_rule = fields.Boolean(string='User changed analytic account', default=False)

    def _set_analytic_account(self):
        for rec in self:
            rec.bypass_analytic_rule = True
            rec.user_selected_analytic_account = rec.analytic_account_id

    @api.depends('statement_id','product_id', 'account_id', 'partner_id', 'purchase_line_id', 'purchase_line_id.account_analytic_id', 'sale_line_ids', 'sale_line_ids.order_id.analytic_account_id', 'move_id',
                 'move_id.stock_move_id', 'move_id.stock_move_id.location_dest_id', 'move_id.stock_move_id.location_dest_id.x_studio_warehouse')
    def _compute_analytic_account(self):
        for record in self:
            analytic_account_id = record.analytic_account_id if record.analytic_account_id else False
            analytic_tag_ids = record.analytic_tag_ids if record.analytic_tag_ids else []
            if not record.bypass_analytic_rule:
                if record:
                    if not analytic_account_id:
                        warehouse_id = False
                        if record.purchase_line_id.order_id.picking_type_id and record.purchase_line_id.order_id.picking_type_id.warehouse_id:
                            warehouse_id = record.purchase_line_id.order_id.picking_type_id.warehouse_id.id
                        if record.sale_line_ids and record.mapped('sale_line_ids.order_id.warehouse_id'):
                            warehouse_id = record.mapped('sale_line_ids.order_id.warehouse_id.id')[0]
                        if record.move_id and record.move_id.stock_move_id:
                            warehouse_id = record.move_id.stock_move_id.location_dest_id.x_studio_warehouse.id
                            if not warehouse_id:
                                warehouse_id = record.move_id.stock_move_id.location_id.x_studio_warehouse.id
                        rec = self.env['account.analytic.default'].account_get(
                            product_id=record.product_id.id,
                            partner_id=record.partner_id.commercial_partner_id.id or record.move_id.partner_id.commercial_partner_id.id,
                            account_id=record.account_id.id,
                            user_id=record.env.uid,
                            date=record.date,
                            company_id=record.move_id.company_id.id,
                            warehouse_id=warehouse_id
                        )
                        if rec:
                            analytic_account_id = rec.analytic_id
                            analytic_tag_ids = rec.analytic_tag_ids
                    if record.purchase_line_id and record.purchase_line_id.account_analytic_id:
                        analytic_account_id = record.purchase_line_id.account_analytic_id.id
            else:
                analytic_account_id = record.user_selected_analytic_account
            record.analytic_account_id = analytic_account_id
            record.analytic_tag_ids = analytic_tag_ids
        return
