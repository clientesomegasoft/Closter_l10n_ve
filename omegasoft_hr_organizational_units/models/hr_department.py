# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Department(models.Model):
    _inherit = "hr.department"
    
    organizational_units_ids = fields.Many2many('hr.organizational.units', string='organizational units', domain="[('company_id', '=', company_id)]")
    active_organizational_units = fields.Boolean(string='active organizational units', related='company_id.active_organizational_units')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=False)
    code = fields.Char(related = "analytic_account_id.code", string="code")