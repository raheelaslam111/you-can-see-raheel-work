from odoo import _, api, fields, models
import pdb



class HrAppraisal(models.Model):
    _inherit = "hr.appraisal"


    active = fields.Boolean(default=True)
    core_evaluation_ids = fields.One2many('core.evaluation','appraisal_id',string='Core Evaluations',ondelete='cascade')
    core_evaluation_numbers = fields.Integer(string='Core Evaluation',compute='get_core_evaluation_no')


    def get_core_evaluation_no(self):
        for rec in self:
            rec.core_evaluation_numbers = len(rec.core_evaluation_ids) or 0


    def action_open_core_evaluation(self):
        list_ids = []
        for line in self.core_evaluation_ids:
            list_ids.append(line.id)
        form_view = self.env.ref('appraisal_core_evaluation.core_evaluation_view_form')
        tree_view = self.env.ref('appraisal_core_evaluation.core_evaluation_view_tree')
        return {
            'domain': [('id', 'in', list_ids)],
            'name': _('Core Evaluation'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'core.evaluation',
            'view_id': False,
            'views': [(tree_view and tree_view.id or False, 'tree'),
                      (form_view and form_view.id or False, 'form')],
            'context': {'default_appraisal_id': self.id},
            'type': 'ir.actions.act_window'
        }




class CoreEvaluation(models.Model):
    _name = "core.evaluation"
    _description = "core evaluation"
    _rec_name = 'appraisal_id'


    get_it = fields.Selection([('1','1'),
                               ('2','2'),
                               ('3','3'),
                               ('4','4'),
                               ('5','5')],string='Get It')
    get_it_color = fields.Selection([
        ('below', 'below'),
        ('equal', 'equal'),
        ('above', 'above')
    ], string='color', compute='get_colour_value')
    get_it_bg_color = fields.Boolean(string='bg_color', compute='get_colour_value')
    get_it_white_color = fields.Boolean(string='white_color', compute='get_colour_white')
    want_it = fields.Selection([('1','1'),
                                ('2','2'),
                               ('3','3'),
                               ('4','4'),
                               ('5','5')],string='Want It')
    want_it_color = fields.Selection([
        ('below', 'below'),
        ('equal', 'equal'),
        ('above', 'above')
    ], string='color', compute='get_colour_value')
    want_it_bg_color = fields.Boolean(string='bg_color', compute='get_colour_value')
    want_it_white_color = fields.Boolean(string='white_color', compute='get_colour_white')
    capacity_emotional = fields.Selection([('1','1'),
                               ('2','2'),
                               ('3','3'),
                               ('4','4'),
                               ('5','5')],
                                string='Capacity: Emotional')
    capacity_emotional_color = fields.Selection([
        ('below', 'below'),
        ('equal', 'equal'),
        ('above', 'above')
    ], string='color', compute='get_colour_value')
    capacity_emotional_bg_color = fields.Boolean(string='bg_color', compute='get_colour_value')
    capacity_emotional_white_color = fields.Boolean(string='white_color', compute='get_colour_white')
    capacity_intellectual = fields.Selection([('1', '1'),
                                           ('2', '2'),
                                           ('3', '3'),
                                           ('4', '4'),
                                           ('5', '5')],
                                          string='Capacity: Intellectual')
    capacity_intellectual_color = fields.Selection([
        ('below', 'below'),
        ('equal', 'equal'),
        ('above', 'above')
    ], string='color', compute='get_colour_value')
    capacity_intellectual_bg_color = fields.Boolean(string='bg_color', compute='get_colour_value')
    capacity_intellectual_white_color = fields.Boolean(string='white_color', compute='get_colour_white')
    capacity_physical = fields.Selection([('1', '1'),
                                           ('2', '2'),
                                           ('3', '3'),
                                           ('4', '4'),
                                           ('5', '5')],
                                          string='Capacity: Physical')
    capacity_physical_color = fields.Selection([
        ('below', 'below'),
        ('equal', 'equal'),
        ('above', 'above')
    ], string='color', compute='get_colour_value')
    capacity_physical_bg_color = fields.Boolean(string='bg_color', compute='get_colour_value')
    capacity_physical_white_color = fields.Boolean(string='white_color', compute='get_colour_white')
    capacity_time = fields.Selection([('1', '1'),
                                           ('2', '2'),
                                           ('3', '3'),
                                           ('4', '4'),
                                           ('5', '5')],
                                          string='Capacity: Time')
    capacity_time_color = fields.Selection([
        ('below', 'below'),
        ('equal', 'equal'),
        ('above', 'above')
    ], string='color', compute='get_colour_value')
    capacity_time_bg_color = fields.Boolean(string='bg_color', compute='get_colour_value')
    capacity_time_white_color = fields.Boolean(string='white_color', compute='get_colour_white')
    appraisal_id = fields.Many2one('hr.appraisal',string='Employee')
    # color = fields.Selection([
    #     ('below', 'below'),
    #     ('equal', 'equal'),
    #     ('above', 'above')
    # ], string='color', compute='get_colour_value')
    bg_color = fields.Boolean(string='bg_color', compute='get_colour_value')
    white_color = fields.Boolean(string='white_color', compute='get_colour_white')



    def get_colour_white(self):
        for rec in self:
            if int(rec.get_it) == 3:
                rec.get_it_white_color = True
            else:
                rec.get_it_white_color = False

            if int(rec.want_it) == 3:
                rec.want_it_white_color = True
            else:
                rec.want_it_white_color = False

            if int(rec.capacity_emotional) == 3:
                rec.capacity_emotional_white_color = True
            else:
                rec.capacity_emotional_white_color = False

            if int(rec.capacity_intellectual) == 3:
                rec.capacity_intellectual_white_color = True
            else:
                rec.capacity_intellectual_white_color = False

            if int(rec.capacity_physical) == 3:
                rec.capacity_physical_white_color = True
            else:
                rec.capacity_physical_white_color = False

            if int(rec.capacity_time) == 3:
                rec.capacity_time_white_color = True
            else:
                rec.capacity_time_white_color = False
            # pdb.set_trace()



    def get_colour_value(self):
        for rec in self:
            if int(rec.get_it) > 3:
                rec.get_it_color = 'above'
                rec.get_it_bg_color = True
            elif int(rec.get_it) < 3:
                rec.get_it_color = 'below'
                rec.get_it_bg_color = False
            else:
                rec.get_it_color = 'equal'
                rec.get_it_bg_color = False
                # rec.white_color = True

            if int(rec.want_it) > 3:
                rec.want_it_color = 'above'
                rec.want_it_bg_color = True
            elif int(rec.want_it) < 3:
                rec.want_it_color = 'below'
                rec.want_it_bg_color = False
            else:
                rec.want_it_color = 'equal'
                rec.want_it_bg_color = False
                # rec.white_color = True

            if int(rec.capacity_emotional) > 3:
                rec.capacity_emotional_color = 'above'
                rec.capacity_emotional_bg_color = True
            elif int(rec.capacity_emotional) < 3:
                rec.capacity_emotional_color = 'below'
                rec.capacity_emotional_bg_color = False
            else:
                rec.capacity_emotional_color = 'equal'
                rec.capacity_emotional_bg_color = False
                # rec.white_color = True

            if int(rec.capacity_intellectual) > 3:
                rec.capacity_intellectual_color = 'above'
                rec.capacity_intellectual_bg_color = True
            elif int(rec.capacity_intellectual) < 3:
                rec.capacity_intellectual_color = 'below'
                rec.capacity_intellectual_bg_color = False
            else:
                rec.capacity_intellectual_color = 'equal'
                rec.capacity_intellectual_bg_color = False
                # rec.white_color = True

            if int(rec.capacity_physical) > 3:
                rec.capacity_physical_color = 'above'
                rec.capacity_physical_bg_color = True
            elif int(rec.capacity_physical) < 3:
                rec.capacity_physical_color = 'below'
                rec.capacity_physical_bg_color = False
            else:
                rec.capacity_physical_color = 'equal'
                rec.capacity_physical_bg_color = False
                # rec.white_color = True

            if int(rec.capacity_time) > 3:
                rec.capacity_time_color = 'above'
                rec.capacity_time_bg_color = True
            elif int(rec.capacity_time) < 3:
                rec.capacity_time_color = 'below'
                rec.capacity_time_bg_color = False
            else:
                rec.capacity_time_color = 'equal'
                rec.capacity_time_bg_color = False
                # rec.white_color = True
            # pdb.set_trace()


    # def assign_color(self,field=):
    #     for rec in self:
    #         if int(field) > 3:
    #             rec.color = 'above'
    #             rec.bg_color = True
    #         elif int(field) < 3:
    #             rec.color = 'below'
    #             rec.bg_color = False
    #         else:
    #             rec.color = 'equal'
    #             rec.bg_color = False
    #             rec.white_color = True

