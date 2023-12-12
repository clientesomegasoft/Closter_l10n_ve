# -*- coding: utf-8 -*-

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
	_inherit = "res.config.settings"

	currency_ref_id = fields.Many2one(related='company_id.currency_ref_id', readonly=False, required=True)
	fiscal_currency_id = fields.Many2one(related='company_id.fiscal_currency_id', readonly=False, required=True)