# -*- coding: utf-8 -*-

from odoo import fields, models

class Partner(models.Model):
	_inherit = "res.partner"

	is_iva_agent = fields.Boolean(string='¿Es agente de retención de IVA?', copy=False)
	iva_rate_id = fields.Many2one('withholding.iva.rate', string='Tasa de retención de IVA', copy=False)

	def write(self, vals):
		if vals.get('is_iva_agent', self.is_iva_agent) and ((
			'partner_type' in vals and vals['partner_type'] not in ('customer', 'customer_supplier')
		) or (
			'person_type_id' in vals and vals['person_type_id'] not in (
				self.env.ref('l10n_ve_fiscal_identification.person_type_pjdo').id,
				self.env.ref('l10n_ve_fiscal_identification.person_type_pnre').id
		))):
			vals['is_iva_agent'] = False
		return super(Partner, self).write(vals)