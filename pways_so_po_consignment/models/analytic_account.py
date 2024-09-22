from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountAnalyticPlan(models.Model):
    _inherit = "account.analytic.plan"

    is_consignment = fields.Boolean(string="Consignment", help="Consignment")


class AccountAsset(models.Model):
    _inherit = "account.move"

    analytic_id = fields.Many2one(
        "account.analytic.account", string="Analytic", copy=False
    )
    consignment_id = fields.Many2one("sale.consignment.order", copy=False)
    consignment_bill = fields.Boolean(copy=False)


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"
    _order = "id desc"

    purchase_order_id = fields.Many2one("purchase.order", string="Purchase", copy=False)
    consignment_ids = fields.One2many(
        "consignments.details", "analytic_id", string="Consignment"
    )
    is_consignments = fields.Boolean(
        string="Consignments", help="Consignments", copy=False
    )
    bill_count = fields.Integer(string="Bill", compute="_compute_bill_count")
    commission = fields.Float(string="Commission (%)")

    def _compute_bill_count(self):
        for analytic in self:
            analytic.bill_count = len(
                self.env["account.move"].search([("analytic_id", "=", self.id)])
            )

    def action_generate_bill(self):
        invoice_line_list = []
        product_commission = self.env["product.product"]

        journal_domain = [
            ("type", "=", "purchase"),
            ("company_id", "=", self.env.user.company_id.id),
        ]
        journal_id = self.env["account.journal"].search(journal_domain, limit=1)
        if not journal_id:
            raise ValidationError(_("Purchase type journal is not found"))

        income_ids = self.consignment_ids.filtered(
            lambda x: x.consignment_type == "income" and not x.is_invoices
        )
        expenses_ids = self.consignment_ids.filtered(
            lambda x: x.consignment_type == "expense" and not x.is_invoices
        )

        consignments_bill = self.env["account.move"].search(
            [
                ("analytic_id", "=", self.id),
                ("move_type", "=", "in_invoice"),
                ("state", "=", "draft"),
            ],
            limit=1,
        )
        if not consignments_bill:
            consignments_bill = self.env["account.move"].create(
                {
                    "move_type": "in_invoice",
                    "partner_id": self.partner_id.id or False,
                    "journal_id": journal_id.id or False,
                    "invoice_line_ids": invoice_line_list or False,
                    "invoice_date": date.today(),
                    "analytic_id": self.id,
                    "purchase_id": self.purchase_order_id.id,
                    "consignment_bill": True,
                }
            )
        if income_ids or expenses_ids:
            if self.commission:
                product_commission = self.env["product.product"].search(
                    [("default_code", "=", "commission")], limit=1
                )
                if not product_commission:
                    raise ValidationError(
                        _(
                            "Please create service type product "
                            "with default code commission"
                        )
                    )
            total_amount = sum(income_ids.mapped("sales"))
            commission_price = (total_amount * self.commission) / 100
            if total_amount and commission_price:
                for line in income_ids:
                    vals = (
                        0,
                        0,
                        {
                            "product_id": line.product_id.id or False,
                            "name": line.product_id.name,
                            "quantity": line.qty,
                            "product_uom_id": line.uom_id.id or False,
                            "price_unit": line.unit_price,
                            "analytic_distribution": {self.id: 100},
                        },
                    )
                    invoice_line_list.append(vals)

                for line in expenses_ids:
                    vals = (
                        0,
                        0,
                        {
                            "product_id": line.product_id.id or False,
                            "name": line.product_id.name,
                            "quantity": line.qty,
                            "product_uom_id": line.uom_id.id or False,
                            "price_unit": -abs(line.unit_price),
                            "analytic_distribution": {self.id: 100},
                        },
                    )
                    invoice_line_list.append(vals)

                if self.commission and income_ids:
                    total_amount = sum(income_ids.mapped("sales"))
                    commission_price = (total_amount * self.commission) / 100
                    vals = (
                        0,
                        0,
                        {
                            "product_id": product_commission.id or False,
                            "name": product_commission.name,
                            "quantity": 1,
                            "price_unit": -abs(commission_price),
                            "analytic_distribution": {self.id: 100},
                        },
                    )
                    invoice_line_list.append(vals)

                # purchase journal
                if consignments_bill:
                    consignments_bill.write(
                        {"invoice_line_ids": invoice_line_list or False}
                    )
                self.consignment_ids.write({"is_invoices": True})

    def action_open_bill(self):
        move_id = self.env["account.move"].search([("analytic_id", "=", self.id)])
        return {
            "name": _("Commision Bills"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "account.move",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", move_id.ids)],
        }


class ConsignmentsDetails(models.Model):
    _name = "consignments.details"

    analytic_id = fields.Many2one("account.analytic.account", string="Analytic")
    product_id = fields.Many2one("product.product", string="Product")
    description = fields.Char(string="Desc", related="product_id.name")
    date = fields.Date(string="Date", default=fields.Date.today())
    consignment_type = fields.Selection(
        [("income", "Income"), ("expense", "Expense")], string="Type"
    )
    qty = fields.Float(string="Qty")
    uom_id = fields.Many2one("uom.uom", string="Uom")
    unit_price = fields.Float(string="Price")
    sales = fields.Float(string="Total Amount", compute="_compute_sales", store=True)
    others_expense = fields.Float(string="Expenses")
    sale_id = fields.Many2one("sale.order", string="Sale")
    is_invoices = fields.Boolean(string="Invoiced")
    expenses_id = fields.Many2one("expenses.details", string="Expenses")
    purchase_order_line_id = fields.Many2one("purchase.order.line", string="Purchase")

    @api.depends("unit_price", "qty")
    def _compute_sales(self):
        for line in self:
            line.sales = line.qty * line.unit_price
