import pdb

from odoo import models, fields, _
import json
import requests
import logging

logger = logging.getLogger(__name__)
TIMEOUT = 100
import base64
from odoo.exceptions import UserError, ValidationError


class ImportAPIData(models.TransientModel):
    _name = 'import.api.data'

    def _get_outputs(self):
        if self._context.get('active_ids'):
            return self.env['product.lines'].search([('id', 'in', self._context.get('active_ids'))])

    product_ids = fields.Many2many('product.lines', string="Products", default=lambda self: self._get_outputs())

    def import_data(self):
        pro = self.env['product.product']
        for product in self.product_ids:
            product_inv = self.env['product.product'].search([('default_code', '=', product.model_number), ('is_aviq_product', '=', True)])
            if not product_inv:
                product_specs_list2 = []
                for spec in product.product_specs_ids:
                    values_specs2 = {
                        'specification_id': spec.specification_id,
                        'spec_name': spec.spec_name,
                        'spec_unit': spec.spec_unit,
                        'spec_value': spec.spec_value,
                        'spec_group': spec.spec_group,
                        'spec_data_type': spec.spec_data_type,
                        # 'product_id': spec.product_id

                    }
                    product_specs_list2.append([0, 0, values_specs2])
                values = {
                    'name': product.part_number or product.model_number or '',
                    'description': product.short_description,
                    'default_code': product.model_number,
                    'is_aviq_product': True,
                    'image_medium': product.image_spotlight or False,  # base64.b64encode(requests.get(product.image_spotlight).content) or False,
                    'manufacturer': product.manufacturer,
                    'product_specs_ids': product_specs_list2,
                    'description_sale': product.name,
                    'description_purchase': product.name,
                }
                product_inv = self.env['product.product'].create(values)
                product.odoo_product_id = product_inv.id

                product_inv.product_tmpl_id.is_aviq_product = True
            pro += product_inv

        product_list = pro.mapped('id')
        form_view = self.env.ref('product.product_normal_form_view')
        tree_view = self.env.ref('product.product_template_tree_view')
        return {
            'domain': [('id', 'in', product_list)],
            'name': _('Products'),
            # 'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.product',
            'view_id': False,
            'views': [(tree_view and tree_view.id or False, 'tree'),
                      (form_view and form_view.id or False, 'form')],
            # 'context': {'default_class_id': self.id},
            'type': 'ir.actions.act_window'
        }
