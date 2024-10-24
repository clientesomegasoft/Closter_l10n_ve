from odoo import api, fields, models


class PaidSalesAllocation(models.Model):
    _name = "paid.sales.allocation"
    _description = "Paid sales allocation"

    contract_id = fields.Many2one("hr.contract", string="Contract")
    employee_id = fields.Many2one("hr.employee", string="Employee")
    invoice_id = fields.Many2one("account.move", string="Invoice")
    invoice_state = fields.Selection(related="invoice_id.state", store=True)
    department_id = fields.Many2one(related="invoice_id.department_id")
    date = fields.Datetime(string="Date")
    payment_date = fields.Date(string="Payment date", readonly=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Pending"),
            ("processed", "Processed"),
            ("paid", "Paid"),
            ("cancel", "Cancel"),
        ],
        string="State",
        default="pending",
    )
    assignment = fields.Monetary(string="Assignment")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    is_manual_commission = fields.Boolean()

    @api.constrains("invoice_state")
    def _constrains_invoice_state(self):
        for rec in self:
            if rec.state not in ("paid", "cancel") and rec.invoice_state in (
                "draft",
                "cancel",
            ):
                rec.state = "cancel"
