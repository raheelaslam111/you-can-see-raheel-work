from odoo import models, fields, api, _


class MRPPackagingDateWizard(models.TransientModel):
    _name = 'mrp.packaging.date.wizard'
    _description = 'MRP Packaging Date Wizard'

    mo_ids = fields.Many2many('mrp.production')
    date_packaging = fields.Date('Packaging Date', default=fields.Date.context_today)
    date_error = fields.Char()

    @api.model
    def default_get(self, fields):
        res = super(MRPPackagingDateWizard, self).default_get(fields)
        # res_ids = self._context.get('active_ids')
        res_ids = self.env['mrp.production'].browse(self.env.context['active_ids'])
        res.update({
            'mo_ids': res_ids,
        })
        return res

    def action_done(self):
        for rec in self.mo_ids:
            rec.write({
                'packaging_date': self.date_packaging
            })
            return rec.button_mark_done()

    @api.onchange('date_packaging')
    def _onchange_date_packaging(self):
        for rec in self:
            if rec.date_packaging:
                if rec.date_packaging > fields.Date.context_today(self):
                    rec.date_error = "Date should not be in future."
                    return {
                        'warning': {
                            'title': _('Date Validation!'),
                            'message': _("Date should not be in future.")}}
                elif rec.date_packaging < fields.Date.context_today(self):
                    rec.date_error = False
                    return {
                        'warning': {
                            'title': _('Date Warning!'),
                            'message': _("You have set a date that is in the past.")}}

                else:
                    rec.date_error = False
