# -*- coding: utf-8 -*-
import pdb

from odoo import models, fields, api, _
from pytz import timezone
from datetime import datetime


class CellHolidays(models.Model):
    _name = 'cell.holidays'
    _description = 'Global and Custom Holiday'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Holiday')
    date = fields.Date(string="Date", default=fields.Date.today)
    day = fields.Char(string="Day")

    @api.onchange('date')
    def _compute_day_of_the_week(self):
        if self.date:
            day = self.date.weekday()
            if day == 0:
                self.day = 'Monday'
            elif day == 1:
                self.day = 'Tuesday'
            elif day == 2:
                self.day = 'Wednesday'
            elif day == 3:
                self.day = 'Thursday'
            elif day == 4:
                self.day = 'Friday'
            elif day == 5:
                self.day = 'Saturday'
            else:
                self.day = 'Sunday'
