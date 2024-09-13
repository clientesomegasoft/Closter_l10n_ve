# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CommissionScale(models.Model):
	_name = 'commission.scale'
	_description = 'Commission scale'
	_inherit = ['mail.thread.cc', 'mail.activity.mixin']

	name = fields.Char(string="Name", required=True, tracking=True)
	code = fields.Char(string="Code", readonly=True, tracking=True)
	active = fields.Boolean('Active', default=True, tracking=True)
	sale_scale_from = fields.Float(tracking=True)
	sale_scale_to = fields.Float(tracking=True)
	fixed_amount = fields.Float(string="Fixed amount", tracking=True)
	percentage = fields.Float(string="Percentage", tracking=True)
	curency_id = fields.Many2one('res.currency', string="Currency", domain=[('active', '=', True)], tracking=True)

	@api.model_create_multi
	def create(self, vals_list):
		res = super(CommissionScale, self).create(vals_list)
		for rec in res:
			rec.code = self.env['ir.sequence'].next_by_code('commission.scale.seq')
		return res