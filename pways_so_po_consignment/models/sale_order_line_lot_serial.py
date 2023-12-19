# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime, date
from odoo.exceptions import ValidationError, UserError
import json

class SaleOrderLineLotSerial(models.Model):
    _name = 'sale.order.line.lot.serial'
    _description = "Sale Order Line Lot serial"

    line_id = fields.Many2one('sale.order.line', string="Sale Lines")
    product_id = fields.Many2one('product.product', related="line_id.product_id")
    lot_producing_id = fields.Many2one('stock.lot', string='Lot/Serial', domain="[('product_id', '=', product_id)]")
    qty = fields.Float(string="Qty")
    uom_id = fields.Many2one('uom.uom', related="line_id.product_id.uom_id")

    def close_action_window(self):
        return False

    @api.constrains('qty')
    def _check_qty(self):
        for record in self:
            so_line_id = self.env['sale.consignment.line.lot.serial'].search([('line_id', '=', record.line_id.id)])
            qty = sum(so_line_id.mapped('qty'))
            if qty > record.line_id.product_uom_qty:
                raise ValidationError("Line qty can not be greater than consignment qty.")
            if record.line_id.product_id.tracking == 'serial' and record.qty > 1:
                raise ValidationError("For serial done qty must be 1")

    @api.constrains('lot_producing_id')
    def check_lot_serial(self):
        for rec in self.filtered(lambda x: x.line_id.product_id.tracking == 'serial'):
            so_line_ids = self.env['sale.consignment.line.lot.serial'].search([('lot_producing_id', '=', rec.lot_producing_id.id), ('product_id', '=', rec.product_id.id)])
            if so_line_ids and len(so_line_ids) > 1:
                raise ValidationError("For some products same serial/lot number is used twice.")

