from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"  # pylint: disable=consider-merging-classes-inherited

    is_consignment = fields.Boolean(string="Consignment", help="Consignment")
    is_consignments = fields.Boolean(string="Consignments", help="Consignments")
    commission = fields.Float(string="Commission (%)")
    expenses_ids = fields.One2many(
        "expenses.details", "purchase_expense_id", string="Expenses Details"
    )
    account_analytic_id = fields.Many2one("account.analytic.account")

    @api.model
    def create(self, vals):
        res = super(__class__, self).create(vals)
        if res["is_consignments"]:
            res["name"] = (
                self.env["ir.sequence"].next_by_code("purchase.consignments") or "/"
            )
        return res

    def button_confirm(self):
        res = super(__class__, self).button_confirm()
        consignments_data = []
        if self.is_consignments:
            plan_id = self.env["account.analytic.plan"].search(
                [("is_consignment", "=", "True")], limit=1
            )
            if not plan_id:
                raise ValidationError(_("Please set analytic plan for consignment"))
            analytic_id = self.env["account.analytic.account"].search(
                [("purchase_order_id", "=", self.id)], limit=1
            )
            if not analytic_id:
                analytic_id = self.env["account.analytic.account"].create(
                    {
                        "name": f"{self.name}-cm-{self.partner_id.name}",
                        "partner_id": self.partner_id.id,
                        "purchase_order_id": self.id,
                        "is_consignments": True,
                        "commission": self.commission,
                        "plan_id": plan_id.id,
                    }
                )
                if analytic_id:
                    self.account_analytic_id = analytic_id.id
                    self.order_line.analytic_distribution = {analytic_id.id: 100}
            # add expenses
            for line in self.expenses_ids.filtered(lambda x: not x.closing_done):
                d_vals = {
                    "product_id": line.product_id.id,
                    "description": line.product_id.name,
                    "consignment_type": "expense",
                    "qty": line.qty,
                    "uom_id": line.product_id.uom_id.id,
                    "unit_price": line.unit_price,
                    "others_expense": line.unit_price,
                    "expenses_id": line.id,
                }
                consignments_data.append((0, 0, d_vals))
            analytic_id.consignment_ids = consignments_data
            self.expenses_ids.closing_done = True
        return res


class ExpensesDetails(models.Model):
    _name = "expenses.details"
    _description = "Expenses Details"

    purchase_expense_id = fields.Many2one("purchase.order", string="Purchase")
    product_id = fields.Many2one("product.product", string="Product")
    date = fields.Date(
        string="Date", default=fields.Date.today(), readonly=True, help="Date"
    )
    account_id = fields.Many2one("account.account", string="Account")
    unit_price = fields.Float(string="Unit Price")
    qty = fields.Float(string="Quantity", default="1")
    uom_id = fields.Many2one(
        "uom.uom", string="Product UOM", related="product_id.uom_id"
    )
    subtotal = fields.Float(string="Sub Total", store=True, compute="_compute_subtotal")
    closing_done = fields.Boolean(string="Closing Done")

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            self.unit_price = self.product_id.list_price

    @api.depends("unit_price", "qty")
    def _compute_subtotal(self):
        for expenses in self:
            expenses.subtotal = expenses.qty * expenses.unit_price

    @api.model
    def create(self, vals):
        res = super(__class__, self).create(vals)
        analytic_id = res.purchase_expense_id.account_analytic_id
        if analytic_id:
            consignments_data = []
            d_vals = {
                "product_id": res.product_id.id,
                "description": res.product_id.name,
                "consignment_type": "expense",
                "qty": res.qty,
                "uom_id": res.product_id.uom_id.id,
                "unit_price": res.unit_price,
                "others_expense": res.unit_price,
                "expenses_id": self.id,
            }
            consignments_data.append((0, 0, d_vals))
            analytic_id.consignment_ids = consignments_data
            res.closing_done = True
        return res

    def unlink(self):
        for order in self:
            analytic_id = self.purchase_expense_id.account_analytic_id
            if analytic_id:
                consignment_id = analytic_id.consignment_ids.filtered(
                    lambda x: x.expenses_id.id == order.id
                )
                consignment_id.unlink()
        return super(__class__, self).unlink()


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    location_id = fields.Many2one("stock.location", "Location", copy=False)

    def _prepare_stock_moves(self, picking):
        res = super(__class__, self)._prepare_stock_moves(picking)
        if self.location_id:
            for val in res:
                val["location_dest_id"] = self.location_id and self.location_id.id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        if self.order_id.account_analytic_id:
            lines.analytic_distribution = {self.order_id.account_analytic_id.id: 100}
        return lines
