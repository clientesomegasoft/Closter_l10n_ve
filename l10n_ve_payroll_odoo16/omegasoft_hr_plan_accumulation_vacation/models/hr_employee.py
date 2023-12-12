# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    history_ids = fields.One2many('hr_plan_accumulation.history', 'employee_id', string='Accumulated', domain = [('state', 'in', ['draft', 'confirm', 'refuse', 'validate1', 'validate'])])