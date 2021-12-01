import operator
import pdb

from odoo import http,_
from odoo.exceptions import UserError
from odoo.http import request

from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.main import Session, ensure_db



class PasswordSecurityHome(AuthSignupHome):

    @http.route(['/testing'], type='http', auth="public", website=True)
    def testing_detail(self,**kw):

        return request.render("registration_form_custom.custom_template_for_testing")

    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """
        values = {key: qcontext.get(key) for key in ('login', 'name', 'password','passport', 'cnic',
                                                         'contact_turk',
                                                         'radiogroup',
                                                         'profession_detail',
                                                         'kimlik_number',
                                                         'turk_city',
                                                         'family_detail',)}
        # values_reg = {key: qcontext.get(key) for key in ('passport', 'cnic',
        #                                                  'contact_turk',
        #                                                  'radiogroup',
        #                                                  'profession_detail',
        #                                                  'kimlik_number',
        #                                                  'turk_city',
        #                                                  'family_detail',
        #                                                  )}
        # request.env.context = dict(self.env.context)
        # request.env.context.update(values_reg)
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '')
        if lang in supported_lang_codes:
            values['lang'] = lang
        self._signup_with_values(qcontext.get('token'), values)
        request.env.cr.commit()

    def _signup_with_values(self, token, values):
        db, login, password = request.env['res.users'].sudo().signup(values, token)
        request.env.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
        uid = request.session.authenticate(db, login, password)
        if not uid:
            raise SignupError(_('Authentication Failed.'))


