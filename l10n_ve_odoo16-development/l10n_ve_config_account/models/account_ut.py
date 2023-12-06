# -*- coding: utf-8 -*-

from odoo import fields, models, api

class AccountUT(models.Model):
	_name = "account.ut"
	_description = "Unidad Tributaria"
	_order = "date desc"

	name = fields.Char(string='Número de referencia', required=True, help="Número de referencia según la ley.")
	date = fields.Date(string='Fecha', required=True, help="Fecha en la que entra en vigor la nueva unidad tributaria.")
	amount = fields.Float(string='Monto')

	_sql_constraints = [('check_amount', 'CHECK(amount > 0)', 'El monto de la unidad tributaria debe ser mayo a cero (0).')]

	@api.model
	def get_current_ut(self):
		return self.search([('date', '<=', fields.Date.today())], limit=1)