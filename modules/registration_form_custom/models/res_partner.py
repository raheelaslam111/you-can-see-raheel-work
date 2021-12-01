# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import pdb

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError
from odoo.addons.auth_signup.models.res_partner import SignupError, now
from odoo.tools.misc import ustr
from ast import literal_eval

class Partner(models.Model):
    _inherit = 'res.partner'

    reg_cnic = fields.Char(string='CNIC')
    contact_turk = fields.Char(string='Turkey Contact No.')
    passport = fields.Char(string='Passport')
    nature_of_stay = fields.Selection([('Short Term/Tourist Visa','Short Term/Tourist Visa'),
                                       ('Student','Student'),
                                       ('Resident Card Holder/Kimlik holder','Resident Card Holder/Kimlik holder'),
                                       ('Other','Other'),
                                       ])
    profession_detail = fields.Text(string='Profession Detail')
    kimlik_number = fields.Char(string='Kimlik Number')
    turk_city = fields.Char(string='City in Turkey')
    family_detail = fields.Text(string='Family Detail')

    @api.model
    def create(self, vals):
        res = super(Partner, self).create(vals)
        if 'passport' in self.env.context:
            res.passport = self.env.context['passport']
        if 'cnic' in self.env.context:
            res.reg_cnic = self.env.context['cnic']
        if 'contact_turk' in self.env.context:
            res.contact_turk = self.env.context['contact_turk']
        if 'radiogroup' in self.env.context:
            res.nature_of_stay = self.env.context['radiogroup']
        if 'profession_detail' in self.env.context:
            res.profession_detail = self.env.context['profession_detail']
        if 'kimlik_number' in self.env.context:
            res.kimlik_number = self.env.context['kimlik_number']
        if 'turk_city' in self.env.context:
            res.turk_city = self.env.context['turk_city']
        if 'family_detail' in self.env.context:
            res.family_detail = self.env.context['family_detail']
        return res



class ResUsers(models.Model):
    _inherit = "res.users"

    reg_cnic = fields.Char(string='CNIC')
    passport = fields.Char(string='Passport')
    contact_turk = fields.Char(string='Turkey Contact No.')
    nature_of_stay = fields.Selection([('Short Term/Tourist Visa', 'Short Term/Tourist Visa'),
                                       ('Student', 'Student'),
                                       ('Resident Card Holder/Kimlik holder', 'Resident Card Holder/Kimlik holder'),
                                       ('Other', 'Other'),
                                       ])
    profession_detail = fields.Text(string='Profession Detail')
    kimlik_number = fields.Char(string='Kimlik Number')
    turk_city = fields.Char(string='City in Turkey')
    family_detail = fields.Text(string='Family Detail')

    @api.model
    def create(self,vals):
        res = super(ResUsers, self).create(vals)
        if 'passport' in self.env.context:
            res.passport = self.env.context['passport']
        if 'cnic' in self.env.context:
            res.reg_cnic = self.env.context['cnic']
        if 'contact_turk' in self.env.context:
            res.contact_turk = self.env.context['contact_turk']
        if 'radiogroup' in self.env.context:
            res.nature_of_stay = self.env.context['radiogroup']
        if 'profession_detail' in self.env.context:
            res.family_detail = self.env.context['profession_detail']
        if 'kimlik_number' in self.env.context:
            res.kimlik_number = self.env.context['kimlik_number']
        if 'turk_city' in self.env.context:
            res.turk_city = self.env.context['turk_city']
        if 'family_detail' in self.env.context:
            res.family_detail = self.env.context['family_detail']

        return res



    @api.model
    def signup(self, values, token=None):
        """ signup a user, to either:
            - create a new user (no token), or
            - create a user for a partner (with token, but no user for partner), or
            - change the password of a user (with token, and existing user).
            :param values: a dictionary with field values that are written on user
            :param token: signup token (optional)
            :return: (dbname, login, password) for the signed up user
        """
        values_reg = {key: values.get(key) for key in ('passport', 'cnic',
                                                     'contact_turk',
                                                     'radiogroup',
                                                     'profession_detail',
                                                     'kimlik_number',
                                                     'turk_city',
                                                     'family_detail')}
        self.env.context = dict(self.env.context)
        self.env.context.update(values_reg)
        values = {key: values.get(key) for key in ('login', 'name', 'password')}

        if token:
            # signup with a token: find the corresponding partner id
            partner = self.env['res.partner']._signup_retrieve_partner(token, check_validity=True, raise_exception=True)
            # invalidate signup token
            partner.write({'signup_token': False, 'signup_type': False, 'signup_expiration': False})

            partner_user = partner.user_ids and partner.user_ids[0] or False

            # avoid overwriting existing (presumably correct) values with geolocation data
            if partner.country_id or partner.zip or partner.city:
                values.pop('city', None)
                values.pop('country_id', None)
            if partner.lang:
                values.pop('lang', None)

            if partner_user:
                # user exists, modify it according to values
                values.pop('login', None)
                values.pop('name', None)
                partner_user.write(values)
                if not partner_user.login_date:
                    partner_user._notify_inviter()
                return (self.env.cr.dbname, partner_user.login, values.get('password'))
            else:
                # user does not exist: sign up invited user
                values.update({
                    'name': partner.name,
                    'partner_id': partner.id,
                    'email': values.get('email') or values.get('login'),
                })
                if partner.company_id:
                    values['company_id'] = partner.company_id.id
                    values['company_ids'] = [(6, 0, [partner.company_id.id])]
                partner_user = self._signup_create_user(values)
                partner_user._notify_inviter()
        else:
            # no token, sign up an external user
            values['email'] = values.get('email') or values.get('login')
            self._signup_create_user(values)

        return (self.env.cr.dbname, values.get('login'), values.get('password'))

    def _create_user_from_template(self, values):
        template_user_id = literal_eval(self.env['ir.config_parameter'].sudo().get_param('base.template_portal_user_id', 'False'))
        template_user = self.browse(template_user_id)
        if not template_user.exists():
            raise ValueError(_('Signup: invalid template user'))

        if not values.get('login'):
            raise ValueError(_('Signup: no login given for new user'))
        if not values.get('partner_id') and not values.get('name'):
            raise ValueError(_('Signup: no name or partner given for new user'))

        # create a copy of the template user (attached to a specific partner_id if given)
        values['active'] = True
        try:
            with self.env.cr.savepoint():
                return template_user.with_context(no_reset_password=True).copy(values)
        except Exception as e:
            # copy may failed if asked login is not available.
            raise SignupError(ustr(e))