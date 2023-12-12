# -*- coding: utf-8 -*-

from odoo import models, fields

class ResConfigSettings(models.TransientModel):
	_inherit = "res.config.settings"

	overtime_category_ids = fields.Many2many(related='company_id.overtime_category_ids', readonly=False)
	withholdig_category_ids = fields.Many2many(related='company_id.withholdig_category_ids', readonly=False)
	withholdig_rule_ids = fields.Many2many(related='company_id.withholdig_rule_ids', readonly=False)
	wage_received_category_ids = fields.Many2many(related='company_id.wage_received_category_ids', readonly=False)
	wage_received_rule_ids = fields.Many2many(related='company_id.wage_received_rule_ids', readonly=False)

class ResCompany(models.Model):
	_inherit = "res.company"

	overtime_category_ids = fields.Many2many('hr.salary.rule.category', 'overtime_hr_category_rel', string='Categorias horas extras laborales')
	withholdig_category_ids = fields.Many2many('hr.salary.rule.category', 'withholding_hr_category_rel', string='Categorias impuestos retenidos')
	withholdig_rule_ids = fields.Many2many('hr.salary.rule', 'withholding_hr_rule_rel', string='Reglas impuestos retenidos', domain="[('category_id', 'in', withholdig_category_ids)]")
	wage_received_category_ids = fields.Many2many('hr.salary.rule.category', 'wage_recieved_hr_category_rel', string='Categorias remuneraciones recibidas')
	wage_received_rule_ids = fields.Many2many('hr.salary.rule', 'wage_recieved_hr_rule_rel', string='Reglas remuneraciones recibidas', domain="[('category_id', 'in', wage_received_category_ids)]")