# -*- coding: utf-8 -*-

from odoo import models, fields

class ResCompany(models.Model):
	_inherit = "res.company"

	in_islr_journal_id = fields.Many2one('account.journal', string='Diario de ISLR en compras')
	out_islr_journal_id = fields.Many2one('account.journal', string='Diario de ISLR en ventas')
	in_islr_account_id = fields.Many2one('account.account', string='Cuenta de ISLR en compras')
	out_islr_account_id = fields.Many2one('account.account', string='Cuenta de ISLR en ventas')

	def _create_per_company_withholding_sequence(self):
		super(ResCompany, self)._create_per_company_withholding_sequence()
		values = [{
			'name': 'Withholding ISLR: %s' % company.name,
			'code': 'account_withholding_islr',
			'company_id': company.id,
			'padding': 8,
			'number_next': 1,
			'number_increment': 1
		} for company in self]
		if values:
			self.env['ir.sequence'].create(values)