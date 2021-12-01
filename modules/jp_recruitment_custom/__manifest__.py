##############################################################################
{
    'name': 'Job Position Applicants Survey Recruitment',
    'version': '14.1.002',
    'author': 'silverdale',
    'website': 'www.silverdaletech.com',
    'category': 'hr_recruitment',
    'license': 'AGPL-3',
    'sequence': 15,
    'summary': 'customization in recruitment module and survey module',
    'images': [],
    'depends': ['hr_recruitment', 'propertyworx_ext', 'hr_appraisal', 'website_hr_recruitment', 'survey', 'survey_personality'],
    'description': """
	Sprint: 2116,
        Tasks: T2878,H1056,T2856 ,T3259,H1155,,H1050,T3306,T3000,T3811,T3805,T3802,T3894,T3893,H1854,H2324,T4513,T4458,T4512
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/job_position_inherit.xml',
        'views/job_detail_template_inherit.xml',
        'views/application_recruitment_inherit.xml',
        'views/survey_options_inherit.xml',
        'views/questionnaire_survey_dictionary_view.xml',
    ],
    # 'qweb': [
    #     "static/src/xml/reset_to_draft.xml",
    # ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
