# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Department(models.Model):
	_inherit = "hr.department"
	
	generate_commissions = fields.Boolean(string="Generate commissions")