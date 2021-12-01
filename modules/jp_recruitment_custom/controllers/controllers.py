# -*- coding: utf-8 -*-
import pdb

from odoo import http
from odoo.addons.survey.controllers.main import Survey
import json
import logging
import werkzeug

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import fields, http, _
from odoo.addons.base.models.ir_ui_view import keep_query
from odoo.exceptions import UserError
from odoo.http import request, content_disposition
from odoo.osv import expression


class SurveyInherit(Survey):

    @http.route('/survey/submit/<string:survey_token>/<string:answer_token>', type='json', auth='public', website=True)
    def survey_submit(self, survey_token, answer_token, **post):
        """ Submit a page from the survey.
        This will take into account the validation errors and store the answers to the questions.
        If the time limit is reached, errors will be skipped, answers will be ignored and
        survey state will be forced to 'done'"""
        # Survey Validation
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=True)
        if access_data['validity_code'] is not True:
            return {'error': access_data['validity_code']}
        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']

        if answer_sudo.state == 'done':
            return {'error': 'unauthorized'}

        questions, page_or_question_id = survey_sudo._get_survey_questions(answer=answer_sudo,
                                                                           page_id=post.get('page_id'),
                                                                           question_id=post.get('question_id'))

        if not answer_sudo.test_entry and not survey_sudo._has_attempts_left(answer_sudo.partner_id, answer_sudo.email,
                                                                             answer_sudo.invite_token):
            # prevent cheating with users creating multiple 'user_input' before their last attempt
            return {'error': 'unauthorized'}

        if answer_sudo.survey_time_limit_reached or answer_sudo.question_time_limit_reached:
            if answer_sudo.question_time_limit_reached:
                time_limit = survey_sudo.session_question_start_time + relativedelta(
                    seconds=survey_sudo.session_question_id.time_limit
                )
                time_limit += timedelta(seconds=3)
            else:
                time_limit = answer_sudo.start_datetime + timedelta(minutes=survey_sudo.time_limit)
                time_limit += timedelta(seconds=10)
            if fields.Datetime.now() > time_limit:
                # prevent cheating with users blocking the JS timer and taking all their time to answer
                return {'error': 'unauthorized'}

        errors = {}
        # Prepare answers / comment by question, validate and save answers
        inactive_questions = request.env[
            'survey.question'] if answer_sudo.is_session_answer else answer_sudo._get_inactive_conditional_questions()
        for question in questions:
            if question in inactive_questions:  # if question is inactive, skip validation and save
                continue
            answer, comment = self._extract_comment_from_answers(question, post.get(str(question.id)))
            errors.update(question.validate_question(answer, comment))
            if not errors.get(question.id):
                answer_sudo.save_lines(question, answer, comment)

        if errors and not (answer_sudo.survey_time_limit_reached or answer_sudo.question_time_limit_reached):
            return {'error': 'validation', 'fields': errors}

        if not answer_sudo.is_session_answer:
            answer_sudo._clear_inactive_conditional_answers()

        if answer_sudo.survey_time_limit_reached or survey_sudo.questions_layout == 'one_page':
            answer_sudo._mark_done()
        elif 'previous_page_id' in post:
            # Go back to specific page using the breadcrumb. Lines are saved and survey continues
            return self._prepare_question_html(survey_sudo, answer_sudo, **post)
        else:
            vals = {'last_displayed_page_id': page_or_question_id}
            if not answer_sudo.is_session_answer:
                next_page = survey_sudo._get_next_page_or_question(answer_sudo, page_or_question_id)
                if not next_page:
                    answer_sudo._mark_done()

            answer_sudo.write(vals)

        #Silverdale tech : T3000
        if answer_sudo and answer_sudo.applicant_id and len(answer_sudo.applicant_id)<2:
            personality_dict = {}
            # check_user_input = len(request.env['survey.user_input.line'].sudo().search(
            #     [('applicant_id', '=', answer_sudo.applicant_id.id),
            #      ('ignore_survey_evaluation', '=', True)]))
            # if check_user_input > 1:
            #     raise UserError(_("You can only attempt one Personality survey."))
            # if check_user_input == 1:
            user_input = request.env['survey.user_input.line'].sudo().search([('applicant_id', '=', answer_sudo.applicant_id.id),
                                                                           ('ignore_survey_evaluation','=',True)])

            for user_answer in user_input:
                question = user_answer.question_id

                if question.title.find('A1:')!=-1:
                    personality_dict['accommodating'] = user_answer.average_of_suggestion
                if question.title.find('A2:')!=-1:
                    personality_dict['innovative'] = user_answer.average_of_suggestion

                if question.title.find('B1:')==-1:
                    personality_dict['introspective'] = user_answer.average_of_suggestion
                if question.title.find('B2:')!=-1:
                    personality_dict['social'] = user_answer.average_of_suggestion
                if question.title.find('C1:')!=-1:
                    personality_dict['urgency'] = user_answer.average_of_suggestion
                if question.title.find('C2:')!=-1:
                    personality_dict['stability'] = user_answer.average_of_suggestion
                if question.title.find('D1:')!=-1:
                    personality_dict['non_conforming'] = user_answer.average_of_suggestion
                if question.title.find('D2:')!=-1:
                    personality_dict['conforming'] = user_answer.average_of_suggestion
                if question.title.find('L:')!=-1:
                    personality_dict['emotion_logic'] = user_answer.average_of_suggestion
                if question.title.find('I:')!=-1:
                    personality_dict['ingenuity'] = user_answer.average_of_suggestion

                if personality_dict:
                    partner = answer_sudo.applicant_id.partner_id
                    for rec in partner:
                        personality_dict['partner_id'] = rec.id
                        personality = request.env['personality.main'].search([('partner_id','=',rec.id)])
                        if not personality:
                            personality = personality.sudo().create(personality_dict)
                            personality.sudo().write({'applicant_id':answer_sudo.applicant_id.id})
                        else:
                            personality.sudo().write(personality_dict)
                            personality.sudo().write({'applicant_id': answer_sudo.applicant_id.id})

        # pdb.set_trace()

        return self._prepare_question_html(survey_sudo, answer_sudo)

