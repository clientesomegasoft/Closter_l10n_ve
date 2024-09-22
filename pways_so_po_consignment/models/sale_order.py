from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_consignments_sale = fields.Boolean(string="Sale Consignment", copy=False)
    is_consignments_sales = fields.Boolean(string="Sale Consignments", copy=False)
    invoiced = fields.Boolean(string="Commission Paid", copy=False)
    consignment_id = fields.Many2one("sale.consignment.order", string="Consignment")
    consignment_rount_id = fields.Many2one(
        related="warehouse_id.consignment_rount_id",
        string="Consignment Route",
        store=True,
    )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_tracking = fields.Selection(related="product_id.tracking")
    line_lot_serial_ids = fields.One2many(
        "sale.order.line.lot.serial", "line_id", string="lines"
    )
    consignment_move_id = fields.Many2one("stock.move", string="Consignment Move")
    sale_consignment_line_id = fields.Many2one(
        "sale.consignment.line", string="Consignment Line"
    )

    def sale_line_lot_serial_assign(self):
        view_id = self.env.ref("pways_so_po_consignment.sale_order_line_form_view").id
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_id": view_id,
            "view_mode": "form",
            "res_model": "sale.order.line",
            "target": "new",
            "context": {"create": False},
            "res_id": self.id,
        }

    def _prepare_procurement_values(self, group_id=False):
        """Prepare specific key for moves or other components that will be
        created from a stock rule comming from a sale order line. This method
        could be override in order to add other custom key that could be used
        in move/po creation.
        """
        values = super(__class__, self)._prepare_procurement_values(group_id)
        if self.consignment_move_id.state != "done":
            self.consignment_move_id._action_done()
        if self.consignment_move_id:
            values.update({"route_ids": self.order_id.consignment_rount_id})
        return values
