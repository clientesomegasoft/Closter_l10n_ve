from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"  # pylint: disable=consider-merging-classes-inherited

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
    _inherit = "sale.order.line"  # pylint: disable=consider-merging-classes-inherited

    product_tracking = fields.Selection(related="product_id.tracking")
    line_lot_serial_ids = fields.One2many(
        "sale.order.line.lot.serial", "line_id", string="lines"
    )
    consignment_move_id = fields.Many2one("stock.move", string="Consignment Move")
    sale_consignment_line_id = fields.Many2one(
        "sale.consignment.line", string="Consignment Line"
    )
    purchase_order_line_id = fields.Many2one("purchase.order.line", "Purchase Line")

    def _prepare_invoice_line(self, **optional_values):
        values = super(__class__, self)._prepare_invoice_line(**optional_values)
        if self.order_id.analytic_id:
            values["analytic_distribution"] = {self.order_id.analytic_id.id: 100}
        return values

    @api.depends("product_id")
    def _compute_product_uom(self):
        res = super()._compute_product_uom()
        for rec in self:
            if rec.order_id.is_consignments_purchase and not rec.order_id.analytic_id:
                raise ValidationError(_("Please select consignment account"))
            if rec.order_id.is_consignments_purchase and rec.order_id.analytic_id:
                product_line_ids = (
                    rec.order_id.analytic_id.purchase_order_id.order_line.filtered(
                        lambda x: x.product_id == rec.product_id
                    )
                )
                if product_line_ids:
                    rec.purchase_order_line_id = product_line_ids[0]
        return res

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
