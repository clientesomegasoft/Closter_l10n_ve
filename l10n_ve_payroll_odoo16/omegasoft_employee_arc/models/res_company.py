# -*- coding: UTF-8 -*-

from odoo import models, fields

class ResCompany(models.Model):
	_inherit = "res.company"

	withholding_officer_id = fields.Many2one('hr.employee', string='Funcionario de retención')
	islr_agent_number = fields.Char(string='Nro de contribuyente')
	arc_template_id = fields.Many2one('mail.template', 'Use template',domain="[('model', '=', 'employee.arc.report.wizard')]")
	