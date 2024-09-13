# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMove(models.Model):
	_inherit = "account.move"

	fiscal_transaction_type = fields.Char(compute='_compute_fiscal_transaction_type', store=True)

	@api.depends('move_type')
	def _compute_fiscal_transaction_type(self):
		for move in self:
			if move.move_type in ('in_refund', 'out_refund'):
				move.fiscal_transaction_type = 'ANU-03'
			elif move.debit_origin_id:
				move.fiscal_transaction_type = 'COM-02'
			else:
				move.fiscal_transaction_type = 'REG-01'