# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
	_inherit = "sale.order"

	department_id = fields.Many2one('hr.department', string="Department", domain=[('generate_commissions', '=', True)])
	seller_employee_id = fields.Many2one('hr.employee', string="seller")
	assigned_employee_id = fields.Many2one('hr.employee', string="Assigned")
	required_department_id = fields.Boolean(string="required_department_id", default=False)

	@api.onchange('seller_employee_id')
	def _onchange_seller_employee(self):
		if self.seller_employee_id and not self.assigned_employee_id:
			self.assigned_employee_id = self.seller_employee_id
			self.required_department_id = True
	
	@api.onchange('assigned_employee_id', 'seller_employee_id')
	def _onchange_required_department_id(self):
		if self.seller_employee_id and self.assigned_employee_id:
			self.required_department_id = True
		else:
			self.required_department_id = False

	def _prepare_invoice(self):
		self.ensure_one()
		res = super(SaleOrder, self)._prepare_invoice()
		res['department_id'] = self.department_id.id
		res['seller_employee_id'] = self.seller_employee_id.id
		res['assigned_employee_id'] = self.assigned_employee_id.id
		return res