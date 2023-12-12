# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HrContract(models.Model):
    _inherit = 'hr.contract'

    structure_loan_discount = fields.Many2one('hr.payroll.structure',  string="Structure Loan and Discount")
