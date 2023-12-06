# -*- coding: utf-8 -*-

from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
	_inherit = "res.config.settings"

	is_iva_agent = fields.Boolean(related='company_id.partner_id.is_iva_agent', readonly=False)
	in_iva_journal_id = fields.Many2one(related='company_id.in_iva_journal_id', readonly=False, domain="[('company_id', '=', company_id), ('withholding_journal_type', '=', 'iva')]")
	out_iva_journal_id = fields.Many2one(related='company_id.out_iva_journal_id', readonly=False, domain="[('company_id', '=', company_id), ('withholding_journal_type', '=', 'iva')]")
	in_iva_account_id = fields.Many2one(related='company_id.in_iva_account_id', readonly=False)
	out_iva_account_id = fields.Many2one(related='company_id.out_iva_account_id', readonly=False)
	iva_rate_id = fields.Many2one(related='company_id.partner_id.iva_rate_id', readonly=False)

	@api.onchange('is_iva_agent')
	def _onchange_is_iva_agent(self):
		if not self.is_iva_agent:
			self.in_iva_journal_id = False
			self.in_iva_account_id = False