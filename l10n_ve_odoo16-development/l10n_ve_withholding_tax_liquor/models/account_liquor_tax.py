# -*- coding: utf-8 -*-

from odoo import fields, models

class AccountLiquorTax(models.Model):
	_name = "account.liquor.tax"
	_description = "Impuesto al licor"

	name = fields.Char(string='Nombre del impuesto', required=True)
	rate = fields.Float(string='Porcentaje', digits=(5,2))

	_sql_constraints = [
		('check_rate', 'CHECK(rate > 0 AND rate <= 100)', 'El importe debe estar en un rango mayor a 0 y menor o igual a 100.'),
	]