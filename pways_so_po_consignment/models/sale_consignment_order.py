from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleConsignmentOrder(models.Model):
    _name = "sale.consignment.order"
    _description = "Sale Consignment Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="Name", default="New")
    state = fields.Selection(
        [
            ("draft", "Quotation"),
            ("waiting_approval", "Waiting For Approval"),
            ("approval", "Approved"),
            ("consignment", "Consignment"),
            ("sale", "Sales Order"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        readonly=True,
        copy=False,
        index=True,
        tracking=3,
        default="draft",
    )
    date_order = fields.Datetime(
        string="Order Date",
        required=True,
        readonly=True,
        index=True,
        copy=False,
        default=fields.Datetime.now,
    )
    partner_id = fields.Many2one("res.partner", string="Customer", required=True)
    order_line = fields.One2many(
        "sale.consignment.line", "order_id", string="Order Lines"
    )
    user_id = fields.Many2one(
        "res.users", string="Salesperson", default=lambda self: self.env.user
    )
    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.user.company_id
    )
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", required=True)
    sale_ids = fields.Many2many("sale.order", string="Sale Order", copy=False)
    subtotal = fields.Float(string="Total", compute="_compute_subtotal", store=True)
    moves_count = fields.Integer(string="Moves", compute="_compute_moves_count")
    sales_count = fields.Integer(string="Sales", compute="_compute_sales_count")
    move_line_count = fields.Integer(
        string="Moves Lines", compute="_compute_move_line_count"
    )
    moves_ids = fields.Many2many("stock.move", string="Product Moves", copy=False)
    bill_count = fields.Integer(string="Bill", compute="_compute_bill_count")
    commission = fields.Float(string="Commission (%)")

    def action_unreserved(self):
        self.moves_ids.write({"state": "draft"})
        self.moves_ids.unlink()
        self.write({"state": "draft"})

    def action_cancel(self):
        self.write({"state": "cancel"})

    @api.model
    def create(self, vals):
        res = super(SaleConsignmentOrder, self).create(vals)
        res["name"] = (
            self.env["ir.sequence"].next_by_code("sale.consignment.order") or "/"
        )
        return res

    @api.depends("order_line.product_uom_qty", "order_line.price_unit")
    def _compute_subtotal(self):
        for consignment in self:
            consignment.subtotal = sum(consignment.order_line.mapped("price_subtotal"))

    def _compute_move_line_count(self):
        for consignment in self:
            move_line_ids = consignment.moves_ids.mapped("move_line_ids")
            consignment.move_line_count = len(move_line_ids)

    def _compute_moves_count(self):
        for consignment in self:
            consignment.moves_count = len(consignment.moves_ids)

    def _compute_sales_count(self):
        for consignment in self:
            consignment.sales_count = len(consignment.sale_ids)

    def action_request_approval(self):
        for line in self.order_line:
            if line.product_id.tracking != "none" and line.product_uom_qty != sum(
                line.line_lot_serial_ids.mapped("qty")
            ):
                raise ValidationError(
                    _(
                        "Please select lot/serial for product %s "
                        % (line.product_id.name)
                    )
                )
        self.write({"state": "waiting_approval"})

    def action_approval(self):
        self.write({"state": "approval"})

    def action_open_moves(self):
        move_ids = self.moves_ids
        return {
            "name": _("Stock Moves"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "stock.move",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", move_ids.ids)],
        }

    def action_sale_orders(self):
        return {
            "name": _("Sale Orders"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "sale.order",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", self.sale_ids.ids)],
        }

    def action_open_stock_move_lines(self):
        move_ids = self.moves_ids
        move_line_ids = move_ids.mapped("move_line_ids")
        return {
            "name": _("Stock Move Lines"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "stock.move.line",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", move_line_ids.ids)],
        }

    def action_confirm(self):
        stock_to_transit_ids = self.env["stock.move"]
        if (
            not self.warehouse_id.consignment_location_id
            or not self.warehouse_id.consignment_rount_id
        ):
            raise ValidationError(
                _(
                    "Please assigned consignment location or consignment route in seleted warehouse."
                )
            )

        for line in self.order_line:
            if line.product_id.tracking != "none" and line.product_uom_qty != sum(
                line.line_lot_serial_ids.mapped("qty")
            ):
                raise ValidationError(
                    _(
                        "Please select lot/serail for product %s "
                        % (line.product_id.name)
                    )
                )

        group_id = self.env["procurement.group"].sudo().create({"name": self.name})

        for consignment in self:
            for line in consignment.order_line:
                move_line_ids = []
                line_lot_serial_ids = line.line_lot_serial_ids
                quantity = (
                    sum(line.line_lot_serial_ids.mapped("qty"))
                    if line.product_id.tracking != "none"
                    else line.product_uom_qty
                )

                # create move lines
                if line_lot_serial_ids:
                    for lot in line_lot_serial_ids:
                        move_line_ids.append(
                            [
                                0,
                                0,
                                {
                                    "lot_id": lot.lot_producing_id.id,
                                    "qty_done": lot.qty,
                                    "origin": lot.product_id.name,
                                    "product_id": lot.product_id.id,
                                    "product_uom_id": lot.product_id.uom_id.id,
                                    "location_id": consignment.warehouse_id.lot_stock_id.id,
                                    "location_dest_id": consignment.warehouse_id.consignment_location_id.id,
                                },
                            ]
                        )
                else:
                    # for lot in line_lot_serial_ids:
                    move_line_ids.append(
                        [
                            0,
                            0,
                            {
                                "qty_done": line.product_uom_qty,
                                "origin": line.product_id.name,
                                "product_id": line.product_id.id,
                                "product_uom_id": line.product_id.uom_id.id,
                                "location_id": consignment.warehouse_id.lot_stock_id.id,
                                "location_dest_id": consignment.warehouse_id.consignment_location_id.id,
                            },
                        ]
                    )
                # create move
                stock_to_transit = (
                    self.env["stock.move"]
                    .sudo()
                    .create(
                        {
                            "name": consignment.name,
                            "origin": consignment.name,
                            "product_id": line.product_id.id,
                            "location_id": consignment.warehouse_id.lot_stock_id.id,
                            "location_dest_id": consignment.warehouse_id.consignment_location_id.id,
                            "product_uom_qty": quantity,
                            "product_uom": line.product_id.uom_id.id,
                            "group_id": group_id.id,
                            "move_line_ids": move_line_ids,
                        }
                    )
                )

                # stock_to_transit.move_line_ids.unlink()

                line.move_id = stock_to_transit.id
                stock_to_transit_ids |= stock_to_transit

            stock_to_transit_ids._action_confirm()
            stock_to_transit_ids._action_assign()
            consignment.write(
                {
                    "state": "consignment",
                    "moves_ids": [(4, x) for x in stock_to_transit_ids.ids],
                }
            )

    def action_return_qty(self):
        return_move_ids = self.env["stock.move"]
        order_line_ids = self.order_line.filtered(lambda x: x.available_qty > 0)

        if order_line_ids:
            group_id = self.env["procurement.group"].sudo().create({"name": self.name})

        for line in order_line_ids:
            move_line_ids = []
            if line.line_lot_serial_ids:
                for lot in line.line_lot_serial_ids:
                    move_line_ids.append(
                        [
                            0,
                            0,
                            {
                                "lot_id": lot.lot_producing_id.id,
                                "qty_done": lot.unreserve_qty,
                                "origin": lot.product_id.name,
                                "product_id": lot.product_id.id,
                                "product_uom_id": lot.product_id.uom_id.id,
                                "location_id": self.warehouse_id.consignment_location_id.id,
                                "location_dest_id": self.warehouse_id.lot_stock_id.id,
                            },
                        ]
                    )
            else:
                move_line_ids.append(
                    [
                        0,
                        0,
                        {
                            "qty_done": line.available_qty,
                            "origin": line.product_id.name,
                            "product_id": line.product_id.id,
                            "product_uom_id": line.product_id.uom_id.id,
                            "location_id": self.warehouse_id.lot_stock_id.id,
                            "location_dest_id": self.warehouse_id.consignment_location_id.id,
                        },
                    ]
                )

            return_move_ids |= (
                self.env["stock.move"]
                .sudo()
                .create(
                    {
                        "name": self.name,
                        "origin": self.name,
                        "product_id": line.product_id.id,
                        "location_id": self.warehouse_id.consignment_location_id.id,
                        "location_dest_id": self.warehouse_id.lot_stock_id.id,
                        "product_uom_qty": line.available_qty,
                        "product_uom": line.product_id.uom_id.id,
                        "group_id": group_id.id,
                        "move_line_ids": move_line_ids,
                    }
                )
            )
            # return_move_id.move_line_ids.unlink()

            return_move_ids._action_confirm()
            return_move_ids._action_assign()
            return_move_ids._action_done()
            self.write(
                {"state": "done", "moves_ids": [(4, x) for x in return_move_ids.ids]}
            )

    def action_done(self):
        if all([line.available_qty == 0 for line in self.order_line]):
            self.write({"state": "done"})
        else:
            raise ValidationError(
                _("Before making done. Please either sale or return products")
            )

    def action_assign(self):
        for move in self.moves_ids.filtered(
            lambda x: x.state in ["waiting", "confirmed", "partially_available"]
        ):
            move._action_assign()

    def _compute_bill_count(self):
        for analytic in self:
            analytic.bill_count = len(
                self.env["account.move"].search([("consignment_id", "=", self.id)])
            )

    def action_generate_bill(self):
        invoice_line_list = []
        product_commission = self.env["product.product"]
        consignments_bill = self.env["account.move"]

        journal_domain = [
            ("type", "=", "purchase"),
            ("company_id", "=", self.env.user.company_id.id),
        ]
        journal_id = self.env["account.journal"].search(journal_domain, limit=1)
        income_ids = self.sale_ids.filtered(lambda x: not x.invoiced)
        if not journal_id:
            raise ValidationError(_("Purchase type journal is not found"))
        commission = self.commission or self.partner_id.commission
        if income_ids and commission:
            consignments_bill = self.env["account.move"].create(
                {
                    "move_type": "in_invoice",
                    "partner_id": self.partner_id.id or False,
                    "journal_id": journal_id.id or False,
                    "invoice_line_ids": invoice_line_list or False,
                    "invoice_date": date.today(),
                    "consignment_id": self.id,
                    "consignment_bill": True,
                }
            )
            product_commission = self.env["product.product"].search(
                [("default_code", "=", "commission")], limit=1
            )
            if not product_commission:
                raise ValidationError(
                    _("Please create service type product with default code commission")
                )

            product_ids = income_ids.mapped("order_line").mapped("product_id")
            sale_price = sum(product_ids.mapped("list_price"))
            standard_price = sum(product_ids.mapped("standard_price"))
            commission_price = ((sale_price - standard_price) * commission) / 100
            sale_name = ", ".join(income_ids.mapped("name")) or ""
            name = "%s-%s-%s-%s-%s" % (
                self.partner_id.name,
                product_commission.name,
                commission,
                self.name,
                sale_name,
            )
            if product_commission and commission_price:
                vals = (
                    0,
                    0,
                    {
                        "product_id": product_commission.id or False,
                        "name": name,
                        "quantity": 1,
                        "price_unit": abs(commission_price),
                    },
                )
                invoice_line_list.append(vals)

            # purchase journal
            if consignments_bill:
                consignments_bill.write(
                    {"invoice_line_ids": invoice_line_list or False}
                )
            income_ids.write({"invoiced": True})

    def action_open_bill(self):
        move_id = self.env["account.move"].search([("consignment_id", "=", self.id)])
        return {
            "name": _("Commision Bills"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "account.move",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", move_id.ids)],
        }


class SaleConsignmentLine(models.Model):
    _name = "sale.consignment.line"
    _description = "Sale Consignment Line"

    name = fields.Char(string="Name", related="product_id.name", store=True)
    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.user.company_id
    )
    order_id = fields.Many2one(
        "sale.consignment.order", string="sale Consignment Order"
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        change_default=True,
        ondelete="restrict",
        check_company=True,
    )
    product_uom_qty = fields.Float(
        string="Quantity", digits="Product Unit of Measure", required=True, default=1.0
    )
    sale_qty = fields.Float("Sale Qty", compute="_compute_sale_qty")
    available_qty = fields.Float("Available Qty", compute="_compute_available_qty")
    product_uom = fields.Many2one("uom.uom", string="Unit of Measure")
    price_unit = fields.Float(
        "Unit Price", required=True, digits="Product Price", default=0.0
    )
    tax_ids = fields.Many2many("account.tax", string="Taxes")
    price_subtotal = fields.Float(
        string="Subtotal", compute="_compute_price_subtotal", store=True
    )
    move_id = fields.Many2one("stock.move", string="Stock Move")
    product_tracking = fields.Selection(related="product_id.tracking")
    line_lot_serial_ids = fields.One2many(
        "sale.consignment.line.lot.serial",
        "line_id",
        string="Sale Consignment Line Lot Serial",
    )
    warehouse_id = fields.Many2one(
        "stock.warehouse", related="order_id.warehouse_id", store=True
    )
    order_line_id = fields.Many2one("sale.order.line", string="line")
    free_qty = fields.Float("Available Qty", compute="_compute_free_qty")
    state = fields.Selection(
        [
            ("draft", "Quotation"),
            ("consignment", "Consignment"),
            ("sale", "Sales Order"),
            ("done", "Locked"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        store=True,
        related="order_id.state",
    )
    cost_total = fields.Float("Cost Total", compute="_compute_cost_total")
    profit_total = fields.Float("Profit Total", compute="_compute_profit_total")
    sale_total = fields.Float("Sale Total", compute="_compute_sale_total")

    def _compute_cost_total(self):
        for line in self:
            line.cost_total = line.sale_qty * line.product_id.standard_price

    def _compute_sale_total(self):
        for line in self:
            line.sale_total = line.sale_qty * line.product_id.list_price

    @api.depends("cost_total", "price_subtotal")
    def _compute_profit_total(self):
        for line in self:
            line.profit_total = line.sale_total - line.cost_total

    def _compute_free_qty(self):
        for line in self:
            warehouse_id = line.order_id.warehouse_id.id
            available_quantity = line.product_id.with_context(
                {}, warehouse=warehouse_id
            ).free_qty
            line.free_qty = available_quantity

    def _compute_available_qty(self):
        for line in self:
            order_lines = line.order_id.sale_ids.mapped("order_line")
            order_lines_product = order_lines.filtered(
                lambda x: x.product_id.id == line.product_id.id
                and x.sale_consignment_line_id.id == line.id
            )
            available_qty = line.product_uom_qty - sum(
                order_lines_product.mapped("product_uom_qty")
            )
            line.available_qty = available_qty

    def _compute_sale_qty(self):
        for line in self:
            order_lines = line.order_id.sale_ids.mapped("order_line")
            order_lines_product = order_lines.filtered(
                lambda x: x.product_id.id == line.product_id.id
                and x.sale_consignment_line_id.id == line.id
            )
            line.sale_qty = sum(order_lines_product.mapped("product_uom_qty"))

    def sale_line_lot_serial(self):
        view_id = self.env.ref(
            "pways_so_po_consignment.sale_consignment_line_form_view"
        ).id
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_id": view_id,
            "view_mode": "form",
            "res_model": "sale.consignment.line",
            "target": "new",
            "context": {"create": False},
            "res_id": self.id,
        }

    @api.depends("product_uom_qty", "price_unit")
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.product_uom_qty * line.price_unit

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id.list_price
            self.tax_ids = self.product_id.taxes_id
            self.product_uom = self.product_id.uom_id.id

    def close_action_window(self):
        return True
