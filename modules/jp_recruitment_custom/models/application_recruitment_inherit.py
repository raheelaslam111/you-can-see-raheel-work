import json
import pdb
import random
import uuid
import werkzeug

from odoo import api, exceptions, fields, models, _
from odoo.exceptions import AccessError
from odoo.osv import expression
from odoo.tools import is_html_empty
from odoo.exceptions import UserError, ValidationError


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    survey_user_input_ids = fields.Many2many('custom.questions', string='Evaluation', compute='_default_survey_user_input_ids')
    questionare_survey_user_input_ids = fields.Many2many('questionare.questions', string='Qualifying Survey', compute='_default_questionare_survey_user_input_ids')
    stage_ids = fields.Many2many('hr.recruitment.stage', string='Stages Dict.', compute='get_stages_job_dict')
    link_visible = fields.Boolean('link visible', compute='make_link_visible')
    personality_traits_ids = fields.One2many('personality.traitscore', 'applicant_id', string='Personality')
    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='State',
        required=False)
    city = fields.Char(
        string='City',
        required=False)

    def make_link_visible(self):
        if self.stage_id in self.stage_ids:
            self.link_visible = True
        else:
            self.link_visible = False

    def get_stages_job_dict(self):
        self.stage_ids = self.job_id.interview_survey_dict_ids.mapped('recruitment_stage_id')
        # list = []
        # for line in self.job_id.interview_survey_dict_ids.mapped('survey_id')

    def _default_survey_user_input_ids(self):
        survey_user_input = self.env['custom.questions'].search([('applicant_id', '=', self.id), ('ignore_survey_evaluation', '=', False)]).ids
        if survey_user_input:
            self.survey_user_input_ids = survey_user_input
        else:
            self.survey_user_input_ids = False

    def _default_questionare_survey_user_input_ids(self):
        survey_user_input = self.env['questionare.questions'].search([('applicant_id', '=', self.id)]).ids
        if survey_user_input:
            self.questionare_survey_user_input_ids = survey_user_input
        else:
            self.questionare_survey_user_input_ids = False

    def start_questionare_survey_custom(self):
        get_survey_from_job = self.job_id.questionare_survey_dict_ids.filtered(
            lambda r: r.recruitment_stage_id.id == self.stage_id.id)
        if len(get_survey_from_job) > 0:
            self.job_id.survey_id = get_survey_from_job[0].survey_id.id
            # y=0
            self.ensure_one()
            # create a response and link it to this applicant
            # if not self.response_id:

            # resolve issue while working on T3000
            partner = self.partner_id
            if not partner:
                partner = self.env['res.partner'].search(['|', ('email', '=', self.email_from), ('name', '=', self.email_from)], limit=1)
                if not partner:
                    partner = self.env['res.partner'].create({'email': self.email_from,
                                                              'name': self.partner_name})
                self.partner_id = partner[0].id

            response = get_survey_from_job[0].survey_id._create_answer(partner=self.partner_id)
            # grab the token of the response and start surveying
            return get_survey_from_job[0].survey_id.action_start_survey(answer=response)
        else:
            raise ValidationError(
                _('There is no survey for this Stage in Job dictionary.'))

    def start_survey_custom_123(self):
        get_survey_from_job = self.job_id.interview_survey_dict_ids.filtered(
            lambda r: r.recruitment_stage_id.id == self.stage_id.id)
        if len(get_survey_from_job) > 0:
            self.job_id.survey_id = get_survey_from_job[0].survey_id.id
            # y=0
            self.ensure_one()
            # create a response and link it to this applicant
            # if not self.response_id:

            # resolve issue while working on T3000
            partner = self.partner_id
            if not partner:
                partner = self.env['res.partner'].search(['|', ('email', '=', self.email_from), ('name', '=', self.email_from)], limit=1)
                if not partner:
                    partner = self.env['res.partner'].create({'email': self.email_from,
                                                              'name': self.partner_name})
                self.partner_id = partner[0].id

            response = get_survey_from_job[0].survey_id._create_answer(partner=self.partner_id)
            # grab the token of the response and start surveying
            return get_survey_from_job[0].survey_id.action_start_survey(answer=response)
        else:
            raise ValidationError(
                _('There is no survey for this Stage in Job dictionary.'))


class questionare_questions(models.Model):
    _name = 'questionare.questions'
    _description = 'Questionnaire_questions'
    _rec_name = 'question_id'

    question_id = fields.Many2one('survey.question', string='Question')
    question_type = fields.Selection(related='question_id.question_type')
    survey_id = fields.Many2one('survey.survey', string='Survey')
    survey_user_input_line_id = fields.Many2one('survey.user_input.line', string='Survey User Input')
    ignore_survey_evaluation = fields.Boolean(related='survey_id.ignore_survey_evaluation', string='Ignore Survey Evaluation')
    survey_name = fields.Char(related='survey_id.title')
    applicant_id = fields.Many2one('hr.applicant', string='Applicant')
    value_text_box = fields.Text(string="Answer")


