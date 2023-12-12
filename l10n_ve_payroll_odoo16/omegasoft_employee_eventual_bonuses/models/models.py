# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo.exceptions import UserError, ValidationError


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'
    

    bonus_line_ids = fields.One2many(
        string='bonus lines',
        comodel_name='hr_employee_bonus_line',
        inverse_name='employee_id',
    )