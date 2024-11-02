import io
from datetime import date

from odoo import _, api, models
from odoo.tools.misc import xlsxwriter

SECTIONS = {
    "sale": {
        "name": "Ventas",
        "move_type": ("out_invoice", "out_refund"),
        "states": ("posted", "cancel"),
        "lines": {
            "exempt": "Ventas exentas o no gravadas",
            "general": "Ventas internas gravadas por alícuota general",
            "reduced": "Ventas internas gravadas por alícuota reducida",
            "additional": "Ventas internas gravadas por alícuota adicional",
        },
        "withholding": {
            "type": "customer",
            "name": "IVA retenido en ventas",
        },
    },
    "purchase": {
        "name": "Compras",
        "move_type": ("in_invoice", "in_refund"),
        "states": ("posted",),
        "lines": {
            "exempt": "Compras exentas o no gravadas",
            "general": "Compras internas gravadas por alícuota general",
            "reduced": "Compras internas gravadas por alícuota reducida",
            "additional": "Compras internas gravadas por alícuota adicional",
        },
        "withholding": {
            "type": "supplier",
            "name": "IVA retenido en compras",
        },
    },
}


class FiscalBooksReportHandler(models.AbstractModel):
    _name = "account.fiscal.books.report.handler"
    _inherit = "account.report.custom.handler"
    _description = "Libros Fiscales Custom Handler"

    def _custom_options_initializer(self, report, options, previous_options=None):
        opts = super()._custom_options_initializer(
            report, options, previous_options=previous_options
        )
        options["buttons"] += [
            {
                "name": "Generar libro de ventas",
                "action": "datailed_xlsx",
                "action_param": "sale",
                "sequence": 90,
            },
            {
                "name": "Generar libro de compras",
                "action": "datailed_xlsx",
                "action_param": "purchase",
                "sequence": 90,
            },
        ]
        return opts

    def _caret_options_initializer(self):
        return {
            "account.move.line": [
                {
                    "name": "Ver apuntes contables",
                    "action": "caret_option_account_move_line",
                }
            ],
            "account.withholding.iva": [
                {
                    "name": "Ver retenciones",
                    "action": "caret_option_account_withholding_iva",
                }
            ],
        }

    def _dynamic_lines_generator(
        self, report, options, all_column_groups_expression_totals
    ):
        def _get_section_tax_lines(domain):
            balance, tax_base_amount = (
                self.env.company.currency_id.id == fiscal_currency_id.id
                and ("balance", "tax_base_amount")
                or ("balance_ref", "tax_base_amount_ref")
            )
            tables, where_clause, where_params = report._query_get(
                options, "strict_range", domain=domain
            )
            self._cr.execute(
                f"""
                SELECT
                    account_tax.fiscal_tax_type,
                    SUM(
                        CASE
                         WHEN account_move_line.display_type = 'product'
                         THEN ABS(account_move_line.{balance}) *
                         CASE
                          WHEN account_move_line__move_id.move_type
                          IN ('out_refund', 'in_refund')
                          THEN -1
                          ELSE 1
                         END
                        ELSE account_move_line.{tax_base_amount} *
                         CASE
                          WHEN account_move_line__move_id.move_type
                          IN ('out_refund', 'in_refund')
                          THEN -1
                          ELSE 1
                          END
                        END
                    ),
                    SUM(
                        CASE
                         WHEN account_move_line.display_type = 'product'
                         THEN 0.0
                        ELSE
                         ABS(account_move_line.{balance}) *
                         CASE
                          WHEN account_move_line__move_id.move_type
                          IN ('out_refund', 'in_refund')
                          THEN -1
                          ELSE 1
                          END
                        END
                    )
                FROM {tables}
                LEFT JOIN account_move_line_account_tax_rel
                ON account_move_line_account_tax_rel.account_move_line_id = account_move_line.id
                JOIN account_tax
                ON account_tax.id IN (
                    account_move_line.tax_line_id,
                    account_move_line_account_tax_rel.account_tax_id
                )
                WHERE {where_clause} AND ((
                    account_move_line.display_type = 'product'
                    AND account_tax.fiscal_tax_type = 'exempt'
                    ) OR (
                    account_move_line.display_type = 'tax'
                    AND account_tax.fiscal_tax_type != 'exempt'
                ))
                GROUP BY account_tax.fiscal_tax_type
            """,
                where_params,
            )
            return {v[0]: v[1:] for v in self._cr.fetchall()}

        def _get_section_withholding_line(withholding_type):
            self._cr.execute(
                """
                SELECT 0.0, SUM(
                    account_withholding_iva.amount *
                    CASE
                     WHEN account_move.move_type IN ('out_refund', 'in_refund')
                     THEN -1
                    ELSE 1
                    END
                )
                FROM account_withholding_iva
                JOIN account_move
                ON account_move.id = account_withholding_iva.invoice_id
                WHERE
                    account_move.not_in_fiscal_book = FALSE
                    AND account_withholding_iva.state = 'posted'
                    AND account_withholding_iva.type = %s
                    AND account_withholding_iva.date BETWEEN %s AND %s
                    AND account_withholding_iva.company_id IN %s
            """,
                [
                    withholding_type,
                    options["date"]["date_from"],
                    options["date"]["date_to"],
                    tuple(options.get("multi_company", self.env.company.ids)),
                ],
            )
            return self._cr.fetchone()

        lines = []
        fiscal_currency_id = self.env.company.fiscal_currency_id

        for id, section in SECTIONS.items():  # pylint: disable=redefined-builtin
            section_tax_lines = _get_section_tax_lines(
                domain=[
                    ("move_id.move_type", "in", section["move_type"]),
                    ("move_id.not_in_fiscal_book", "=", False),
                ]
            )

            # SECTION LINE
            section_id = report._get_generic_line_id(None, None, markup=id)
            lines.append(
                (
                    0,
                    {
                        "id": section_id,
                        "name": section["name"],
                        "level": 1,
                        "columns": [
                            {
                                "no_format": value,
                                "name": report.format_value(
                                    value,
                                    figure_type="monetary",
                                    currency=fiscal_currency_id,
                                ),
                                "style": "white-space:nowrap;",
                            }
                            for value in [
                                sum(i)
                                for i in zip(*section_tax_lines.values(), strict=True)
                            ]
                        ],
                    },
                )
            )

            # TAX LINES
            for t_type, name in section["lines"].items():
                lines.append(
                    (
                        0,
                        {
                            "id": report._get_generic_line_id(
                                None, None, markup=t_type, parent_line_id=section_id
                            ),
                            "name": name,
                            "caret_options": "account.move.line"
                            if section_tax_lines.get(t_type)
                            else None,
                            "unfoldable": False,
                            "parent_id": section_id,
                            "level": 2,
                            "columns": [
                                {
                                    "no_format": value,
                                    "name": report.format_value(
                                        value,
                                        figure_type="monetary",
                                        currency=fiscal_currency_id,
                                    ),
                                    "style": "white-space:nowrap;",
                                }
                                for value in section_tax_lines.get(t_type, (0, 0))
                            ],
                        },
                    )
                )

            # WITHHOLDING LINE
            withholding_line = _get_section_withholding_line(
                section["withholding"]["type"]
            )
            lines.append(
                (
                    0,
                    {
                        "id": report._get_generic_line_id(
                            None, None, markup=section["withholding"]["type"]
                        ),
                        "name": section["withholding"]["name"],
                        "caret_options": "account.withholding.iva"
                        if withholding_line[1]
                        else None,
                        "level": 2,
                        "columns": [
                            {
                                "no_format": value,
                                "name": report.format_value(
                                    value,
                                    figure_type="monetary",
                                    currency=fiscal_currency_id,
                                ),
                                "style": "white-space:nowrap;",
                            }
                            for value in withholding_line
                        ],
                    },
                )
            )

        return lines

    def caret_option_account_move_line(self, options, params):
        report = self.env["account.report"].browse(options["report_id"])
        section, t_type = (
            report._get_markup(line_id) for line_id in params["line_id"].split("|")[-2:]
        )
        domain = report._get_options_domain(options, "strict_range")
        domain += [
            ("move_id.move_type", "in", SECTIONS[section]["move_type"]),
            ("move_id.not_in_fiscal_book", "=", False),
        ]

        if t_type == "exempt":
            domain += [
                ("display_type", "=", "product"),
                ("tax_ids.fiscal_tax_type", "=", t_type),
            ]
        else:
            domain += [
                ("display_type", "=", "tax"),
                ("tax_line_id.fiscal_tax_type", "=", t_type),
            ]

        return {
            "type": "ir.actions.act_window",
            "name": _("Apuntes contables"),
            "res_model": "account.move.line",
            "views": [[self.env.ref("account.view_move_line_tree").id, "list"]],
            "domain": domain,
        }

    def caret_option_account_withholding_iva(self, options, params):
        report = self.env["account.report"].browse(options["report_id"])
        withholding_type = report._get_markup(params["line_id"])
        return {
            "type": "ir.actions.act_window",
            "name": _("Retenciones"),
            "res_model": "account.withholding.iva",
            "views": [
                [
                    self.env.ref(
                        "l10n_ve_withholding_iva.account_withholding_iva_view_tree"
                    ).id,
                    "list",
                ],
                [False, "form"],
            ],
            "domain": [
                ("state", "=", "posted"),
                ("type", "=", withholding_type),
                ("date", ">=", options["date"]["date_from"]),
                ("date", "<=", options["date"]["date_to"]),
                ("invoice_id.not_in_fiscal_book", "=", False),
                (
                    "company_id",
                    "in",
                    options.get("multi_company", self.env.company.ids),
                ),
            ],
        }

    def datailed_xlsx(self, options, file_type):
        report = self.env["account.report"].browse(options["report_id"])
        options["file_type"] = file_type
        return report.export_file(options, "get_xlsx")

    @api.model
    def get_headers(self, options):
        name = SECTIONS[options["file_type"]]["name"]
        return [
            [
                {"name": "", "colspan": 11},
                {"name": f"{name} internas", "colspan": 11},
                {"name": "Comprobantes de retención IVA", "colspan": 3},
            ],
            [
                {"name": "Nro.", "key": "id"},
                {"name": "Fecha emisión documento", "key": "date"},
                {"name": "Nro. de RIF", "key": "rif"},
                {
                    "name": "Nombre ó razón social",
                    "key": "partner_name",
                    "set_column": 30,
                },
                {"name": "Tipo persona", "key": "partner_code"},
                {"name": "Nro. de control", "key": "nro_ctrl"},
                {"name": "Nro. de factura", "key": "invoice_name"},
                {"name": "Nro. nota de crédito", "key": "refund_name"},
                {"name": "Nro. nota de débito", "key": "debit_name"},
                {"name": "Nro. factura afectada", "key": "affected_name"},
                {"name": "Tipo de transacción", "key": "document_type"},
                {"name": f"{name} incluyendo IVA", "key": "amount_total", "sum": 0.0},
                {
                    "name": f"{name} exentas o no gravadas",
                    "key": "base_exempt",
                    "sum": 0.0,
                },
                {
                    "name": "Base imponible alícuota general",
                    "key": "base_general",
                    "sum": 0.0,
                },
                {"name": "% alícuota general", "key": "tax_general"},
                {
                    "name": "Impuesto alícuota general",
                    "key": "amount_general",
                    "sum": 0.0,
                },
                {
                    "name": "Base imponible alícuota reducida",
                    "key": "base_reduced",
                    "sum": 0.0,
                },
                {"name": "% alícuota reducida", "key": "tax_reduced"},
                {
                    "name": "Impuesto alícuota reducida",
                    "key": "amount_reduced",
                    "sum": 0.0,
                },
                {
                    "name": "Base imponible alícuota adicional",
                    "key": "base_additional",
                    "sum": 0.0,
                },
                {"name": "% alícuota adicional", "key": "tax_additional"},
                {
                    "name": "Impuesto alícuota adicional",
                    "key": "amount_additional",
                    "sum": 0.0,
                },
                {"name": "Nro. de comprobante", "key": "withholding_name"},
                {"name": "IVA retenido", "key": "withholding_amount", "sum": 0.0},
                {"name": "Fecha del Comprobante", "key": "withholding_date"},
            ],
        ]

    @api.model
    def _select(self, options):
        amount_total, tax_base_amount, balance = (
            self.env.company.currency_id.id == self.env.company.fiscal_currency_id.id
            and ("amount_total_signed", "tax_base_amount", "balance")
            or ("amount_total_ref", "tax_base_amount_ref", "balance_ref")
        )

        return (
            f"""
            ROW_NUMBER() OVER(ORDER BY {
                'account_move.nro_ctrl ASC' if options['file_type'] == 'sale'
                else 'account_move.invoice_date ASC'
            }) AS id,
            account_move.invoice_date AS date,
            COALESCE(res_partner.vat, res_partner.identification) AS rif,
            res_partner.name AS partner_name,
            person_type.code AS partner_code,
            account_move.nro_ctrl AS nro_ctrl,
            CASE
                WHEN account_move.move_type = 'out_invoice'
                AND account_move.debit_origin_id IS NULL
                THEN account_move.name
                WHEN account_move.move_type = 'in_invoice'
                AND account_move.debit_origin_id IS NULL
                THEN account_move.supplier_invoice_number
            END AS invoice_name,
            CASE
                WHEN account_move.move_type = 'out_refund'
                THEN account_move.name
                WHEN account_move.move_type = 'in_refund'
                THEN account_move.supplier_invoice_number
            END AS refund_name,
            CASE
                WHEN account_move.move_type = 'out_invoice'
                AND account_move.debit_origin_id IS NOT NULL
                THEN account_move.name
                WHEN account_move.move_type = 'in_invoice'
                AND account_move.debit_origin_id IS NOT NULL
                THEN account_move.supplier_invoice_number
            END AS debit_name,
            CASE
                WHEN account_move.move_type IN ('out_invoice', 'out_refund')
                THEN affected_move.name
                WHEN account_move.move_type IN ('in_invoice', 'in_refund')
                THEN affected_move.supplier_invoice_number
            END AS affected_name,
            CASE
                WHEN account_move.state = 'cancel'
                THEN 'ANU-03'
                WHEN account_move.move_type IN ('out_invoice', 'in_invoice')
                AND account_move.debit_origin_id IS NULL
                THEN 'REG-01'
                WHEN account_move.move_type IN ('out_refund', 'in_refund')
                OR (account_move.move_type IN ('out_invoice', 'in_invoice')
                AND account_move.debit_origin_id IS NOT NULL)
                THEN 'COM-02'
            END AS document_type,
            CASE
                WHEN account_move.state = 'posted'
                AND account_move.invoice_date >= %(date_from)s
                THEN
                    ABS(account_move.{amount_total}) *
                    CASE
                     WHEN account_move.move_type IN ('out_refund', 'in_refund')
                     THEN -1
                     ELSE 1
                    END
                ELSE 0.0
            END AS amount_total,
            SUM(
                CASE
                 WHEN account_move.state = 'posted'
                 AND account_move.invoice_date >= %(date_from)s
                 AND account_move_line.display_type = 'product'
                 AND account_tax.fiscal_tax_type = 'exempt'
                 THEN
                    ABS(account_move_line.{balance}) *
                    CASE
                     WHEN account_move.move_type IN ('out_refund', 'in_refund')
                     THEN -1
                     ELSE 1
                    END
                ELSE 0.0
                END
            ) AS base_exempt,"""
            + ",".join(
                f"""
            SUM(
                CASE
                 WHEN account_move.state = 'posted'
                 AND account_move.invoice_date >= %(date_from)s
                 AND account_move_line.display_type = 'tax'
                 AND account_tax.fiscal_tax_type = %({t})s
                 THEN
                    ABS(account_move_line.{tax_base_amount}) *
                    CASE
                     WHEN account_move.move_type IN ('out_refund', 'in_refund')
                     THEN -1
                     ELSE 1
                    END
                ELSE 0.0
                END
            ) AS base_{t},
            MAX(
                CASE
                 WHEN account_move.state = 'posted'
                 AND account_move.invoice_date >= %(date_from)s
                 AND account_move_line.display_type = 'tax'
                 AND account_tax.fiscal_tax_type = %({t})s
                THEN
                    TO_CHAR(account_tax.amount, '999%%')
                ELSE ''
                END
            ) AS tax_{t},
            SUM(
                CASE
                 WHEN account_move.state = 'posted'
                 AND account_move.invoice_date >= %(date_from)s
                 AND account_move_line.display_type = 'tax'
                 AND account_tax.fiscal_tax_type = %({t})s
                 THEN
                    ABS(account_move_line.{balance}) *
                    CASE
                     WHEN account_move.move_type IN ('out_refund', 'in_refund')
                     THEN -1
                     ELSE 1
                    END
                ELSE 0.0
                END
            ) AS amount_{t}"""
                for t in ("general", "reduced", "additional")
            )
            + """,
            account_withholding_iva.name AS withholding_name,
            COALESCE(account_withholding_iva.amount, 0.0) *
            CASE
             WHEN account_move.move_type IN ('out_refund', 'in_refund')
             THEN -1
             ELSE 1
            END AS withholding_amount,
            account_withholding_iva.date AS withholding_date
        """
        )

    @api.model
    def _from(self, options):
        return """
            account_move
            JOIN res_partner ON res_partner.id = account_move.partner_id
            LEFT JOIN person_type ON person_type.id = res_partner.person_type_id
            LEFT JOIN account_move affected_move
            ON affected_move.id IN (
                account_move.reversed_entry_id, account_move.debit_origin_id)
            JOIN account_move_line
            ON account_move_line.move_id = account_move.id
            LEFT JOIN account_move_line_account_tax_rel
            ON account_move_line_account_tax_rel.account_move_line_id = account_move_line.id
            JOIN account_tax
            ON account_tax.id IN (
                account_move_line.tax_line_id, account_move_line_account_tax_rel.account_tax_id
            )
            LEFT JOIN account_withholding_iva
            ON account_withholding_iva.id = account_move.withholding_iva_id
            AND account_withholding_iva.state = 'posted'
        """

    @api.model
    def _where(self, options):
        return """
            account_move.not_in_fiscal_book = FALSE
            AND account_move.move_type IN %(types)s
            AND account_move.state IN %(states)s
            AND account_move.company_id = %(company)s
            AND (account_move.invoice_date
            BETWEEN %(date_from)s AND %(date_to)s
            OR account_withholding_iva.date
            BETWEEN %(date_from)s AND %(date_to)s)
        """

    @api.model
    def _group_by(self, options):
        return """
            account_move.id, res_partner.id, person_type.id,
            affected_move.id, account_withholding_iva.id
        """

    @api.model
    def _params(self, options):
        return {
            **{t: t for t in ("general", "reduced", "additional")},
            "types": SECTIONS[options["file_type"]]["move_type"],
            "states": SECTIONS[options["file_type"]]["states"],
            "date_from": options["date"]["date_from"],
            "date_to": options["date"]["date_to"],
            "company": tuple(options.get("multi_company", self.env.company.ids)),
        }

    @api.model
    def get_lines(self, options):
        self._cr.execute(
            f"""
            SELECT {self._select(options)}
            FROM {self._from(options)}
            WHERE {self._where(options)}
            GROUP BY {self._group_by(options)}
            ORDER BY {
                'account_move.nro_ctrl ASC'
                if options['file_type'] == 'sale'
                else 'account_move.invoice_date ASC'
            }
        """,
            self._params(options),
        )
        return self._cr.dictfetchall()

    def get_xlsx(self, options, response=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(
            output,
            {
                "in_memory": True,
                "strings_to_formulas": False,
            },
        )

        report_name = "Libro de %s" % SECTIONS[options["file_type"]]["name"]
        sheet = workbook.add_worksheet(report_name)
        bold_style = workbook.add_format(
            {"font_name": "Helvetica Neue", "bold": True, "font_size": 10}
        )
        header_style_1 = workbook.add_format(
            {
                "font_name": "Helvetica Neue",
                "bold": True,
                "font_size": 8,
                "align": "center",
                "valign": "vcenter",
                "bg_color": "#00b050",
                "border": True,
            }
        )
        header_style_2 = workbook.add_format(
            {
                "font_name": "Helvetica Neue",
                "bold": True,
                "font_size": 8,
                "align": "center",
                "valign": "vcenter",
                "bg_color": "#b4c6e7",
                "border": True,
            }
        )
        default_style = workbook.add_format(
            {"font_name": "Helvetica Neue", "font_size": 8, "border": True}
        )
        date_style = workbook.add_format(
            {
                "font_name": "Helvetica Neue",
                "font_size": 8,
                "border": True,
                "num_format": "yyyy-mm-dd",
            }
        )
        total_style = workbook.add_format(
            {
                "font_name": "Helvetica Neue",
                "bold": True,
                "font_size": 8,
                "bg_color": "#aeabab",
                "border": True,
            }
        )

        # COMPANY HEADER
        company_id = self.env.company.partner_id
        sheet.merge_range(
            1, 1, 1, 10, "Nombre de la empresa: " + company_id.name, bold_style
        )
        sheet.merge_range(2, 1, 2, 10, f"RIF.: {company_id.vat}", bold_style)
        sheet.merge_range(
            3,
            1,
            3,
            10,
            "Dirección de la empresa: " + company_id.contact_address.replace("\n", " "),
            bold_style,
        )
        sheet.merge_range(4, 1, 4, 10, report_name.upper(), bold_style)
        sheet.merge_range(
            5, 1, 5, 2, "Desde: " + options["date"]["date_from"], bold_style
        )
        sheet.merge_range(
            5, 3, 5, 10, "Hasta: " + options["date"]["date_to"], bold_style
        )
        y_offset = 7

        headers = self.get_headers(options)
        for header in headers:
            x_offset = 1
            for column in header:
                colspan = column.get("colspan", 1)
                sheet.set_column(y_offset, x_offset, column.get("set_column", 20))
                if column["name"]:
                    if colspan == 1:
                        sheet.write(y_offset, x_offset, column["name"], header_style_2)
                    else:
                        sheet.merge_range(
                            y_offset,
                            x_offset,
                            y_offset,
                            x_offset + colspan - 1,
                            column["name"],
                            header_style_1,
                        )
                x_offset += colspan
            y_offset += 1
        sheet.set_row(y_offset - 1, 30)

        columns = headers[-1]
        for line in self.get_lines(options):
            for x_offset, column in enumerate(columns, 1):
                value = line[column["key"]]
                style = date_style if isinstance(value, date) else default_style
                sheet.write(y_offset, x_offset, value, style)
                if "sum" in column:
                    column["sum"] += value
            y_offset += 1

        for x_offset, column in enumerate(columns, 1):
            sheet.write(y_offset, x_offset, column.get("sum"), total_style)

        y_offset += 2
        sheet.merge_range(
            y_offset,
            1,
            y_offset,
            2,
            "RESUMEN DE %s" % report_name.upper(),
            header_style_1,
        )
        sheet.write(y_offset, 3, "BASE IMPONIBLE", header_style_1)
        sheet.write(y_offset, 4, "DÉBITO/CRÉDITO FISCAL", header_style_1)

        resumen_data = {c["key"]: c["sum"] for c in columns if "sum" in c}
        total_base = total_amount = 0.0
        for key, name in SECTIONS[options["file_type"]]["lines"].items():
            y_offset += 1
            sheet.merge_range(y_offset, 1, y_offset, 2, name, default_style)
            sheet.write(y_offset, 3, resumen_data.get(f"base_{key}"), default_style)
            sheet.write(y_offset, 4, resumen_data.get(f"amount_{key}"), default_style)
            total_base += resumen_data.get(f"base_{key}", 0.0)
            total_amount += resumen_data.get(f"amount_{key}", 0.0)

        y_offset += 1
        sheet.merge_range(
            y_offset,
            1,
            y_offset,
            2,
            "Total %s y débitos/créditos fiscales"
            % SECTIONS[options["file_type"]]["name"].lower(),
            default_style,
        )
        sheet.write(y_offset, 3, total_base, default_style)
        sheet.write(y_offset, 4, total_amount, default_style)

        y_offset += 1
        sheet.merge_range(y_offset, 1, y_offset, 2, "Total IVA retenido", default_style)
        sheet.write(y_offset, 3, None, default_style)
        sheet.write(y_offset, 4, resumen_data.get("withholding_amount"), default_style)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return {
            "file_name": "%s.xlsx" % report_name,
            "file_content": generated_file,
            "file_type": "xlsx",
        }
