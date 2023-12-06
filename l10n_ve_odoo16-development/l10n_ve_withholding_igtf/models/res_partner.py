# -*- coding: UTF-8 -*-

from odoo import models, fields

class Partner(models.Model):
	_inherit = "res.partner"

	apply_igtf = fields.Boolean(string='Agente de percepción de IGTF')

	def write(self, vals):
		if vals.get('apply_igtf', self.apply_igtf) and 'partner_type' in vals and vals['partner_type'] not in ('supplier', 'customer_supplier'):
			vals['apply_igtf'] = False
		return super(Partner, self).write(vals)