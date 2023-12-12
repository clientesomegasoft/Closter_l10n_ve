
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import re

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    family_information_ids = fields.One2many(comodel_name='hr_employee_family_information', inverse_name='employee_id', string="Famyli informarion")