import pdb
import json
from odoo import _, api, fields, models
import requests
import base64
from odoo.exceptions import UserError, ValidationError

class ProductProduct(models.Model):
    _inherit = "product.product"

    is_aviq_product = fields.Boolean('AV IQ Product', default=False)
    manufacturer = fields.Char(string='Manufacturer',readonly=True)
    product_specs_ids = fields.One2many('product.product.specs','product_id',string='Product Specs',ondelete='cascade')


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_aviq_product = fields.Boolean('AV IQ Product', default=False)


class ProductMain(models.Model):
    _name = 'product.main'
    _description = 'product_main'
    _rec_name = 'user_name'

    api_id = fields.Many2one('api.settings', string='API')
    user_name = fields.Char(string='User Name', related="api_id.user_name", store=True)
    password = fields.Char(string='Password', related="api_id.password", store=True)
    clientid = fields.Char(string="Client Id", related="api_id.clientid", store=True)
    uid = fields.Char(string='UID', related="api_id.uid", store=True)
    url = fields.Char(String="URL", required=True)
    url_specs = fields.Char(String="URL for Product Specs", required=True)
    option = fields.Selection([('MFR','MFR')
                               ,('Tier1','Tier1')
                               ,('Tier2','Tier2')
                               ,('Tier3','Tier3')],
                              string='Option',
                              help='Single Category IDs If Option begins with Tier OR Single Manufacturer ID If Option=MFR ',
                              default='MFR') # , ('Global', 'Global')
    pgsize = fields.Integer(string='pg size', default='10')
    pgnum = fields.Integer(string='pg num',default='1')
    manufacturer_ids = fields.Many2many('manufacturer.lines',string='Manufacturers')
    categories_ids = fields.Many2many('categories.lines',string='Categories')
    product_lines_ids = fields.One2many('product.lines', 'product_main_id', string='Product Lines',
                                             ondelete='cascade')
    # tax_code_id = fields.Many2one('product.tax.code',string='Product Tax Code')

    #cron Job Fields
    cron_id = fields.Many2one('ir.cron', string='Schedule Activity')
    interval_number = fields.Integer()
    interval_type = fields.Selection(string='Interval_type', selection=[('minutes', 'Minutes'),
                                                                        ('hours', 'Hours'), ('days', 'Days'),
                                                                        ('weeks', 'Weeks'), ('months', 'Months'), ],
                                     default="hours")
    run_date = fields.Datetime(string='Run Date', )
    cron_active = fields.Boolean(sting="Active", )

    @api.model
    def create(self, vals):
        res = super(ProductMain, self).create(vals)
        model_id = self.env['ir.model'].search([('model', '=', self._name)])
        cron_values = {
            'name': "Cron get products " + res.api_id.name + " " + res.user_name,
            'model_id': model_id and model_id.id,
            'state': 'code',
            'code': 'model.cron_get_products(' + str(res.id) +')',
            'interval_number': res.interval_number,
            'interval_type': res.interval_type,
            'numbercall': -1,
            'active': res.cron_active,
        }
        cron = self.env['ir.cron'].sudo().create(cron_values)
        if cron:
            res.cron_id = cron.id
        return res

    @api.onchange('interval_number', 'interval_type', 'run_date', 'cron_active')
    def change_schedule_activity(self):
        if self.cron_id:
            if self.interval_number:
                self.cron_id.interval_number = self.interval_number
            if self.interval_type:
                self.cron_id.interval_type = self.interval_type
            if self.run_date:
                self.cron_id.nextcall = self.run_date
            self.cron_id.active = self.cron_active

    def fetch_products(self):
        if self.option == 'MFR':
            for manufacturer in self.manufacturer_ids:
                self.fetch_products_data(manufacturer.manufacturer_id)
        else:
            for category in self.categories_ids:
                self.fetch_products_data(category.category_id)

    def fetch_products_data(self, ID):

        url = str(self.url)+"?clientid="+str(self.clientid)+"&uid="+str(self.uid)+"&option="+str(self.option)+"&ID="+str(ID)
        if self.pgsize and self.pgnum:
            url = str(self.url)+"?clientid="+str(self.clientid)+"&uid="+str(self.uid)+"&option="+str(self.option)+"&pgsize="+str(self.pgsize)+"&pgnum="+str(self.pgnum)+"&ID="+str(ID)
        elif self.pgsize:
            url = str(self.url) + "?clientid=" + str(self.clientid) + "&uid=" + str(self.uid) + "&option=" + str(self.option) + "&pgsize=" + str(self.pgsize)+ "&ID=" + str(ID)
        elif self.pgnum:
            url = str(self.url)+"?clientid="+str(self.clientid)+"&uid="+str(self.uid)+"&option="+str(self.option)+"&pgnum="+str(self.pgnum)+"&ID="+str(ID)

        auth = (str(self.user_name), str(self.password))
        headers = {'Content-Type': 'application/json'}

        response = requests.request("GET", url=url, headers=headers,auth=auth)
        if response.status_code != 200:
            raise ValidationError(_('Connection is down/Not-Established while getting products.'))

        y = json.loads(response.text)

        for x in y:

            url_specs = str(self.url_specs) + "?ID="+str(x['PRODUCT_ID']) +"&uid=" + str(self.uid) + "&clientid=" + str(self.clientid)

            response_spec = requests.request("GET", url=url_specs, headers=headers, auth=auth)
            if response_spec.status_code != 200:
                raise ValidationError(_('Connection is down/Not-Established while getting product specifications.'))

            product_specs_response = json.loads(response_spec.text)
            product_specs_list = []
            for spec in product_specs_response:
                values_specs = {
                    'specification_id': spec['SPECIFICATION_ID'],
                    'spec_name': spec['SPECNAME'],
                    'spec_unit': spec['SPECUNIT'],
                    'spec_value': spec['SPECVALUE'],
                    'spec_group': spec['SPECGROUP'],
                    'spec_data_type': spec['SPECDATATYPE'],
                    # 'product_line_id': spec['MANUFACTURER_ID']

                }
                product_specs_list.append([0,0,values_specs])

            values = {
                'manufacturer_id' : x['MANUFACTURER_ID'],
                'manufacturer': x['MANUFACTURER'],
                'model_number': x['MODEL_NUMBER'],
                'part_number': x['PART_NUMBER'],
                'upc_number': x['UPC_NUMBER'],
                'name': x['DISPLAY_NAME'],
                'short_description': x['SHORT_DESCRIPTION'],
                'image_url': x['IMAGE_SPOTLIGHT'],
                # 'image_spotlight': x['IMAGE_SPOTLIGHT'] and base64.b64encode(requests.get(x['IMAGE_SPOTLIGHT']).content) or False,
                't1cat': x['T1CAT'],
                't2cat': x['T2CAT'],
                't3cat': x['T3CAT'],
                'model_number_clean': x['MODEL_NUMBER_CLEAN'],
                'msrp': x['MSRP'],
                'row': x['ROW'],
                'product_specs_ids': product_specs_list

            }
            product = self.env['product.lines'].search([('product_main_id','=',self.id),('product_id','=',x['PRODUCT_ID'])], limit=1)
            if product:
                product.write(values)
            else:
                values['product_main_id'] =  self.id,
                values['product_id'] =  x['PRODUCT_ID'],
                product.create(values)

    def create_av_product(self):
        selected_product_lines = self.product_lines_ids.filtered(lambda l: l.create_product == True)
        pro = self.env['product.product']

        for product in selected_product_lines:
            product_inv = self.env['product.product'].search([('default_code','=',product.model_number),('is_aviq_product','=',True)])
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
                    'name' : product.name,
                    'description': product.short_description,
                    'default_code': product.model_number,
                    'is_aviq_product': True,
                    'image_medium': product.image_spotlight or False, #base64.b64encode(requests.get(product.image_spotlight).content) or False,
                    'manufacturer': product.manufacturer,
                    'product_specs_ids': product_specs_list2
                }
                product_inv = self.env['product.product'].create(values)
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

    def url_to_image(self):
        for line in self.product_lines_ids:
            if line.image_url:
                line.image_spotlight = base64.b64encode(requests.get(line.image_url).content)

    def cron_get_products(self, id):
        for rec in self.search([('id', '=', int(id))]):
            rec.fetch_products()
            rec.url_to_image()


