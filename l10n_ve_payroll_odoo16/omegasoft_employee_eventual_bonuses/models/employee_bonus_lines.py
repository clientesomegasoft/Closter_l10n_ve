# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime


class HrEmployeeBonusLine(models.Model):
    _name = 'hr_employee_bonus_line'
    _description = 'Employee bonus line'
    _order = 'bonus_id desc, employee_bonus_amount desc'

    name = fields.Selection(
        related='bonus_id.name'
    )

    description = fields.Char(related='bonus_id.description')

    active = fields.Boolean(
        default=True, help="Set active to false to hide the children tag without removing it.")

    bonus_id = fields.Many2one(
        string='Bonus',
        comodel_name='hr_employee_bonus',
        ondelete='restrict',
    )

    employee_id = fields.Many2one(string='Employee',comodel_name='hr.employee',ondelete='restrict')

    employee_bonus_amount = fields.Float(string='Employee bonus amount',)
