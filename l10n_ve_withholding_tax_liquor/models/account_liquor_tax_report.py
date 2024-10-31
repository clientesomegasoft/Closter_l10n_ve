from odoo import Command, api, fields, models


class AccountLiquourTaxReport(models.Model):
    _name = "account.liquor.tax.report"
    _description = "Report tax on liquor sales"

    name = fields.Char(
        string="Name",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("paid", "Paid")],
        string="State",
        default="draft",
        required=True,
        readonly=True,
        copy=False,
    )
    date_from = fields.Date(
        string="From",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_to = fields.Date(
        string="To",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    line_ids = fields.One2many(
        "account.liquor.tax.report.line", "report_id", string="Lines", readonly=True
    )
    amount = fields.Monetary(string="Total", compute="_compute_amount", store=True)
    currency_id = fields.Many2one(
        "res.currency", related="company_id.fiscal_currency_id", store=True
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company.id,
        readonly=True,
    )

    @api.depends("line_ids.base_amount", "line_ids.amount")
    def _compute_amount(self):
        for report_id in self:
            report_id.amount = sum(report_id.line_ids.mapped("amount"))

    def seek_for_lines(self):
        self._cr.execute(
            """
            SELECT
            account_liquor_tax.id, account_liquor_tax.rate, ARRAY_AGG(account_move_line.id)
            FROM liquor_tax_move_line_rel
            JOIN account_liquor_tax
            ON account_liquor_tax.id = liquor_tax_move_line_rel.tax_id
            JOIN account_move_line
            ON account_move_line.id = liquor_tax_move_line_rel.line_id
            JOIN account_move
            ON account_move.id = account_move_line.move_id
            WHERE
                account_move.move_type IN ('out_invoice', 'out_refund')
                AND account_move_line.parent_state = 'posted'
                AND account_move_line.date BETWEEN %s AND %s
                AND account_move_line.company_id = %s
            GROUP BY account_liquor_tax.id
        """,
            [self.date_from, self.date_to, self.company_id.id],
        )

        rows = self._cr.fetchall()
        is_company_currency = self.currency_id == self.company_id.currency_id
        report_lines = [Command.clear()]

        for tax_id, rate, line_ids in rows:
            move_line_ids = self.env["account.move.line"].browse(line_ids)

            base_amount = 0.0
            for line in move_line_ids:
                price_subtotal = line.company_currency_id.round(
                    line.price_subtotal / line.currency_rate
                )
                if not is_company_currency:
                    price_subtotal = line.currency_ref_id.round(
                        price_subtotal * line.currency_rate_ref.rate
                    )
                base_amount += price_subtotal

            values = {
                "report_id": self.id,
                "liquor_tax_id": tax_id,
                "rate": rate,
                "base_amount": base_amount,
            }

            report_lines.append(Command.create(values))

        self.line_ids = report_lines

    def button_draft(self):
        self.write({"state": "draft"})

    def button_confirm(self):
        self.write({"state": "confirmed"})

    def button_pay(self):
        self.write({"state": "paid"})


class AccountLiquourTaxReportLine(models.Model):
    _name = "account.liquor.tax.report.line"
    _description = "Lines report tax on liquor sales"

    report_id = fields.Many2one(
        "account.liquor.tax.report", required=True, ondelete="cascade"
    )
    liquor_tax_id = fields.Many2one(
        "account.liquor.tax", string="Impuesto", required=True
    )
    rate = fields.Float(string="Percentage")
    base_amount = fields.Monetary(string="Taxable base")
    amount = fields.Monetary(string="Total", compute="_compute_amount", store=True)
    currency_id = fields.Many2one(
        "res.currency", related="company_id.fiscal_currency_id", store=True
    )
    company_id = fields.Many2one(
        "res.company", related="report_id.company_id", store=True
    )

    _sql_constraints = [
        (
            "unique_liquor_tax_per_report",
            "UNIQUE(report_id, liquor_tax_id)",
            "You can only have one line per tax type",
        )
    ]

    @api.depends("rate", "base_amount")
    def _compute_amount(self):
        for line in self:
            line.amount = line.currency_id.round(line.base_amount * line.rate / 100)