class ProductSpecs(models.Model):
    _name = 'product.product.specs'
    _description = 'product.product.specs'
    _rec_name = ''

    specification_id = fields.Integer(string='Specification Id')
    spec_name = fields.Char(string='SPEC.NAME')
    spec_unit = fields.Char(string='SPEC.UNIT')
    spec_value = fields.Char(string='SPEC.VALUE')
    spec_group = fields.Char(string='SPEC.GROUP')
    spec_data_type = fields.Char(string='SPEC.DATA.TYPE')
    product_id = fields.Many2one('product.product',string='Product Id')


class product_lines(models.Model):
    _name = 'product.lines'
    _description = 'product.lines'

    manufacturer_id = fields.Integer(string="MANUFACTURER_ID")
    manufacturer = fields.Char(string="MANUFACTURER")
    product_id = fields.Char(string="PRODUCT_ID")

    model_number = fields.Char(string="MODEL NUMBER")
    part_number = fields.Char(string="PART NUMBER")
    upc_number = fields.Char(string="UPC NUMBER")
    name = fields.Char(string="Name")
    short_description = fields.Text(string="SHORT DESCRIPTION")
    image_spotlight = fields.Binary(string="IMAGE_SPOTLIGHT")
    image_url = fields.Char(string="Image Url")
    t1cat = fields.Char(string="T1CAT")
    t2cat = fields.Char(string="T2CAT")
    t3cat = fields.Char(string="T3CAT")
    model_number_clean = fields.Char(string="MODEL NUMBER CLEAN")
    msrp = fields.Char(string="MSRP")
    row = fields.Char(string="ROW")

    create_product = fields.Boolean(string='Create Product',default=False)

    product_main_id = fields.Many2one('product.main',string='Product API')
    odoo_product_id = fields.Many2one('product.product', string='Odoo Product')

    api_id = fields.Many2one('api.settings', string='API', related="product_main_id.api_id", store=True)
    product_specs_ids = fields.One2many('product.specs','product_line_id',string='Product Specs')


class product_specs(models.Model):
    _name = 'product.specs'
    _description = 'product_specs'
    _rec_name = ''

    specification_id = fields.Integer(string='Specification Id')
    spec_name = fields.Char(string='SPEC.NAME')
    spec_unit = fields.Char(string='SPEC.UNIT')
    spec_value = fields.Char(string='SPEC.VALUE')
    spec_group = fields.Char(string='SPEC.GROUP')
    spec_data_type = fields.Char(string='SPEC.DATA.TYPE')
    product_line_id = fields.Many2one('product.lines',string='Product Line Id')

