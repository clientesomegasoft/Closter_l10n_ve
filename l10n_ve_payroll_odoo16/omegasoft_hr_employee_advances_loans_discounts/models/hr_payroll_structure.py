# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class HrPayslip(models.Model):
    _name = 'hr.payroll.structure'
    _inherit = ['hr.payroll.structure', 'mail.thread', 'mail.activity.mixin']


    is_loan_discount = fields.Boolean("Is loan and Discount", default=False, tracking=True)