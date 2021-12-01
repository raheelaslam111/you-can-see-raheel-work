import pdb
from odoo import api, fields, models, _


class HrJob(models.Model):
    _inherit = "hr.job"

    AVAILABLE_PRIORITIES = [
        ('0', 'Normal'),
        ('1', 'Good'),
        ('2', 'Very Good'),
        ('3', 'Excellent')
    ]

    job_type = fields.Selection([('employee', 'Employee'), ('ic', 'IC')
                                    , ('partner', 'Partner')
                                    , ('vendor', 'Vendor'),
                                 ('other', 'Other'), ], string='Job Type')
    hiring_team_id = fields.Many2one('hr.department', string='Hiring Team')
    position_history = fields.Text(string='Position History',
                                   help="Briefly describe the incumbant's pro's and con's and how the chosen applicant can do better")
    description = fields.Html(string='Description')
    native_genius = fields.Text(string='Native Genius', help="Native Genius.")
    appraisal_count = fields.Integer(string='Appraisal Count', compute='count_appraisal')
    # Existing field only defind here for apply help
    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department', help='Team')
    # Existing field only defind here for apply help
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Sourcing Mrg',
        help="Recruiter",
        required=False)

    # for "Skills & EXP" tab
    soft_skill_ids = fields.Many2many('vgwcs.vgwcs', string='Soft Skills')
    experience = fields.Html(string='Experience')

    # fields for goal/kpi tab
    career_path = fields.Html(string='Career Path')
    onboarding_plan = fields.Html(string='Onboarding Plan')

    # fields for comp tab
    comp_benefits_perks = fields.Html(string='Comp/Benefits/Perks')
    comp_benefits_perks_internal_notes = fields.Html(string='Comp/Benefits/Perks Internal Notes')

    # fields for Intake/Sourcing/Referrals tab
    sourcing_referrals_ids = fields.One2many('sourcing.referrals', 'job_id', string='Sourcing Referrals')

    priority = fields.Selection(AVAILABLE_PRIORITIES, "Priority", default='0')

    tags_ids = fields.Many2many('res.partner.category', string="Tags")

    interview_survey_dict_ids = fields.Many2many('interview.survey.dictionary', string='Interview Survey Dictionary')
    questionare_survey_dict_ids = fields.Many2many('questionare.survey.dictionary', string='Questionnaire Survey Dictionary')
    co_intro_job_posting = fields.Html(string='Co Intro on Job Posting')

    def get_all_related_recruitment_intro(self):
        accoutibility_records = self.env['accountability.accountability']
        accountibility = self.env['accountability.accountability'].search([])
        for acc in accountibility:
            if self.id in acc.job_ids.ids:
                accoutibility_records += acc
        return accoutibility_records

    def count_appraisal(self):
        appraisal = len(self.env['hr.appraisal'].search([('job_id', '=', self.id)]))
        self.appraisal_count = appraisal

    def action_appraisal_jobs_rel(self):
        appraisal = self.env['hr.appraisal'].search([('job_id', '=', self.id)]).mapped('id')

        return {
            'domain': [('id', 'in', appraisal)],
            'name': _('Appraisal'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.appraisal',
            'view_id': False,
            # 'views': [(self.env.ref('	hr_appraisal.view_hr_appraisal_tree').id, 'tree'),
            #           (self.env.ref('hr_appraisal.view_hr_appraisal_form').id, 'form')],
            # 'context': {'default_class_id': self.id},
            'type': 'ir.actions.act_window'
        }

    class QuestionareSurveyDictionary(models.Model):
        _name = 'questionare.survey.dictionary'
        _description = 'Questionnaire survey dictionary'

        recruitment_stage_id = fields.Many2one('hr.recruitment.stage', string='Stage', required=True)
        survey_id = fields.Many2one('survey.survey', string='Survey', required=True)

    class InterviewSurveyDictionary(models.Model):
        _name = 'interview.survey.dictionary'
        _description = 'interview survey dictionary'

        recruitment_stage_id = fields.Many2one('hr.recruitment.stage', string='Stage', required=True)
        survey_id = fields.Many2one('survey.survey', string='Survey', required=True)

    class VGWCS(models.Model):
        _name = 'vgwcs.vgwcs'
        _description = 'soft skills VGWCS'

        attribute = fields.Char(string='Attribute')
        description = fields.Char(string='Description')
        attribute_type = fields.Char(string='Attribute Type')
        critical = fields.Char(string='Critical')
        category = fields.Char(string='Category')
        changeability = fields.Char(string='Changeability')

    class sourcing_referrals(models.Model):
        _name = 'sourcing.referrals'
        _description = 'sourcing.referrals'

        sourcing = fields.Many2one('res.partner', string='Sourcing')
        referrals = fields.Many2one('res.partner', string='Referrals')
        job_id = fields.Many2one('hr.job', string='Job')
