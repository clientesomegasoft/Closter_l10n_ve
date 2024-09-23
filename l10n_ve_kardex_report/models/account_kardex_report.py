from odoo import models
from odoo.tools.misc import format_datetime

TYPE_CLASS = {
    "Entrada": "text-success",
    "Salida": "text-danger",
    "Ajuste": "text-warning",
}


class AccountKardexReport(models.AbstractModel):
    _name = "account.kardex.report.handler"
    _description = "Libro de inventario"
    _inherit = "account.report.custom.handler"

    def _custom_options_initializer(self, report, options, previous_options=None):
        opts = super()._custom_options_initializer(
            report, options, previous_options=previous_options
        )
        options["column_headers"][0] = [
            {"name": "", "colspan": 2},
            {"name": "Saldo inicial", "colspan": 3, "forced_options": {}},
            {"name": "Movimiento", "colspan": 3, "forced_options": {}},
            {"name": "Saldo final", "colspan": 3, "forced_options": {}},
        ]
        options["columns"] += options["columns"][2:] * 2
        return opts

    def _dynamic_lines_generator(
        self, report, options, all_column_groups_expression_totals
    ):
        unfolded_lines = options.get("unfolded_lines")
        unfold_all = self._context.get("print_mode") or options.get("unfold_all")
        lines = []

        for product in self._get_product_ids(options):
            line_id = report._get_generic_line_id("product.product", product.id)
            lines.append(
                (
                    0,
                    {
                        "id": line_id,
                        "name": product.display_name,
                        "columns": [],
                        "unfoldable": True,
                        "unfolded": line_id in unfolded_lines or unfold_all,
                        "expand_function": "_report_expand_unfoldable_line_svl",
                        "colspan": 12,
                        "level": 1,
                    },
                )
            )
        return lines

    def _report_expand_unfoldable_line_svl(
        self,
        line_dict_id,
        groupby,
        options,
        progress,
        offset,
        unfold_all_batch_data=None,
    ):
        report = self.env.ref("l10n_ve_kardex_report.kardex_report")
        unfold_all = self._context.get("print_mode") or options.get("unfold_all")
        load_more_counter = 0
        has_more = False
        lines = []

        model, model_id = report._get_model_info_from_id(line_dict_id)
        product_id = self.env[model].browse(model_id)
        uom_name = product_id.uom_id.display_name

        for line in self._get_svl_lines(
            options, product_id, report=report, offset=offset
        ):
            if not unfold_all and load_more_counter == report.load_more_limit:
                has_more = True
                break

            lines.append(
                {
                    "id": report._get_generic_line_id(
                        "stock.valuation.layer", line["id"], parent_line_id=line_dict_id
                    ),
                    "name": format_datetime(self.env, line["create_date"]),
                    "parent_id": line_dict_id,
                    "caret_options": "stock.valuation.layer",
                    "level": 2,
                    "columns": [
                        {"name": line["type"], "class": TYPE_CLASS.get(line["type"])},
                        {"name": uom_name},
                        # SALDO INICIAL
                        {"name": line["init_quantity"]},
                        {
                            "name": report.format_value(
                                line["init_unit_cost"],
                                blank_if_zero=False,
                                figure_type="monetary",
                            )
                        },
                        {
                            "name": report.format_value(
                                line["init_value"],
                                blank_if_zero=False,
                                figure_type="monetary",
                            )
                        },
                        # MOVIMIENTO
                        {"name": line["quantity"]},
                        {
                            "name": report.format_value(
                                line["unit_cost"],
                                blank_if_zero=False,
                                figure_type="monetary",
                            )
                        },
                        {
                            "name": report.format_value(
                                line["value"],
                                blank_if_zero=False,
                                figure_type="monetary",
                            )
                        },
                        # SALDO FINAL
                        {"name": line["end_quantity"]},
                        {
                            "name": report.format_value(
                                line["end_unit_cost"],
                                blank_if_zero=False,
                                figure_type="monetary",
                            )
                        },
                        {
                            "name": report.format_value(
                                line["end_value"],
                                blank_if_zero=False,
                                figure_type="monetary",
                            )
                        },
                    ],
                }
            )
            load_more_counter += 1

        return {
            "lines": lines,
            "offset_increment": load_more_counter,
            "has_more": has_more,
        }

    def _get_product_ids(self, options):
        return self.env["product.product"].browse(
            [
                x["product_id"][0]
                for x in self.env["stock.valuation.layer"].read_group(
                    [
                        ("create_date", ">=", options["date"]["date_from"]),
                        ("create_date", "<=", options["date"]["date_to"]),
                        ("product_id.type", "=", "product"),
                        ("company_id", "=", self.env.company.id),
                    ],
                    ["product_id"],
                    ["product_id"],
                )
            ]
        )

    def _get_svl_lines(self, options, product_id, report=None, offset=None):
        sub_query = """
            SELECT
                svl.id,
                svl.create_date,
                CASE
                    WHEN sm.is_inventory = TRUE OR svl.stock_move_id IS NULL THEN 'Ajuste'
                    WHEN sl.usage != 'internal' AND sld.usage = 'internal' THEN 'Entrada'
                    WHEN sl.usage = 'internal' AND sld.usage != 'internal' THEN 'Salida'
                END AS type,
                COALESCE(svl.quantity, 0.0) AS quantity,
                COALESCE(svl.unit_cost, 0.0) AS unit_cost,
                COALESCE(svl.value, 0.0) AS value,
                COALESCE(SUM(svl.quantity) OVER (PARTITION BY svl.product_id ORDER BY svl.create_date, svl.id), 0.0) AS end_quantity,
                COALESCE(SUM(svl.value) OVER (PARTITION BY svl.product_id ORDER BY svl.create_date, svl.id), 0.0) AS end_value
            FROM stock_valuation_layer svl
            LEFT JOIN stock_move sm ON sm.id = svl.stock_move_id
            LEFT JOIN stock_location sl ON sl.id = sm.location_id
            LEFT JOIN stock_location sld ON sld.id = sm.location_dest_id
            WHERE
                svl.create_date <= %s AND svl.product_id = %s AND svl.company_id = %s
            ORDER BY svl.create_date, svl.id
        """
        where_params = [options["date"]["date_to"], product_id.id, self.env.company.id]

        if offset:
            sub_query += """
                OFFSET %s
                LIMIT %s
            """
            where_params += [offset, report.load_more_limit]

        query = f"""
            SELECT *,
                end_quantity - quantity AS init_quantity,
                end_value - value AS init_value,
                ROUND(COALESCE((end_value - value) / NULLIF((end_quantity - quantity), 0), 0.0), 2) AS init_unit_cost,
                ROUND(COALESCE(end_value / NULLIF(end_quantity, 0), 0.0), 2) AS end_unit_cost
            FROM ({sub_query}) AS RESULT
            WHERE create_date >= %s
        """
        where_params.append(options["date"]["date_from"])

        self._cr.execute(query, where_params)
        return self._cr.dictfetchall()

    def _caret_options_initializer(self):
        return {
            "stock.valuation.layer": [
                {"name": "Abrir valoración", "action": "caret_option_open_record_form"}
            ]
        }
