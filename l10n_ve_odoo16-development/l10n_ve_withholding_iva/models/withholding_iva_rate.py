# -*- coding: utf-8 -*-

from odoo import models, fields

class WithholdingIvaRate(models.Model):
	_name = "withholding.iva.rate"
	_description = "Tasa de retención de IVA"

	name = fields.Float(string='Tasa')
	description = fields.Char(string='Descripción')

	_sql_constraints = [('check_percentage', 'CHECK(name > 0 AND name <= 100)', 'La tasa de retención de IVA debe ser mayor a cero y menor o igual a 100.')]

	def name_get(self):
		return [(rate.id, f'{rate.name}%') for rate in self]