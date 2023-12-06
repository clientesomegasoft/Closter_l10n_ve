# -*- coding: utf-8 -*-#

from odoo import models, fields, api, _

class AccountPaymentRegister(models.TransientModel):
	_inherit = "account.payment.register"

	apply_itf = fields.Boolean(compute='_compute_apply_itf')
	calculate_itf = fields.Boolean(string='Permitir ITF', default=True)

	@api.depends('currency_id', 'payment_type', 'company_id.apply_itf')
	def _compute_apply_itf(self):
		for pay in self:
			pay.apply_itf = pay.company_id.apply_itf and pay.payment_type == 'outbound' and pay.currency_id.id == pay.company_id.fiscal_currency_id.id

	def _create_payment_vals_from_wizard(self, batch_result):
		payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)
		payment_vals['calculate_itf'] = self.calculate_itf
		return payment_vals