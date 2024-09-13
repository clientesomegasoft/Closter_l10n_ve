# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.tools import  format_amount

class AccountPayment(models.Model):
	_inherit = "account.payment"

	amount_ref = fields.Char(string='Importe referencia', compute='_compute_amount_ref')

	@api.depends('amount', 'currency_id', 'currency_rate_ref')
	def _compute_amount_ref(self):
		for pay in self.with_context(skip_account_move_synchronization=True):
			if pay.currency_id == pay.company_currency_id:
				pay.amount_ref = format_amount(
					env=self.env,
					amount=pay.amount * self.currency_rate_ref.rate,
					currency=pay.currency_ref_id
				)
			elif pay.currency_id == pay.currency_ref_id:
				pay.amount_ref = format_amount(
					env=self.env,
					amount=pay.amount / self.currency_rate_ref.rate,
					currency=pay.company_currency_id
				)
			else:
				pay.amount_ref = format_amount(
					env=self.env,
					amount=pay.currency_id._convert(pay.amount, pay.company_currency_id, pay.company_id, pay.date) * self.currency_rate_ref.rate,
					currency=pay.currency_ref_id
				)

	def _synchronize_to_moves(self, changed_fields):
		if self._context.get('skip_account_move_synchronization'):
			return
		#forzar calculo cuando cambia el selector de tasa
		if isinstance(changed_fields, set) and 'currency_rate_ref' in changed_fields:
			changed_fields.add('currency_id')
		return super(AccountPayment, self)._synchronize_to_moves(changed_fields)

	def _prepare_move_line_default_vals(self, write_off_line_vals=None):
		vals = super(AccountPayment, self)._prepare_move_line_default_vals(write_off_line_vals)
		if self.currency_id == self.currency_ref_id:
			for line in vals:
				balance = self.company_currency_id.round(line['amount_currency'] / self.currency_rate_ref.rate)
				line.update({
					'debit': balance if balance > 0.0 else 0.0,
					'credit': -balance if balance < 0.0 else 0.0,
				})
		return vals