# -*- coding: utf-8 -*-
from odoo import models,fields,api, _
from datetime import datetime
from odoo.exceptions import ValidationError, UserError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_consignments = fields.Boolean(string="Consignment", help="Consignments", copy=False)
    is_consignments_purchase = fields.Boolean(string="Purchase Consignments", help="Consignments", copy=False)
    analytic_id = fields.Many2one('account.analytic.account', string='Consignment Account', copy=False)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        consignments_data = []
        if self.is_consignments and self.analytic_id:
            for line in self.order_line:
                d_vals = {
                    'product_id': line.product_id.id,
                    'description': line.product_id.name,
                    'consignment_type': 'income',
                    'qty': line.product_uom_qty,
                    'uom_id': line.product_id.uom_id.id,
                    'unit_price': line.price_unit,
                    'sales': line.price_unit,
                    'sale_id': self.id,
                    'purchase_order_line_id': line.purchase_order_line_id.id,
                }
                consignments_data.append((0, 0, d_vals))
            self.analytic_id.consignment_ids = consignments_data
        return res

    @api.constrains('order_line')
    def _check_product_line(self):
        analytic_id = self.analytic_id
        if analytic_id:
            for record in self.order_line:
                if record.product_id.id not in analytic_id.purchase_order_id.order_line.mapped('product_id').ids:
                    raise ValidationError(_("Product %s not found in this consignment purchase order" %(record.product_id.name)))
                else:
                    purchase_line_ids = analytic_id.purchase_order_id.order_line.filtered(lambda x: x.product_id.id == record.product_id.id)
                    qty = sum(purchase_line_ids.mapped('product_qty'))
                    if record.product_uom_qty > qty:
                        raise ValidationError(_("Order qty of product %s is more then consignment purchase order" %(record.product_id.name)))


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    purchase_order_line_id = fields.Many2one('purchase.order.line', "Consignment")

    def _prepare_invoice_line(self, **optional_values):
        values = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        if self.order_id.analytic_id:
            values['analytic_distribution'] = {self.order_id.analytic_id.id: 100}
        return values

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        super()._compute_price_unit()
        if self.order_id.is_consignments_purchase and not self.order_id.analytic_id:
            raise ValidationError(_("Please select consignment account"))
        if self.order_id.is_consignments_purchase and self.order_id.analytic_id:
            product_line_ids = self.order_id.analytic_id.purchase_order_id.order_line.filtered(lambda x: x.product_id == self.product_id)
            if product_line_ids:
                self.purchase_order_line_id = product_line_ids[0]
