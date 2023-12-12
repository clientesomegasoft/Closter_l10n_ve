# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
class HrContractHistory(models.Model):
    _inherit = 'hr.contract.history'

    employee_file = fields.Boolean('Employee file', related="employee_id.company_id.employee_file")
    employee_file_code_id = fields.Many2one('employee.file.code', string='Employee File Code', related="employee_id.employee_file_code_id")