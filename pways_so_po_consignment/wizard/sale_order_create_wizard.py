from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderCreateWizards(models.TransientModel):
    _name = "sale.order.create.wizard"
    _description = "Sale Order Create Wizard"

    create_type = fields.Selection(
        [("manually", "Manually"), ("import_xls", "Import Xls")],
        string="Selection",
        default="manually",
    )
    consignment_line_ids = fields.One2many(
        "order.line.wizard", "order_id", string="Line Ids"
    )
    consignment_id = fields.Many2one("sale.consignment.order")
    data_file = fields.Binary(string="XLS File")
    file_name = fields.Char("Filename:- ")

    @api.model
    def default_get(self, vals):
        lines = []
        consignment_id = self.env["sale.consignment.order"]
        vals = super(__class__, self).default_get(vals)
        active_id = self.env.context.get("active_id")
        if active_id:
            consignment_id = self.env["sale.consignment.order"].browse(active_id)
        if consignment_id:
            consignment_line_ids = consignment_id.mapped("order_line")

            if all([line.available_qty == 0 for line in consignment_line_ids]):
                raise ValidationError(
                    _("There are nothing to sale from this consignment order")
                )

            fil_consignment_line_ids = consignment_line_ids.filtered(
                lambda line: line.available_qty > 0
                and line.move_id.state in ["assigned", "done"]
            )

            for line in fil_consignment_line_ids:
                line_wizard_id = self.env["order.line.wizard"].create(
                    {
                        "product_id": line.product_id.id,
                        "qty": line.available_qty,
                        "price_unit": line.price_unit,
                        "move_id": line.move_id.id,
                        "consignment_line_id": line.id,
                    }
                )
                lines.append(line_wizard_id.id)
            vals["consignment_line_ids"] = [[6, 0, lines]]
            vals["consignment_id"] = consignment_id.id
        return vals

    def action_create_sale_order(self):
        pass

        for line in self.consignment_line_ids.filtered(
            lambda x: x.product_id.tracking != "none"
        ):
            if not line.order_line_ids:
                raise ValidationError(
                    _(
                        "Please select proper lot/serial for product %s."
                        % (line.product_id.name)
                    )
                )

        consignment_id = self.consignment_id
        consignment_move_ids = consignment_id.order_line.mapped("move_id")

        for move in consignment_move_ids:
            move._action_done()

        vals = {
            "partner_id": consignment_id.partner_id.id,
            "date_order": consignment_id.date_order,
            "warehouse_id": consignment_id.warehouse_id
            and consignment_id.warehouse_id.id,
            "is_consignments_sales": True,
            "is_consignments_sale": True,
            "consignment_id": consignment_id.id,
        }

        order_id = self.env["sale.order"].create(vals)

        for line in self.consignment_line_ids:
            lines_id = self.env["sale.order.line"].create(
                {
                    "order_id": order_id.id,
                    "product_id": line.product_id.id or False,
                    "name": line.product_id.name,
                    "product_uom_qty": line.qty,
                    "price_unit": line.price_unit,
                    "consignment_move_id": line.move_id.id,
                    "sale_consignment_line_id": line.consignment_line_id.id,
                }
            )

            for lot_serial in line.order_line_ids:
                lot_serial_id = self.env[  # noqa: F841
                    "sale.order.line.lot.serial"
                ].create(
                    {
                        "line_id": lines_id.id,
                        "product_id": lot_serial.product_id.id or False,
                        "qty": lot_serial.qty,
                        "lot_producing_id": lot_serial.lot_producing_id.id,
                    }
                )

        consignment_id.sale_ids = [(4, order_id.id)]
        consignment_id.write({"state": "sale"})


class SaleOrderCreateWizard(models.TransientModel):
    _name = "order.line.wizard"
    _description = "Order Line Wizard"

    order_id = fields.Many2one("sale.order.create.wizard", string="Order")
    consignment_line_id = fields.Many2one("sale.consignment.line", string="Line")
    product_id = fields.Many2one("product.product", string="Product")
    qty = fields.Float(string="Qty")
    price_unit = fields.Float("Price Unit")
    order_line_ids = fields.One2many(
        "order.line.wizard.lot.serial", "line_id", string="Order"
    )
    sale_line_id = fields.Many2one("sale.order.line", string="Sale Orders")
    product_tracking = fields.Selection(related="product_id.tracking")
    move_id = fields.Many2one("stock.move", string="Stock Moves")

    def sale_line_lot_serial(self):
        lines = []
        consignment_line_ids = self.order_id.consignment_id.mapped("order_line")
        view_id = self.env.ref("pways_so_po_consignment.order_line_wizard_from_view").id
        if not self.order_line_ids:
            for line in consignment_line_ids.filtered(
                lambda x: x.product_id == self.product_id
                and x == self.consignment_line_id
            ):
                for lot in line.line_lot_serial_ids.filtered(
                    lambda x: x.unreserve_qty > 0
                ):
                    lot_serial_id = self.env["order.line.wizard.lot.serial"].create(
                        {
                            "line_id": self.id,
                            "product_id": lot.product_id.id,
                            "qty": lot.unreserve_qty,
                            "lot_producing_id": lot.lot_producing_id.id,
                        }
                    )
                    lines.append(lot_serial_id.id)
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_id": view_id,
            "view_mode": "form",
            "res_model": "order.line.wizard",
            "target": "new",
            "context": {"create": False, "default_order_line_ids": [[6, 0, lines]]},
            "res_id": self.id,
        }

    def confirm_lot_serial(self):
        self.qty = sum(self.order_line_ids.mapped("qty"))
        view_id = self.env.ref(
            "pways_so_po_consignment.sale_order_create_wizard_form_view"
        ).id
        return {
            "type": "ir.actions.act_window",
            "name": "Payment Distribution",
            "res_model": "sale.order.create.wizard",
            "target": "new",
            "view_mode": "form",
            "view": [[view_id, "form"]],
            "res_id": self.order_id.id,
        }
