import pdb
from odoo import api, fields, models, _


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant')
    ignore_survey_evaluation = fields.Boolean(string='Ignore Survey Evaluation')
    is_applicant_questionare = fields.Boolean(string='Applicant Questionare')

    # def write(self, vals):
    #
    #     print(vals)
    #     res = super(SurveySurvey, self).write(vals)
    #     if res.state == 'closed':
    #         res.user_input_ids
    #     return res


class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input.line'

    applicant_id = fields.Many2one(related='user_input_id.applicant_id', string='Applicant', store=True, readonly=False)
    average_of_suggestion = fields.Float(string='Average', compute='get_average_of_suggestion')
    ignore_survey_evaluation = fields.Boolean(related='survey_id.ignore_survey_evaluation',string='Ignore Survey Evaluation')
    is_applicant_questionare = fields.Boolean(related='survey_id.is_applicant_questionare',string='Applicant Questionare')

    def get_average_of_suggestion(self):
        for rec in self:
            if rec.question_id.question_type == 'matrix':
                user_input_matrix = rec.user_input_id.user_input_line_ids.filtered(
                    lambda r: r.matrix_row_id.id == rec.matrix_row_id.id)
                # suggested_ans_sum = sum(int(user_input_matrix.suggested_answer_id.value))
                suggested_ans_sum = 0
                for line in user_input_matrix:
                    suggested_ans_sum += int(line.suggested_answer_id.value)
                    matrix_length = len(rec.question_id.matrix_row_ids)
                average = suggested_ans_sum / matrix_length
                rec.average_of_suggestion = average
                print(average)
            else:
                rec.average_of_suggestion = 0.0

    @api.model
    def create(self, vals):
        res = super(SurveyUserInputLine, self).create(vals)
        if res.survey_id.is_applicant_questionare == True:
                obj_main = self.env['questionare.questions']
                obj_questions = self.env['questionare.questions'].search(
                    [('survey_user_input_line_id', '=', res.id), ('question_id', '=', res.question_id.id),
                     ('applicant_id', '=', res.applicant_id.id)])
                if not obj_questions and res.answer_type in ['text_box','char_box']:
                    values = {
                        'question_id': res.question_id.id,
                        'value_text_box': res.value_text_box,
                        'applicant_id': res.applicant_id.id,
                        'survey_id': res.survey_id.id,
                    }
                    obj = self.env['questionare.questions'].create(values)
                    obj_main += obj
        return res


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    applicant_id = fields.Many2one('hr.applicant', string='Applicant')
    ignore_survey_evaluation = fields.Boolean(related='survey_id.ignore_survey_evaluation',string='Ignore Survey Evaluation')
    survey_state = fields.Selection(related='survey_id.state')
    active_interviewer_id = fields.Many2one('res.users',string='Interviwer' ,store=True)
    # survey_questions_ids = fields.One2many('custom.questions','user_input_id',compute='map_survey_questions',string='Survey Questions',ondelete='cascade')

    @api.model
    def create(self, vals):
        if vals.get('survey_id') and vals.get('partner_id'):
            print(vals['survey_id'])

            survey = self.env['survey.survey'].search([('id', '=', vals['survey_id'])], limit=1)
            partner = self.env['res.partner'].search([('id', '=', vals['partner_id'])], limit=1)
            applicant = self.env['hr.applicant'].search(
                [('survey_id', '=', survey.id), ('partner_id', '=', partner.id)], limit=1)
            vals['applicant_id'] = applicant.id
        res = super(SurveyUserInput, self).create(vals)
        res.active_interviewer_id = self.env.uid
        if res.survey_id.ignore_survey_evaluation == False and res.survey_id.is_applicant_questionare == False:
            questions = res.survey_id.question_and_page_ids.filtered(lambda r: r.is_page == False)

            if questions:
                questions = questions.filtered(lambda r: r.question_type == 'matrix')
                obj_main = self.env['custom.questions']
                for line in questions:
                    for matrix in line.matrix_row_ids:
                        obj_questions = self.env['custom.questions'].search(
                            [('matrix_row_id', '=', matrix.id), ('question_id', '=', line.id),
                             ('applicant_id', '=', res.applicant_id.id)])
                        if not obj_questions:
                            print(res.id)
                            values = {
                                'question_id': line.id,
                                'matrix_row_id': matrix.id,
                                'applicant_id': res.applicant_id.id,
                                'survey_id': res.survey_id.id,
                            }
                            obj = self.env['custom.questions'].create(values)
                            print(obj)
                            obj_main += obj
            # res.applicant_id.survey_user_input_ids = obj_main
            # print(res.applicant_id.survey_user_input_ids)
        return res


class Applicant(models.Model):
    _inherit = "hr.applicant"

    applicant_ids = fields.One2many('survey.user_input', 'applicant_id', 'Applicants')
    survey_ids = fields.One2many('survey.survey', 'applicant_id', 'Surveys')
