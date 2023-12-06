# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, get_lang
from odoo.tools.float_utils import float_round

class PurchaseOrder(models.Model):
	_inherit = "purchase.order"

	currency_ref_id = fields.Many2one(related='company_id.currency_ref_id')
	currency_rate_ref = fields.Many2one(
		comodel_name='res.currency.rate',
		string='Tasa de cambio',
		readonly=True, tracking=True,
		states={'draft': [('readonly', False)]},
		default=lambda self: self.env.company.currency_ref_id.get_currency_rate(),
		domain="[('currency_id', '=', currency_ref_id)]"
	)

	def _prepare_invoice(self):
		vals = super(PurchaseOrder, self)._prepare_invoice()
		vals['currency_rate_ref'] = self.currency_rate_ref.id
		return vals

	def _add_supplier_to_product(self):
		# Add the partner in the supplier list of the product if the supplier is not registered for
		# this product. We limit to 10 the number of suppliers for a product to avoid the mess that
		# could be caused for some generic products ("Miscellaneous").
		for line in self.order_line:
			# Do not add a contact as a supplier
			partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id
			already_seller = (partner | self.partner_id) & line.product_id.seller_ids.mapped('partner_id')
			if line.product_id and not already_seller and len(line.product_id.seller_ids) <= 10:
				# Convert the price in the right currency.
				currency = partner.property_purchase_currency_id or self.env.company.currency_id
				if self.currency_id == self.currency_ref_id and self.currency_rate_ref.rate:
					price = line.price_unit / self.currency_rate_ref.rate
				else:
					price = self.currency_id._convert(line.price_unit, currency, line.company_id, line.date_order or fields.Date.today(), round=False)
				# Compute the price for the template's UoM, because the supplier's UoM is related to that UoM.
				if line.product_id.product_tmpl_id.uom_po_id != line.product_uom:
					default_uom = line.product_id.product_tmpl_id.uom_po_id
					price = line.product_uom._compute_price(price, default_uom)

				supplierinfo = self._prepare_supplier_info(partner, line, price, currency)
				# In case the order partner is a contact address, a new supplierinfo is created on
				# the parent company. In this case, we keep the product name and code.
				seller = line.product_id._select_seller(
					partner_id=line.partner_id,
					quantity=line.product_qty,
					date=line.order_id.date_order and line.order_id.date_order.date(),
					uom_id=line.product_uom)
				if seller:
					supplierinfo['product_name'] = seller.product_name
					supplierinfo['product_code'] = seller.product_code
				vals = {
					'seller_ids': [(0, 0, supplierinfo)],
				}
				# supplier info should be added regardless of the user access rights
				line.product_id.product_tmpl_id.sudo().write(vals)


class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	@api.depends('product_qty', 'product_uom', 'company_id', 'order_id.currency_rate_ref')
	def _compute_price_unit_and_date_planned_and_name(self):
		for line in self:
			if not line.product_id or line.invoice_lines or not line.company_id:
				continue
			params = {'order_id': line.order_id}
			seller = line.product_id._select_seller(
				partner_id=line.partner_id,
				quantity=line.product_qty,
				date=line.order_id.date_order and line.order_id.date_order.date() or fields.Date.context_today(line),
				uom_id=line.product_uom,
				params=params)

			if seller or not line.date_planned:
				line.date_planned = line._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

			# If not seller, use the standard price. It needs a proper currency conversion.
			if not seller:
				unavailable_seller = line.product_id.seller_ids.filtered(
					lambda s: s.partner_id == line.order_id.partner_id)
				if not unavailable_seller and line.price_unit and line.product_uom == line._origin.product_uom:
					# Avoid to modify the price unit if there is no price list for this partner and
					# the line has already one to avoid to override unit price set manually.
					continue
				po_line_uom = line.product_uom or line.product_id.uom_po_id
				price_unit = line.env['account.tax']._fix_tax_included_price_company(
					line.product_id.uom_id._compute_price(line.product_id.standard_price, po_line_uom),
					line.product_id.supplier_taxes_id,
					line.taxes_id,
					line.company_id,
				)
				if line.currency_id == self.env.company.currency_ref_id and line.order_id.currency_rate_ref:
					price_unit = price_unit * line.order_id.currency_rate_ref.rate
				else:
					price_unit = line.product_id.currency_id._convert(price_unit, line.currency_id, line.company_id, line.date_order or fields.Date.context_today(line), False)

				line.price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))
				continue

			price_unit = line.env['account.tax']._fix_tax_included_price_company(seller.price, line.product_id.supplier_taxes_id, line.taxes_id, line.company_id) if seller else 0.0

			if line.currency_id == self.env.company.currency_ref_id and line.order_id.currency_rate_ref:
				price_unit = price_unit * line.order_id.currency_rate_ref.rate
			else:
				price_unit = seller.currency_id._convert(price_unit, line.currency_id, line.company_id, line.date_order or fields.Date.context_today(line), False)

			price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))
			line.price_unit = seller.product_uom._compute_price(price_unit, line.product_uom)

			# record product names to avoid resetting custom descriptions
			default_names = []
			vendors = line.product_id._prepare_sellers({})
			for vendor in vendors:
				product_ctx = {'seller_id': vendor.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
				default_names.append(line._get_product_purchase_description(line.product_id.with_context(product_ctx)))
			if not line.name or line.name in default_names:
				product_ctx = {'seller_id': seller.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
				line.name = line._get_product_purchase_description(line.product_id.with_context(product_ctx))