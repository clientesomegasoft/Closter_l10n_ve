# -*- coding: utf-8 -*-

from odoo import fields, models

class PersonType(models.Model):
	_name = "person.type"
	_description = "Tipo de persona"

	name = fields.Char(string='Tipo', required=True)
	code = fields.Char(string='Código', required=True)
	is_company = fields.Boolean(string='Es compañía', default=False)