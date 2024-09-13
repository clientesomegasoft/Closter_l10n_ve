# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrContract(models.Model):
    _inherit = 'hr.contract'

    recent_resets = fields.Date("recent calculation for reset utility")
    
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    wage_type = fields.Selection(related="contract_id.wage_type")
    average_wage = fields.Monetary(related="contract_id.average_wage")
