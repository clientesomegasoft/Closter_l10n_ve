from odoo import Command, api, fields, models


class GrossIncomeReport(models.Model):
    _name = "gross.income.report"
    _description = "Reporte de Ingresos Brutos"

    name = fields.Char(
        string="Descripción",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        [("draft", "Borrador"), ("posted", "Publicado"), ("cancel", "Cancelado")],
        string="Estado",
        default="draft",
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
    town_hall_id = fields.Many2one(
        "res.town.hall",
        string="Alcaldía",
        default=lambda self: self.env.company.town_hall_id,
        required=True,
        readonly=True,
    )
    percentage = fields.Float(related="town_hall_id.percentage", store=True)
    line_ids = fields.One2many(
        "gross.income.report.line", "report_id", string="Líneas", readonly=True
    )
    amount_total = fields.Monetary(
        string="Total", compute="_compute_amount", store=True
    )
    amount_tax = fields.Monetary(
        string="Monto a declarar", compute="_compute_amount", store=True
    )
    move_id = fields.Many2one("account.move", string="Asiento", readonly=True)
    currency_id = fields.Many2one(
        related="company_id.fiscal_currency_id", string="Moneda", store=True
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
        readonly=True,
    )

    @api.depends("line_ids.balance", "percentage")
    def _compute_amount(self):
        for rec in self:
            amount = sum(rec.line_ids.mapped("balance"))
            rec.amount_total = amount
            rec.amount_tax = amount * rec.percentage / 100

    def seek_for_lines(self):
        balance = (
            self.currency_id.id == self.company_id.currency_id.id
            and "balance"
            or "balance_ref"
        )
        self.line_ids = [Command.clear()] + [
            Command.create(
                {
                    "report_id": self.id,
                    "account_id": line["account_id"][0],
                    "balance": -line[balance],
                }
            )
            for line in self.env["account.move.line"].read_group(
                domain=[
                    ("account_id.internal_group", "=", "income"),
                    ("date", ">=", self.date_from),
                    ("date", "<=", self.date_to),
                    ("company_id", "=", self.company_id.id),
                ],
                fields=["account_id", f"{balance}:sum"],
                groupby=["account_id"],
            )
        ]

    def button_draft(self):
        if self.move_id:
            self.move_id.button_draft()
        self.write({"state": "draft"})

    def button_post(self):
        date = fields.Date.today()
        amount_currency = self.currency_id.round(self.amount_tax)
        balance = self.currency_id._convert(
            amount_currency, self.company_id.currency_id, self.company_id, date
        )
        line_ids = [
            {
                "name": self.name,
                "partner_id": self.town_hall_id.partner_id.id,
                "currency_id": self.currency_id.id,
                "amount_currency": amount_currency,
                "balance": balance,
                "account_id": self.town_hall_id.expence_account_id.id,
            },
            {
                "name": self.name,
                "partner_id": self.town_hall_id.partner_id.id,
                "currency_id": self.currency_id.id,
                "amount_currency": -amount_currency,
                "balance": -balance,
                "account_id": self.town_hall_id.payable_account_id.id,
            },
        ]
        expence_account_id = self.move_id.line_ids.filtered(
            lambda line: line.account_id.id == self.town_hall_id.expence_account_id.id
        )
        payable_account_id = self.move_id.line_ids.filtered(
            lambda line: line.account_id.id == self.town_hall_id.payable_account_id.id
        )
        line_ids_commands = [
            Command.update(expence_account_id.id, line_ids[0])
            if expence_account_id
            else Command.create(line_ids[0]),
            Command.update(payable_account_id.id, line_ids[1])
            if payable_account_id
            else Command.create(line_ids[1]),
        ]
        move_values = {
            "move_type": "entry",
            "ref": self.name,
            "date": date,
            "journal_id": self.company_id.out_municipal_journal_id.id,
            "currency_id": self.currency_id.id,
            "company_id": self.company_id.id,
            "line_ids": line_ids_commands,
        }
        if not self.move_id:
            self.move_id = self.env["account.move"].create(move_values)
        else:
            self.move_id.write(move_values)
        self.write({"state": "posted"})

    def button_cancel(self):
        if self.move_id:
            if self.move_id.state == "posted":
                self.move_id._reverse_moves(
                    [
                        {
                            "date": fields.Date.context_today(self),
                            "ref": "Reverso de: " + self.move_id.name,
                        }
                    ],
                    cancel=True,
                )
                self.move_id = False
            elif self.move_id.state == "draft":
                self.move_id.button_cancel()
        self.write({"state": "cancel"})

    def button_open_journal_entry(self):
        self.ensure_one()
        return {
            "name": "Asiento",
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "context": {"create": False},
            "view_mode": "form",
            "res_id": self.move_id.id,
        }


class GrossIncomeReportLine(models.Model):
    _name = "gross.income.report.line"
    _description = "Lineas Reporte de Ingresos Brutos"
    _rec_name = "account_id"

    report_id = fields.Many2one(
        "gross.income.report", required=True, ondelete="cascade"
    )
    account_id = fields.Many2one("account.account", string="Cuenta", required=True)
    balance = fields.Monetary(string="Balance", default=0.0)
    currency_id = fields.Many2one(related="company_id.fiscal_currency_id", store=True)
    company_id = fields.Many2one(related="report_id.company_id", store=True)
