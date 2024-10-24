from dateutil.relativedelta import relativedelta

from odoo import fields, models
from odoo.tools.misc import format_date


class ReportArc(models.AbstractModel):
    _name = "account.arc.report.handler"
    _inherit = "account.report.custom.handler"
    _description = "Reporte ARC-Venezuela"

    def _get_months_table(self, options):
        months_table = "(VALUES %s) AS months_table(date_from, date_to)" % ",".join(
            ["(%s, %s)"] * 12
        )
        params = []
        for month in range(1, 13):
            date_from = fields.Date.from_string(
                "{}-{}-01".format(options["year"], month)
            )
            date_to = date_from + relativedelta(day=31)
            params += [date_from, date_to]
        return self.env.cr.mogrify(months_table, params).decode(
            self.env.cr.connection.encoding
        )

    def _dynamic_lines_generator(
        self, report, options, all_column_groups_expression_totals
    ):
        if not options.get("partner_id"):
            return []

        fiscal_currency_id = self.env.company.fiscal_currency_id
        sql = """
            SELECT
                months_table.date_from AS month,
                COALESCE(SUM(ABS(account_move.{amount_total})), 0.0) AS total_invoice,
                COALESCE(SUM(account_withholding_islr.base_amount), 0.0) AS base,
                COALESCE(SUM(account_withholding_islr.amount), 0.0) AS amount
            FROM {months_table}
            LEFT JOIN account_withholding_islr ON
                account_withholding_islr.date
                BETWEEN months_table.date_from AND months_table.date_to
                AND account_withholding_islr.subject_id = {partner_id}
                AND account_withholding_islr.type = 'supplier'
                AND account_withholding_islr.state = 'posted'
                AND account_withholding_islr.company_id = {company_id}
            LEFT JOIN account_move ON
                account_move.id = account_withholding_islr.invoice_id
            GROUP BY month
            ORDER BY month
        """
        self._cr.execute(
            sql,
            (
                tuple(
                    amount_total=self.env.company.currency_id == fiscal_currency_id
                    and "amount_total_signed"
                    or "amount_total_ref",
                    months_table=self._get_months_table(options),
                    partner_id=options["partner_id"]["id"],
                    company_id=self.env.company.id,
                ),
            ),
        )

        lines = []
        sum_base = sum_amount = sum_total_invoice = 0.0
        for month in self._cr.dictfetchall():
            sum_base += month["base"]
            sum_amount += month["amount"]
            sum_total_invoice += month["total_invoice"]
            lines.append(
                (
                    0,
                    {
                        "id": report._get_generic_line_id(
                            None, None, markup=month["month"]
                        ),
                        "name": format_date(
                            self.env, month["month"], date_format="MMMM"
                        ).capitalize(),
                        "caret_options": "account.withholding.islr",
                        "columns": [
                            {
                                "name": report.format_value(
                                    month["total_invoice"],
                                    currency=fiscal_currency_id,
                                    figure_type="monetary",
                                )
                            },
                            {
                                "name": report.format_value(
                                    month["base"],
                                    currency=fiscal_currency_id,
                                    figure_type="monetary",
                                )
                            },
                            {
                                "name": report.format_value(
                                    month["amount"],
                                    currency=fiscal_currency_id,
                                    figure_type="monetary",
                                )
                            },
                            {
                                "name": report.format_value(
                                    sum_base,
                                    currency=fiscal_currency_id,
                                    figure_type="monetary",
                                )
                            },
                            {
                                "name": report.format_value(
                                    sum_amount,
                                    currency=fiscal_currency_id,
                                    figure_type="monetary",
                                )
                            },
                        ],
                    },
                )
            )
        lines.append(
            (
                0,
                {
                    "id": report._get_generic_line_id(None, None, markup="total"),
                    "name": "Total",
                    "class": "total",
                    "level": 1,
                    "columns": [
                        {
                            "name": report.format_value(
                                sum_total_invoice, currency=fiscal_currency_id
                            )
                        },
                        {
                            "name": report.format_value(
                                sum_base, currency=fiscal_currency_id
                            )
                        },
                        {
                            "name": report.format_value(
                                sum_amount, currency=fiscal_currency_id
                            )
                        },
                    ],
                },
            )
        )
        return lines

    def _caret_options_initializer(self):
        return {
            "account.withholding.islr": [
                {"name": "Ver retenciones", "action": "view_withholding_entries"}
            ]
        }

    def view_withholding_entries(self, options, params):
        report = self.env["account.report"].browse(options["report_id"])
        date_from = fields.Date.from_string(report._get_markup(params["line_id"]))
        return {
            "type": "ir.actions.act_window",
            "name": "ISLR - %s" % options["partner_id"]["name"],
            "res_model": "account.withholding.islr",
            "views": [
                [
                    self.env.ref(
                        "l10n_ve_withholding_islr.account_withholding_islr_view_tree"
                    ).id,
                    "list",
                ],
                [False, "form"],
            ],
            "domain": [
                ("date", ">=", date_from),
                ("date", "<=", date_from + relativedelta(day=31)),
                ("subject_id", "=", options["partner_id"]["id"]),
                ("state", "=", "posted"),
                ("type", "=", "supplier"),
            ],
            "context": {"default_type": "supplier", "create": False},
        }