class custom_questions(models.Model):
    _name = 'custom.questions'
    _description = 'custom_questions'
    _rec_name = 'question_id'

    question_id = fields.Many2one('survey.question', string='Question')
    question_type = fields.Selection(related='question_id.question_type')
    survey_id = fields.Many2one('survey.survey', string='Survey')
    ignore_survey_evaluation = fields.Boolean(related='survey_id.ignore_survey_evaluation', string='Ignore Survey Evaluation')
    survey_name = fields.Char(related='survey_id.title')
    applicant_id = fields.Many2one('hr.applicant', string='Applicant')
    matrix_row_id = fields.Many2one('survey.question.answer', string="Row answer")
    matrix_input = fields.Char(related='matrix_row_id.value')
    interviewer_answer_ids = fields.One2many('survey.interviewer', 'custom_questions_id', string='Interviewers Answers', compute='get_interviewer_answers')

    @api.onchange('applicant_id', 'question_id')
    def create_personality_trait(self):
        for rec in self:
            print(rec)

    # @api.depends('applicant_id.survey_user_input_ids', 'survey_id')
    def get_interviewer_answers(self):
        obj_unlink = self.env['survey.interviewer'].search([])
        obj_unlink.unlink()
        for rec in self:
            obj_main = self.env['survey.interviewer']
            participants = self.env['survey.user_input'].search(
                [('survey_id', '=', rec.survey_id.id), ('applicant_id', '=', rec.applicant_id.id)])
            interviewer_list = []
            for result in participants:
                for user_input in result.user_input_line_ids.filtered(lambda r: r.question_id.id == rec.question_id.id and r.matrix_row_id.id == rec.matrix_row_id.id):
                    if user_input.suggested_answer_id.value.isdigit():
                        score = int(user_input.suggested_answer_id.value)
                    else:
                        for value in user_input.suggested_answer_id.value.split(' '):
                            if value.isdigit():
                                score = int(value)
                    values = {
                        'custom_questions_id': rec.id,
                        'score': float(score),
                        'partner': result.active_interviewer_id.id,
                    }
                    interviewer_list.append([0, 0, values])
                    obj = self.env['survey.interviewer'].create(values)
                    obj_main += obj
                    print(values)
            if interviewer_list:
                rec.interviewer_answer_ids = obj_main
            else:
                rec.interviewer_answer_ids = False

    average_of_suggestion = fields.Float(string='Average', compute='get_average_of_suggestion')

    def get_average_of_suggestion(self):
        # self.average_of_suggestion = 0.0
        y = 0
        for rec in self:
            participants = self.env['survey.user_input'].search(
                [('survey_id', '=', rec.survey_id.id), ('applicant_id', '=', rec.applicant_id.id)])
            input_values = 0
            for result in participants:
                for user_input in result.user_input_line_ids.filtered(lambda r: r.question_id.id == rec.question_id.id and r.matrix_row_id.id == rec.matrix_row_id.id):
                    if user_input.suggested_answer_id.value.isdigit():
                        input_values += int(user_input.suggested_answer_id.value)
                    else:
                        for value in user_input.suggested_answer_id.value.split(' '):
                            if value.isdigit():
                                input_values += int(value)

            if participants:
                rec.average_of_suggestion = input_values / len(participants) or 0.0


            # if rec.question_id.question_type == 'matrix':
            #     user_input_matrix = rec.user_input_id.user_input_line_ids.filtered(
            #         lambda r: r.question_id.id == rec.question_id.id)
            #     # suggested_ans_sum = sum(int(user_input_matrix.suggested_answer_id.value))
            #     suggested_ans_sum = 0
            #     for line in user_input_matrix:
            #         suggested_ans_sum += int(line.suggested_answer_id.value)
            #     matrix_length = len(rec.question_id.matrix_row_ids)
            #     average = suggested_ans_sum / matrix_length
            #     rec.average_of_suggestion = average
            #     print(average)
            else:
                rec.average_of_suggestion = 0.0

    # proposed_contracts = fields.Many2many('hr.contract', string="Proposed Contracts", domain="[('company_id', '=', company_id)]")

    # class sourcing_referrals(models.Model):
    #     _name = 'sourcing.referrals'
    #     _description = 'sourcing.referrals'
    #
    #     sourcing = fields.Many2one('res.partner',string='Sourcing')
    #     referrals = fields.Many2one('res.partner',string='Referrals')
    #     job_id = fields.Many2one('hr.job',string='Job')
