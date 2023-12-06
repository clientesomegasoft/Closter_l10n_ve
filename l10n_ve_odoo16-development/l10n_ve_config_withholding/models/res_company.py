# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
	_inherit = "res.company"

	sign_512 = fields.Image("Insertar imagen", max_width=512, max_height=512)

	def _create_per_company_withholding_sequence(self):
		#OVERRIDE
		return

	@api.model_create_multi
	def create(self, vals_list):
		companies = super().create(vals_list)
		companies.sudo()._create_per_company_withholding_sequence()
		return companies