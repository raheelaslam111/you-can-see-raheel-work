from odoo import api, fields, models, _


class SurveyInterviewer(models.Model):
    _name = "survey.interviewer"
    _description = "survey interviewer"
    _rec_name = 'partner'

    partner = fields.Many2one(
        comodel_name='res.users',
        string='Interviewer',
        required=False)
    score = fields.Float(
        string='Score',
        required=False)
    custom_questions_id = fields.Many2one('custom.questions',string='')
