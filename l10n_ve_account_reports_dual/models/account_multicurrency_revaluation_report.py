# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import chain

from odoo import models


class MulticurrencyRevaluationReportCustomHandler(models.AbstractModel):
    _inherit = "account.multicurrency.revaluation.report.handler"

    def _multi_currency_revaluation_get_custom_lines(
        self, options, line_code, current_groupby, next_groupby, offset=0, limit=None
    ):
        def build_result_dict(report, query_res):
            foreign_currency = (
                self.env["res.currency"].browse(query_res["currency_id"][0])
                if len(query_res["currency_id"]) == 1
                else None
            )

            return {
                "balance_currency": report.format_value(
                    query_res["balance_currency"],
                    currency=foreign_currency,
                    figure_type="monetary",
                ),
                "balance_operation": query_res["balance_operation"],
                "balance_current": query_res["balance_current"],
                "adjustment": query_res["adjustment"],
                "has_sublines": query_res["aml_count"] > 0,
            }

        report = self.env["account.report"].browse(options["report_id"])
        report._check_groupby_fields(
            (next_groupby.split(",") if next_groupby else [])
            + ([current_groupby] if current_groupby else [])
        )

        # No need to run any SQL if we're computing the main line: it does not display any total
        if not current_groupby:
            return {
                "balance_currency": None,
                "balance_operation": None,
                "balance_current": None,
                "adjustment": None,
                "has_sublines": False,
            }

        query = "(VALUES {})".format(
            ", ".join("(%s, %s)" for rate in options["currency_rates"])
        )
        params = list(
            chain.from_iterable(
                (cur["currency_id"], cur["rate"])
                for cur in options["currency_rates"].values()
            )
        )
        custom_currency_table_query = self.env.cr.mogrify(query, params).decode(
            self.env.cr.connection.encoding
        )

        tables, where_clause, where_params = report._query_get(options, "strict_range")
        tail_query, tail_params = report._get_engine_query_tail(offset, limit)

        full_query = (
            f"""
            WITH custom_currency_table(currency_id, rate) AS ({custom_currency_table_query})

            SELECT
                subquery.grouping_key,
                ARRAY_AGG(DISTINCT(subquery.currency_id)) AS currency_id,
                SUM(subquery.balance_currency) AS balance_currency,
                SUM(subquery.balance_operation) AS balance_operation,
                SUM(subquery.balance_current) AS balance_current,
                SUM(subquery.adjustment) AS adjustment,
                COUNT(subquery.aml_id) AS aml_count
            FROM (

                SELECT
                    """
            + (
                f"account_move_line.{current_groupby} AS grouping_key,"
                if current_groupby
                else ""
            )
            + f"""
                    account_move_line.amount_residual AS balance_operation,
                    account_move_line.amount_residual_currency AS balance_currency,
                    account_move_line.amount_residual_currency / custom_currency_table.rate AS balance_current,
                    account_move_line.amount_residual_currency / custom_currency_table.rate - account_move_line.amount_residual AS adjustment,
                    account_move_line.currency_id AS currency_id,
                    account_move_line.id AS aml_id
                FROM {tables}
                JOIN account_account account ON account_move_line.account_id = account.id
                JOIN res_currency currency ON currency.id = account_move_line.currency_id
                JOIN custom_currency_table ON custom_currency_table.currency_id = currency.id
                WHERE {where_clause}
                    AND (account.currency_id != account_move_line.company_currency_id OR (account.account_type IN ('asset_receivable', 'liability_payable') AND (account_move_line.currency_id != account_move_line.company_currency_id)))
                    AND (account_move_line.amount_residual != 0 OR account_move_line.amount_residual_currency != 0)
                    AND {'NOT EXISTS' if line_code == 'to_adjust' else 'EXISTS'} (
                        SELECT * FROM account_account_exclude_res_currency_provision WHERE account_account_id = account_id AND res_currency_id = account_move_line.currency_id
                    )

                UNION ALL

                -- Add the lines without currency, i.e. payment in company currency for invoice in foreign currency
                SELECT
                    """
            + (
                f"account_move_line.{current_groupby} AS grouping_key,"
                if current_groupby
                else ""
            )
            + f"""
                    -part.amount AS balance_operation,
                    CASE
                       WHEN account_move_line.id = part.credit_move_id THEN -part.debit_amount_currency
                       ELSE -part.credit_amount_currency
                    END AS balance_currency,
                    CASE
                       WHEN account_move_line.id = part.credit_move_id THEN -part.debit_amount_currency
                       ELSE -part.credit_amount_currency
                    END / custom_currency_table.rate AS balance_current,
                    CASE
                       WHEN account_move_line.id = part.credit_move_id THEN -part.debit_amount_currency
                       ELSE -part.credit_amount_currency
                    END / custom_currency_table.rate - account_move_line.balance AS adjustment,
                    CASE
                       WHEN account_move_line.id = part.credit_move_id THEN part.debit_currency_id
                       ELSE part.credit_currency_id
                    END AS currency_id,
                    account_move_line.id AS aml_id
                FROM {tables}
                JOIN account_account account ON account_move_line.account_id = account.id
                JOIN account_partial_reconcile part ON account_move_line.id = part.credit_move_id OR account_move_line.id = part.debit_move_id
                JOIN res_currency currency ON currency.id = (CASE WHEN account_move_line.id = part.credit_move_id THEN part.debit_currency_id ELSE part.credit_currency_id END)
                JOIN custom_currency_table ON custom_currency_table.currency_id = currency.id
                WHERE {where_clause}
                    AND (account.currency_id = account_move_line.company_currency_id AND (account.account_type IN ('asset_receivable', 'liability_payable') AND account_move_line.currency_id = account_move_line.company_currency_id))
                    AND (account_move_line.amount_residual != 0 OR account_move_line.amount_residual_currency != 0)
                    AND {'NOT EXISTS' if line_code == 'to_adjust' else 'EXISTS'} (
                        SELECT * FROM account_account_exclude_res_currency_provision WHERE account_account_id = account_id AND res_currency_id = account_move_line.currency_id
                    )
            ) subquery

            GROUP BY grouping_key
            {tail_query}
        """
        )

        self._cr.execute(full_query, (where_params * 2) + tail_params)
        query_res_lines = self._cr.dictfetchall()

        if not current_groupby:
            return build_result_dict(
                report, query_res_lines and query_res_lines[0] or {}
            )
        else:
            rslt = []
            for query_res in query_res_lines:
                grouping_key = query_res["grouping_key"]
                rslt.append((grouping_key, build_result_dict(report, query_res)))
            return rslt
