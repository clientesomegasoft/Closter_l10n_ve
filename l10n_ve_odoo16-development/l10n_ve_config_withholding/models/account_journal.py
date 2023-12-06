# -*- coding: utf-8 -*-

from odoo import fields, models, api

class AccountJournal(models.Model):
	_inherit = "account.journal"

	withholding_journal_type = fields.Selection(selection=[], string='Tipo de diario retenciones')

	@api.onchange('type')
	def _onchange_journal_type(self):
		self.withholding_journal_type = False