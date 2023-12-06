# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class AccountISLRConcept(models.Model):
	_name = "account.islr.concept"
	_description = "Concepto de ISLR"
	_order = "name"

	name = fields.Char(string='Nombre de concepto', required=True)
	rate_ids = fields.One2many('account.islr.concept.rate', 'islr_concept_id', string='Tasas')

	def get_concept_rate(self, person_type_id, base_ut):
		self.ensure_one()

		rate_id = self.rate_ids.filtered(lambda l: l.person_type_id.id == person_type_id.id)
		if not rate_id:
			raise ValidationError(f'No se encontro tasa de retención de ISLR.\n\nTipo: {person_type_id.name}\nConcepto: {self.name}')

		if not rate_id.rate_type:
			rate = rate_id.rate / 100
			subtraction = rate_id.subtraction
		else:
			if base_ut <= 2000:
				rate = 0.15
				subtraction = 0.0
			elif base_ut <= 3000:
				rate = 0.2
				subtraction = 140
			else:
				rate = 0.34
				subtraction = 500
			if rate_id.rate_type == 'payment':
				subtraction = 0.0

		return {
			'id': rate_id.id,
			'base': rate_id.base / 100,
			'rate': rate,
			'subtraction': subtraction,
		}


class AccountISLRConceptRate(models.Model):
	_name = "account.islr.concept.rate"
	_description = "Tasa de concepto de ISLR"
	_order = "name"

	name = fields.Char(string='Código', size=3, required=True)
	person_type_id = fields.Many2one('person.type', string='Tipo de persona', required=True)
	base = fields.Float(string='% Base', digits=(5,2), default=100)
	factor = fields.Float(string='Factor', digits=(16,4))
	rate = fields.Float(string='% Retención', digits=(5,2))
	subtraction = fields.Float(string='Sustracción (UT)', compute='_compute_subtraction', store=True)
	rate_type = fields.Selection([('payment', 'Pagos acumulados'), ('rate', 'Tarifa 2')], string='Tipo tasa')
	islr_concept_id = fields.Many2one('account.islr.concept', string='Concepto de ISLR', ondelete='cascade')

	_sql_constraints = [
		('unique_name', 'UNIQUE(name)', 'El codigo debe ser unico!'),
		('isdigit_name', "CHECK(name ~ '^\d+$')", 'El codigo tiene que ser numérico!'),
		('unique_person_type_id', 'UNIQUE(islr_concept_id, person_type_id)', 'El campo "Tipo de persona" debe ser unico por concepto !'),
	]

	@api.depends('factor', 'rate')
	def _compute_subtraction(self):
		for rec in self:
			rec.subtraction = rec.factor * rec.rate / 100