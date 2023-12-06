# -*- coding: utf-8 -*-

from collections import defaultdict
from odoo import fields, models
from odoo.tools import float_is_zero

class StockValuationLayer(models.Model):
	_inherit = "stock.valuation.layer"

	currency_ref_id = fields.Many2one('res.currency', related='company_id.currency_ref_id')
	unit_cost_ref = fields.Monetary('Valor unitario op.', default=0.0, readonly=True, currency_field='currency_ref_id')
	value_ref = fields.Monetary('Valor total op.', default=0.0, readonly=True, currency_field='currency_ref_id')
	remaining_value_ref = fields.Monetary(default=0.0, currency_field='currency_ref_id')

	def _validate_accounting_entries(self):
		am_vals = []
		for svl in self:
			if not svl.with_company(svl.company_id).product_id.valuation == 'real_time':
				continue
			if svl.currency_id.is_zero(svl.value):
				continue
			move = svl.stock_move_id
			if not move:
				move = svl.stock_valuation_layer_id.stock_move_id
			am_vals += move.with_company(svl.company_id)._account_entry_move(svl.quantity, svl.description, svl.id, svl.value)
		if am_vals:
			account_moves = self.env['account.move'].sudo().with_context(skip_compute_balance_ref=True).create(am_vals)
			account_moves._post()
		for svl in self:
			# Eventually reconcile together the invoice and valuation accounting entries on the stock interim accounts
			if svl.company_id.anglo_saxon_accounting:
				svl.stock_move_id._get_related_invoices()._stock_account_anglo_saxon_reconcile_valuation(product=svl.product_id)


class StockMove(models.Model):
	_inherit = "stock.move"

	def product_price_update_before_done(self, forced_qty=None):
		tmpl_dict = defaultdict(lambda: 0.0)
		# adapt standard price on incomming moves if the product cost_method is 'average'
		std_price_update = {}
		for move in self.filtered(lambda move: move._is_in() and move.with_company(move.company_id).product_id.cost_method == 'average'):
			product_tot_qty_available = move.product_id.sudo().with_company(move.company_id).quantity_svl + tmpl_dict[move.product_id.id]
			rounding = move.product_id.uom_id.rounding

			valued_move_lines = move._get_in_move_lines()
			qty_done = 0
			for valued_move_line in valued_move_lines:
				qty_done += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)

			qty = forced_qty or qty_done
			if float_is_zero(product_tot_qty_available, precision_rounding=rounding):
				new_std_price = move._get_price_unit()
			elif float_is_zero(product_tot_qty_available + move.product_qty, precision_rounding=rounding) or \
					float_is_zero(product_tot_qty_available + qty, precision_rounding=rounding):
				new_std_price = move._get_price_unit()
			else:
				# Get the standard price
				amount_unit = std_price_update.get((move.company_id.id, move.product_id.id)) or move.product_id.with_company(move.company_id).standard_price
				new_std_price = ((amount_unit * product_tot_qty_available) + (move._get_price_unit() * qty)) / (product_tot_qty_available + qty)

			tmpl_dict[move.product_id.id] += qty_done
			# Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
			move.product_id.with_company(move.company_id.id).with_context(disable_auto_svl=True).sudo().write({
				'standard_price': new_std_price,
				'standard_price_ref': new_std_price * move.company_id.currency_ref_id.rate,
			})
			std_price_update[move.company_id.id, move.product_id.id] = new_std_price

		# adapt standard price on incomming moves if the product cost_method is 'fifo'
		for move in self.filtered(lambda move:
								  move.with_company(move.company_id).product_id.cost_method == 'fifo'
								  and float_is_zero(move.product_id.sudo().quantity_svl, precision_rounding=move.product_id.uom_id.rounding)):
			amount = move._get_price_unit()
			move.product_id.with_company(move.company_id.id).sudo().write({
				'standard_price': amount,
				'standard_price_ref': amount * move.company_id.currency_ref_id.rate,
			})

	def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, svl_id, description):
		rslt = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, svl_id, description)
		svl = self.env['stock.valuation.layer'].browse(svl_id)
		value_ref = abs(svl.value_ref)
		rslt['debit_line_vals']['balance_ref'] = value_ref
		rslt['credit_line_vals']['balance_ref'] = -value_ref
		return rslt