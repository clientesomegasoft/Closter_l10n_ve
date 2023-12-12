# -*- coding: utf-8 -*-

from odoo import fields, models

class AccountTax(models.Model):
	_inherit = "account.tax"

	fiscal_tax_type = fields.Selection([
		('general', 'Alícuota general'),
		('reduced', 'Alícuota reducida'),
		('additional', 'Alícuota adicional'),
		('exempt', 'Exento o no gravado')],
		string='Tipo de alícuota'
	)