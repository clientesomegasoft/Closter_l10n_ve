
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class HrJob(models.Model):
    _inherit = 'hr.job'
    
    organizational_units_id = fields.Many2one('hr.organizational.units', string='organizational units', domain="[('company_id', '=', company_id)]")
    active_organizational_units = fields.Boolean(string='active organizational units', related='company_id.active_organizational_units')
    department_id = fields.Many2one('hr.department', 'Department', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    