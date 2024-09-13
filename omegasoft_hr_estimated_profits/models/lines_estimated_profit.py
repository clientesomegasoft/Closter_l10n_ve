# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class LineEstimatedProfit(models.Model):
    _name = 'hr.estimated.profit'
    _description = 'Calculation estimated profit'

    payroll_structure_type = fields.Many2one('hr.payroll.structure.type', string="Structure type",ondelete='restrict')
    structure_type_default_schedule_pay = fields.Selection(related='payroll_structure_type.default_schedule_pay')
    salary_rule_category = fields.Many2many('hr.salary.rule.category', string="Categories of wage rules",ondelete='restrict')
    average_days = fields.Float(string="Average days")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company,ondelete='restrict')

    # @api.constrains('average_days')
    # def _check_average_days(self):
    #     for record in self:
    #         if record.average_days <= 0 and record.structure_type_default_schedule_pay == 'monthly':
    #             raise ValidationError('El promedio de días debe ser superior a cero.')