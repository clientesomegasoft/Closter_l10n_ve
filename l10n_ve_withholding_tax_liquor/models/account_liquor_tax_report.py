from odoo import Command, api, fields, models


class AccountLiquourTaxReport(models.Model):
    _name = "account.liquor.tax.report"
    _description = "Reporte impuesto sobre venta de licor"

    name = fields.Char(
        string="Nombre",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        [("draft", "Borrador"), ("confirmed", "Confirmado"), ("paid", "Pagado")],
        string="Estado",
        default="draft",
        required=True,
        readonly=True,
        copy=False,
    )
    date_from = fields.Date(
        string="Desde",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date_to = fields.Date(
        string="Hasta",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    line_ids = fields.One2many(
        "account.liquor.tax.report.line", "report_id", string="Lineas", readonly=True
    )
    amount = fields.Monetary(string="Total", compute="_compute_amount", store=True)
    currency_id = fields.Many2one(
        "res.currency", related="company_id.fiscal_currency_id", store=True
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
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
            SELECT account_liquor_tax.id, account_liquor_tax.rate, ARRAY_AGG(account_move_line.id)
            FROM liquor_tax_move_line_rel
            JOIN account_liquor_tax ON account_liquor_tax.id = liquor_tax_move_line_rel.tax_id
            JOIN account_move_line ON account_move_line.id = liquor_tax_move_line_rel.line_id
            JOIN account_move ON account_move.id = account_move_line.move_id
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
            for l in move_line_ids:
                price_subtotal = l.company_currency_id.round(
                    l.price_subtotal / l.currency_rate
                )
                if not is_company_currency:
                    price_subtotal = l.currency_ref_id.round(
                        price_subtotal * l.currency_rate_ref.rate
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
    _description = "Lineas reporte impuesto sobre venta de licor"

    report_id = fields.Many2one(
        "account.liquor.tax.report", required=True, ondelete="cascade"
    )
    liquor_tax_id = fields.Many2one(
        "account.liquor.tax", string="Impuesto", required=True
    )
    rate = fields.Float(string="Porcentaje")
    base_amount = fields.Monetary(string="Base imponible")
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
            "Solo se puede tener una linea por tipo de impuesto",
        )
    ]

    @api.depends("rate", "base_amount")
    def _compute_amount(self):
        for line in self:
            line.amount = line.currency_id.round(line.base_amount * line.rate / 100)
