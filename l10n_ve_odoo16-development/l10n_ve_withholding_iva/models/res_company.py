# -*- coding: utf-8 -*-

from odoo import models, fields

class ResCompany(models.Model):
	_inherit = "res.company"

	in_iva_journal_id = fields.Many2one('account.journal', string='Diario de IVA en compras')
	out_iva_journal_id = fields.Many2one('account.journal', string='Diario de IVA en ventas')
	in_iva_account_id = fields.Many2one('account.account', string='Cuenta de IVA en compras')
	out_iva_account_id = fields.Many2one('account.account', string='Cuenta de IVA en ventas')

	def _create_per_company_withholding_sequence(self):
		super(ResCompany, self)._create_per_company_withholding_sequence()
		values = [{
			'name': 'Withholding IVA: %s' % company.name,
			'code': 'account_withholding_iva',
			'company_id': company.id,
			'padding': 8,
			'number_next': 1,
			'number_increment': 1
		} for company in self]
		if values:
			self.env['ir.sequence'].create(values)