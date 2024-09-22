from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleConsignmentLineLotSerial(models.Model):
    _name = "sale.consignment.line.lot.serial"
    _description = "Sale Consignemnt Line Lot"

    line_id = fields.Many2one("sale.consignment.line", string="Line Lot Serial")
    product_id = fields.Many2one(
        "product.product", related="line_id.product_id", store=True
    )
    available_qty = fields.Float(
        string="Available Qty", compute="_compute_available_qty", store=True
    )
    lot_producing_ids = fields.Many2many(
        "stock.lot",
        string="Lot/Serial Number",
        store=True,
        compute="_compute_lot_producing_ids",
    )
    lot_producing_id = fields.Many2one(
        "stock.lot",
        string="Lot/Serial Number",
        domain="[('product_id', '=', product_id)]",
    )
    qty = fields.Float(string="QTY", default="1.0")
    uom_id = fields.Many2one("uom.uom", related="line_id.product_id.uom_id")
    unreserve_qty = fields.Float("Unreserve Qty", compute="_compute_unreserve_qty")

    def close_action_window(self):
        return False

    @api.depends("line_id.product_id")
    def _compute_lot_producing_ids(self):
        for line in self:
            stock_location = line.line_id.order_id.warehouse_id.lot_stock_id.id
            lot_producing_ids = self.product_id.stock_quant_ids.filtered(
                lambda x: x.quantity > 0
            ).mapped("lot_id")
            for lot_line in lot_producing_ids.filtered(lambda x: x.quant_ids):
                available_quantity = line.product_id.with_context(
                    location=stock_location, lot_id=lot_line.id
                ).free_qty
                if available_quantity > 0:
                    line.lot_producing_ids = [(4, lot_line.id)]

    @api.depends("lot_producing_id")
    def _compute_available_qty(self):
        for sale_info_line in self:
            stock_location = (
                sale_info_line.line_id.order_id.warehouse_id.lot_stock_id.id
            )
            available_quantity = sale_info_line.product_id.with_context(
                location=stock_location, lot_id=sale_info_line.lot_producing_id.id
            ).free_qty
            sale_info_line.available_qty = available_quantity

    def _compute_unreserve_qty(self):
        for line in self:
            order_lines = line.line_id.order_id.sale_ids.mapped("order_line")
            order_lines_product = order_lines.filtered(
                lambda x: x.sale_consignment_line_id.id == line.line_id.id
            )
            product_lot_ids = order_lines_product.mapped(
                "line_lot_serial_ids"
            ).filtered(lambda x: x.lot_producing_id.id == line.lot_producing_id.id)
            unreserve_qty = line.qty - sum(product_lot_ids.mapped("qty"))
            line.unreserve_qty = unreserve_qty

    @api.constrains("qty")
    def _check_qty(self):
        so_line_ids = self.env["sale.consignment.line.lot.serial"].search(
            [("line_id", "=", self.line_id.id)]
        )
        for record in self:
            qty = sum(so_line_ids.mapped("qty"))
            if qty > record.line_id.sale_qty:
                raise ValidationError(
                    _("Total quantity can not be greater than line quantity.")
                )
            if record.line_id.product_id.tracking == "serial":
                if 1 < record.qty:
                    raise ValidationError(_("For serial qty will be 1 only"))
            if record.qty > record.available_qty:
                raise ValidationError(
                    _(
                        "Product %s qty is more than lot/serial avalible qty"
                        % (record.product_id.name)
                    )
                )

    @api.constrains("lot_producing_id")
    def check_lot_serial(self):
        for line in self:
            if line.product_id.tracking == "serial":
                so_line_ids = self.env["sale.consignment.line.lot.serial"].search(
                    [
                        ("lot_producing_id", "=", line.lot_producing_id.id),
                        ("line_id", "=", line.line_id.id),
                    ]
                )
                if len(so_line_ids) > 1:
                    raise ValidationError(_("You can not use same serial number twise"))
