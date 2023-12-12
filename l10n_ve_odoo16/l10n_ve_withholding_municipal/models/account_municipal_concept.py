# -*- coding: utf-8 -*-

from odoo import fields, models

class AccountMunicioalConcept(models.Model):
	_name = "account.municipal.concept"
	_description = "Concepto de retencion municipal"

	name = fields.Char(string='Nombre de concepto', required=True)
	rate = fields.Float(string='% Retención', digits=(5,2))

	_sql_constraints = [
		('check_rate', 'CHECK(rate > 0 AND rate <= 100)', 'El porcentaje de retención debe estar en un rango mayor a 0 y menor o igual a 100.'),
	]