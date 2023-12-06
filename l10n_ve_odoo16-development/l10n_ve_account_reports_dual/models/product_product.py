# -*- coding: utf-8 -*-

import time
from odoo import fields, models

class ProductProduct(models.Model):
	_inherit = "product.product"

	sale_avg_price_ref = fields.Float(compute='_compute_product_margin_fields_values', string='Precio Unidad Promedio de Venta op.')
	turnover_ref = fields.Float(compute='_compute_product_margin_fields_values', string='Volumen de negocio op.')
	sales_gap_ref = fields.Float(compute='_compute_product_margin_fields_values', string='Diferencia ventas op.')
	total_cost_ref = fields.Float(compute='_compute_product_margin_fields_values', string='Coste total op.')
	total_margin_ref = fields.Float(compute='_compute_product_margin_fields_values', string='Margen total op.')

	def _compute_product_margin_fields_values(self, field_names=None):
		if field_names is None:
			field_names = []
		date_from = self.env.context.get('date_from', time.strftime('%Y-01-01'))
		date_to = self.env.context.get('date_to', time.strftime('%Y-12-31'))
		invoice_state = self.env.context.get('invoice_state', 'open_paid')
		res = {
			product_id: {
				'date_from': date_from, 'date_to': date_to, 'invoice_state': invoice_state, 'turnover': 0.0,
				'sale_avg_price': 0.0, 'purchase_avg_price': 0.0, 'sale_num_invoiced': 0.0, 'purchase_num_invoiced': 0.0,
				'sales_gap': 0.0, 'purchase_gap': 0.0, 'total_cost': 0.0, 'sale_expected': 0.0, 'normal_cost': 0.0, 'total_margin': 0.0,
				'expected_margin': 0.0, 'total_margin_rate': 0.0, 'expected_margin_rate': 0.0,
				'sale_avg_price_ref': 0.0, 'turnover_ref': 0.0, 'sales_gap_ref': 0.0, 'total_cost_ref': 0.0, 'total_margin_ref': 0.0,
			} for product_id in self.ids
		}
		states = ()
		payment_states = ()
		if invoice_state == 'paid':
			states = ('posted',)
			payment_states = ('in_payment', 'paid', 'reversed')
		elif invoice_state == 'open_paid':
			states = ('posted',)
			payment_states = ('not_paid', 'in_payment', 'paid', 'reversed', 'partial')
		elif invoice_state == 'draft_open_paid':
			states = ('posted', 'draft')
			payment_states = ('not_paid', 'in_payment', 'paid', 'reversed', 'partial')
		if "force_company" in self.env.context:
			company_id = self.env.context['force_company']
		else:
			company_id = self.env.company.id
		self.env['account.move.line'].flush_model(['price_unit', 'quantity', 'balance', 'product_id', 'display_type'])
		self.env['account.move'].flush_model(['state', 'payment_state', 'move_type', 'invoice_date', 'company_id'])
		self.env['product.template'].flush_model(['list_price'])
		sqlstr = """
				WITH currency_rate AS MATERIALIZED ({})
				SELECT
					l.product_id as product_id,
					SUM(
						l.price_unit / COALESCE(NULLIF(CASE WHEN l.currency_id = crr.currency_id THEN crr.rate ELSE cr.rate END, 0), 1) *
						l.quantity * (CASE WHEN i.move_type IN ('out_invoice', 'in_invoice') THEN 1 ELSE -1 END) * ((100 - l.discount) * 0.01)
					) / NULLIF(SUM(l.quantity * (CASE WHEN i.move_type IN ('out_invoice', 'in_invoice') THEN 1 ELSE -1 END)), 0) AS avg_unit_price,
					SUM(l.quantity * (CASE WHEN i.move_type IN ('out_invoice', 'in_invoice') THEN 1 ELSE -1 END)) AS num_qty,
					SUM(ABS(l.balance) * (CASE WHEN i.move_type IN ('out_invoice', 'in_invoice') THEN 1 ELSE -1 END)) AS total,
					SUM(l.quantity * pt.list_price * (CASE WHEN i.move_type IN ('out_invoice', 'in_invoice') THEN 1 ELSE -1 END)) AS sale_expected,
					SUM(
						l.price_unit / COALESCE(NULLIF(CASE WHEN l.currency_id = crr.currency_id THEN crr.rate ELSE cr.rate END, 0), 1) * crr.rate *
						l.quantity * (CASE WHEN i.move_type IN ('out_invoice', 'in_invoice') THEN 1 ELSE -1 END) * ((100 - l.discount) * 0.01)
					) / NULLIF(SUM(l.quantity * (CASE WHEN i.move_type IN ('out_invoice', 'in_invoice') THEN 1 ELSE -1 END)), 0) AS avg_unit_price_ref,
					SUM(ABS(l.balance_ref) * (CASE WHEN i.move_type IN ('out_invoice', 'in_invoice') THEN 1 ELSE -1 END)) AS total_ref,
					SUM(l.quantity * pt.list_price * crr.rate * (CASE WHEN i.move_type IN ('out_invoice', 'in_invoice') THEN 1 ELSE -1 END)) AS sale_expected_ref
				FROM account_move_line l
				LEFT JOIN account_move i ON (l.move_id = i.id)
				LEFT JOIN product_product product ON (product.id=l.product_id)
				LEFT JOIN product_template pt ON (pt.id = product.product_tmpl_id)
				LEFT JOIN res_currency_rate crr ON (crr.id = l.currency_rate_ref)
				left join currency_rate cr on
				(cr.currency_id = i.currency_id and
				 cr.company_id = i.company_id and
				 cr.date_start <= COALESCE(i.invoice_date, NOW()) and
				 (cr.date_end IS NULL OR cr.date_end > COALESCE(i.invoice_date, NOW())))
				WHERE l.product_id IN %s
				AND i.state IN %s
				AND i.payment_state IN %s
				AND i.move_type IN %s
				AND i.invoice_date BETWEEN %s AND  %s
				AND i.company_id = %s
				AND l.display_type = 'product'
				GROUP BY l.product_id
				""".format(self.env['res.currency']._select_companies_rates())
		invoice_types = ('out_invoice', 'out_refund')
		self.env.cr.execute(sqlstr, (tuple(self.ids), states, payment_states, invoice_types, date_from, date_to, company_id))
		for row in self.env.cr.dictfetchall():
			product_id = row['product_id']
			res[product_id]['sale_avg_price'] = row['avg_unit_price'] or 0.0
			res[product_id]['sale_num_invoiced'] = row['num_qty'] or 0.0
			res[product_id]['turnover'] = row['total'] or 0.0
			res[product_id]['sale_expected'] = row['sale_expected'] or 0.0
			res[product_id]['sales_gap'] = res[product_id]['sale_expected'] - res[product_id]['turnover']
			res[product_id]['total_margin'] = res[product_id]['turnover']
			res[product_id]['expected_margin'] = res[product_id]['sale_expected']
			res[product_id]['total_margin_rate'] = res[product_id]['turnover'] and res[product_id]['total_margin'] * 100 / res[product_id]['turnover'] or 0.0
			res[product_id]['expected_margin_rate'] = res[product_id]['sale_expected'] and res[product_id]['expected_margin'] * 100 / res[product_id]['sale_expected'] or 0.0
			# Referencial amount
			res[product_id]['sale_avg_price_ref'] = row['avg_unit_price_ref'] or 0.0
			res[product_id]['turnover_ref'] = row['total_ref'] or 0.0
			res[product_id]['sales_gap_ref'] = (row['sale_expected_ref'] or 0.0) - res[product_id]['turnover_ref']
			res[product_id]['total_margin_ref'] = res[product_id]['turnover_ref']

		ctx = self.env.context.copy()
		ctx['force_company'] = company_id
		invoice_types = ('in_invoice', 'in_refund')
		self.env.cr.execute(sqlstr, (tuple(self.ids), states, payment_states, invoice_types, date_from, date_to, company_id))
		for row in self.env.cr.dictfetchall():
			product_id = row['product_id']
			res[product_id]['purchase_avg_price'] = row['avg_unit_price'] or 0.0
			res[product_id]['purchase_num_invoiced'] = row['num_qty'] or 0.0
			res[product_id]['total_cost'] = row['total'] or 0.0
			res[product_id]['total_margin'] = res[product_id].get('turnover', 0.0) - res[product_id]['total_cost']
			res[product_id]['total_margin_rate'] = res[product_id].get('turnover', 0.0) and res[product_id]['total_margin'] * 100 / res[product_id].get('turnover', 0.0) or 0.0
			# Referencial amount
			res[product_id]['total_cost_ref'] = row['total_ref'] or 0.0
			res[product_id]['total_margin_ref'] = res[product_id].get('turnover_ref', 0.0) - res[product_id]['total_cost_ref']

		for product in self:
			res[product.id]['normal_cost'] = product.standard_price * res[product.id]['purchase_num_invoiced']
			res[product.id]['purchase_gap'] = res[product.id]['normal_cost'] - res[product.id]['total_cost']
			res[product.id]['expected_margin'] = res[product.id].get('sale_expected', 0.0) - res[product.id]['normal_cost']
			res[product.id]['expected_margin_rate'] = res[product.id].get('sale_expected', 0.0) and res[product.id]['expected_margin'] * 100 / res[product.id].get('sale_expected', 0.0) or 0.0
			product.update(res[product.id])
		return res