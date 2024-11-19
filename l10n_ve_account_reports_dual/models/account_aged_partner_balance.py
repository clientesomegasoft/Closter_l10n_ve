from itertools import chain

from dateutil.relativedelta import relativedelta

from odoo import fields, models


class AgedPartnerBalanceCustomHandler(models.AbstractModel):
    _inherit = "account.aged.partner.balance.report.handler"

    def _aged_partner_report_custom_engine_common(
        self,
        options,
        internal_type,
        current_groupby,
        next_groupby,
        offset=0,
        limit=None,
    ):
        if options.get("selected_currency") != self.env.company.currency_ref_id.id:
            return super(__class__, self)._aged_partner_report_custom_engine_common(
                options, internal_type, current_groupby, next_groupby, offset, limit
            )

        report = self.env["account.report"].browse(options["report_id"])
        report._check_groupby_fields(
            (next_groupby.split(",") if next_groupby else [])
            + ([current_groupby] if current_groupby else [])
        )

        def minus_days(date_obj, days):
            return fields.Date.to_string(date_obj - relativedelta(days=days))

        date_to = fields.Date.from_string(options["date"]["date_to"])
        periods = [
            (False, fields.Date.to_string(date_to)),
            (minus_days(date_to, 1), minus_days(date_to, 30)),
            (minus_days(date_to, 31), minus_days(date_to, 60)),
            (minus_days(date_to, 61), minus_days(date_to, 90)),
            (minus_days(date_to, 91), minus_days(date_to, 120)),
            (minus_days(date_to, 121), False),
        ]

        def build_result_dict(report, query_res_lines):
            rslt = {f"period{i}": 0 for i in range(len(periods))}

            for query_res in query_res_lines:
                for i in range(len(periods)):
                    period_key = f"period{i}"
                    rslt[period_key] += query_res[period_key]

            if current_groupby == "id":
                query_res = query_res_lines[0]  # We're grouping by id, so there is only
                # 1 element in query_res_lines anyway
                currency = (
                    self.env["res.currency"].browse(query_res["currency_id"][0])
                    if len(query_res["currency_id"]) == 1
                    else None
                )
                rslt.update(
                    {
                        "due_date": query_res["due_date"][0]
                        if len(query_res["due_date"]) == 1
                        else None,
                        "amount_currency": report.format_value(
                            query_res["amount_currency"], currency=currency
                        ),
                        "currency": currency.display_name if currency else None,
                        "account_name": query_res["account_name"][0]
                        if len(query_res["account_name"]) == 1
                        else None,
                        "expected_date": query_res["expected_date"][0]
                        if len(query_res["expected_date"]) == 1
                        else None,
                        "total": None,
                        "has_sublines": query_res["aml_count"] > 0,
                        # Needed by the custom_unfold_all_batch_data_generator,
                        # to speed-up unfold_all
                        "partner_id": query_res["partner_id"][0]
                        if query_res["partner_id"]
                        else None,
                    }
                )
            else:
                rslt.update(
                    {
                        "due_date": None,
                        "amount_currency": None,
                        "currency": None,
                        "account_name": None,
                        "expected_date": None,
                        "total": sum(rslt[f"period{i}"] for i in range(len(periods))),
                        "has_sublines": False,
                    }
                )

            return rslt

        # Build period table
        period_table_format = "(VALUES %s)" % ",".join(
            "(%s, %s, %s)" for period in periods
        )
        params = list(
            chain.from_iterable(
                (period[0] or None, period[1] or None, i)
                for i, period in enumerate(periods)
            )
        )
        period_table = self.env.cr.mogrify(period_table_format, params).decode(
            self.env.cr.connection.encoding
        )

        # Build query
        tables, where_clause, where_params = report._query_get(
            options,
            "strict_range",
            domain=[("account_id.account_type", "=", internal_type)],
        )

        always_present_groupby = "period_table.period_index"
        if current_groupby:
            select_from_groupby = (
                f"account_move_line.{current_groupby} AS grouping_key,"
            )
            groupby_clause = (
                f"account_move_line.{current_groupby}, {always_present_groupby}"
            )
        else:
            select_from_groupby = ""
            groupby_clause = always_present_groupby
        select_period_query = ",".join(
            f"""
                CASE
                 WHEN period_table.period_index = {i}
                 THEN %s * (
                     SUM(account_move_line.balance_ref) - COALESCE(
                         SUM(part_debit.amount_ref), 0) + COALESCE(
                             SUM(part_credit.amount_ref), 0))
                 ELSE 0
                END AS period{i}
            """
            for i in range(len(periods))
        )

        tail_query, tail_params = report._get_engine_query_tail(offset, limit)
        query = f"""
            WITH period_table(date_start, date_stop, period_index) AS ({period_table})

            SELECT
                {select_from_groupby}
                %s * SUM(account_move_line.amount_residual_currency) AS amount_currency,
                ARRAY_AGG(
                    DISTINCT account_move_line.partner_id) AS partner_id,
                ARRAY_AGG(account_move_line.payment_id) AS payment_id,
                ARRAY_AGG(
                    DISTINCT COALESCE(
                        account_move_line.date_maturity, account_move_line.date)
                    ) AS report_date,
                ARRAY_AGG(
                    DISTINCT account_move_line.expected_pay_date
                    ) AS expected_date,
                ARRAY_AGG(
                    DISTINCT account.code) AS account_name,
                ARRAY_AGG(
                    DISTINCT COALESCE(
                        account_move_line.date_maturity, account_move_line.date)
                    ) AS due_date,
                ARRAY_AGG(
                    DISTINCT account_move_line.currency_id) AS currency_id,
                COUNT(account_move_line.id) AS aml_count,
                ARRAY_AGG(account.code) AS account_code,
                {select_period_query}

            FROM {tables}

            JOIN account_journal journal
            ON journal.id = account_move_line.journal_id
            JOIN account_account account
            ON account.id = account_move_line.account_id

            LEFT JOIN LATERAL (
                SELECT SUM(part.amount_ref) AS amount_ref, part.debit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %s
                GROUP BY part.debit_move_id
            ) part_debit ON part_debit.debit_move_id = account_move_line.id

            LEFT JOIN LATERAL (
                SELECT SUM(part.amount_ref) AS amount_ref, part.credit_move_id
                FROM account_partial_reconcile part
                WHERE part.max_date <= %s
                GROUP BY part.credit_move_id
            ) part_credit ON part_credit.credit_move_id = account_move_line.id

            JOIN period_table ON
                (
                    period_table.date_start IS NULL
                    OR COALESCE(
                        account_move_line.date_maturity, account_move_line.date
                    ) <= DATE(period_table.date_start)
                )
                AND
                (
                    period_table.date_stop IS NULL
                    OR COALESCE(
                        account_move_line.date_maturity, account_move_line.date
                    ) >= DATE(period_table.date_stop)
                )

            WHERE {where_clause}

            GROUP BY {groupby_clause}

            HAVING
                (SUM(account_move_line.debit_ref) - COALESCE(
                    SUM(part_debit.amount_ref), 0)) != 0
                OR
                (SUM(account_move_line.credit_ref) - COALESCE(
                    SUM(part_credit.amount_ref), 0)) != 0
            {tail_query}
        """

        multiplicator = -1 if internal_type == "liability_payable" else 1
        params = [
            multiplicator,
            *([multiplicator] * len(periods)),
            date_to,
            date_to,
            *where_params,
            *tail_params,
        ]
        self._cr.execute(query, params)
        query_res_lines = self._cr.dictfetchall()

        if not current_groupby:
            return build_result_dict(report, query_res_lines)
        else:
            rslt = []

            all_res_per_grouping_key = {}
            for query_res in query_res_lines:
                grouping_key = query_res["grouping_key"]
                all_res_per_grouping_key.setdefault(grouping_key, []).append(query_res)

            for grouping_key, query_res_lines in all_res_per_grouping_key.items():
                rslt.append((grouping_key, build_result_dict(report, query_res_lines)))

            return rslt
