# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict

from odoo import api, models


class GenericTaxReportCustomHandler(models.AbstractModel):
    _inherit = "account.generic.tax.report.handler"

    def _read_generic_tax_report_amounts(
        self, report, options_by_column_group, groupby_fields
    ):
        """Read the tax details to compute the tax amounts.

        :param options_list:    The list of report options, one for each period.
        :param groupby_fields:  A list of tuple (alias, field) representing the
                                way the amounts must be grouped.
        :return:                A dictionary mapping each groupby key (e.g. a tax_id)
                                to a sub dictionary containing:

            base_amount:    The tax base amount expressed in company's currency.
            tax_amount      The tax amount expressed in company's currency.
            children:       The children nodes following the same pattern as
                            the current dictionary.
        """
        fetch_group_of_taxes = False

        select_clause_list = []
        groupby_query_list = []
        for alias, field in groupby_fields:
            select_clause_list.append(f"{alias}.{field} AS {alias}_{field}")
            groupby_query_list.append(f"{alias}.{field}")

            # Fetch both info from the originator tax and the
            # child tax to manage the group of taxes.
            if alias == "src_tax":
                select_clause_list.append(f"tax.{field} AS tax_{field}")
                groupby_query_list.append(f"tax.{field}")
                fetch_group_of_taxes = True

        select_clause_str = ",".join(select_clause_list)
        groupby_query_str = ",".join(groupby_query_list)

        # Fetch the group of taxes.
        # If all children taxes are 'none', all amounts are
        # aggregated and only the group will appear on the report.
        # If some children taxes are not 'none', the children are displayed.
        group_of_taxes_to_expand = set()
        if fetch_group_of_taxes:
            group_of_taxes = (
                self.env["account.tax"]
                .with_context(active_test=False)
                .search([("amount_type", "=", "group")])
            )
            for group in group_of_taxes:
                if set(group.children_tax_ids.mapped("type_tax_use")) != {"none"}:
                    group_of_taxes_to_expand.add(group.id)

        res = {}
        for column_group_key, options in options_by_column_group.items():
            tables, where_clause, where_params = report._query_get(
                options, "strict_range"
            )
            if (
                options.get("selected_currency", False)
                and options.get("selected_currency") == self.env.company.currency_id.id
            ):
                tax_details_query, tax_details_params = self.env[
                    "account.move.line"
                ]._get_query_tax_details(tables, where_clause, where_params)
            else:
                tax_details_query, tax_details_params = (
                    self.env["account.move.line"]
                    .with_context(ref_report=True)
                    ._get_query_tax_details(tables, where_clause, where_params)
                )

            # Avoid adding multiple times the same base
            # amount sharing the same grouping_key.
            # It could happen when dealing with group
            # of taxes for example.
            row_keys = set()

            self._cr.execute(
                f"""
                SELECT
                    {select_clause_str},
                    trl.refund_tax_id IS NOT NULL AS is_refund,
                    SUM(tdr.base_amount) AS base_amount,
                    SUM(tdr.tax_amount) AS tax_amount
                FROM ({tax_details_query}) AS tdr
                JOIN account_tax_repartition_line trl ON trl.id = tdr.tax_repartition_line_id
                JOIN account_tax tax ON tax.id = tdr.tax_id
                JOIN account_tax src_tax ON
                    src_tax.id = COALESCE(tdr.group_tax_id, tdr.tax_id)
                    AND src_tax.type_tax_use IN ('sale', 'purchase')
                JOIN account_account account ON account.id = tdr.base_account_id
                WHERE tdr.tax_exigible
                GROUP BY tdr.tax_repartition_line_id, trl.refund_tax_id, {groupby_query_str}
                ORDER BY src_tax.sequence, src_tax.id, tax.sequence, tax.id
            """,
                tax_details_params,
            )

            for row in self._cr.dictfetchall():
                node = res

                # tuple of values used to prevent adding multiple times the same base amount.
                cumulated_row_key = [row["is_refund"]]

                for alias, field in groupby_fields:
                    grouping_key = f"{alias}_{field}"

                    # Manage group of taxes.
                    # In case the group of taxes is mixing multiple
                    # taxes having a type_tax_use != 'none', consider
                    # them instead of the group.
                    if (
                        grouping_key == "src_tax_id"
                        and row["src_tax_id"] in group_of_taxes_to_expand
                    ):
                        # Add the originator group to the grouping key, to
                        # make sure that its base amount is not treated twice,
                        # for hybrid cases where a tax is both used in a
                        # group and independently.
                        cumulated_row_key.append(row[grouping_key])

                        # Ensure the child tax is used instead of the group.
                        grouping_key = "tax_id"

                    row_key = row[grouping_key]
                    cumulated_row_key.append(row_key)
                    cumulated_row_key_tuple = tuple(cumulated_row_key)

                    node.setdefault(
                        row_key,
                        {
                            "base_amount": {
                                column_group_key: 0.0
                                for column_group_key in options["column_groups"]
                            },
                            "tax_amount": {
                                column_group_key: 0.0
                                for column_group_key in options["column_groups"]
                            },
                            "children": {},
                        },
                    )
                    sub_node = node[row_key]

                    # Add amounts.
                    if cumulated_row_key_tuple not in row_keys:
                        sub_node["base_amount"][column_group_key] += row["base_amount"]
                    sub_node["tax_amount"][column_group_key] += row["tax_amount"]

                    node = sub_node["children"]
                    row_keys.add(cumulated_row_key_tuple)

        return res

    @api.model
    def _read_generic_tax_report_amounts_no_tax_details(
        self, report, options, options_by_column_group
    ):
        # Fetch the group of taxes.
        # If all child taxes have a 'none' type_tax_use,
        # all amounts are aggregated and only the group
        # appears on the report.
        self._cr.execute(
            """
                SELECT
                    group_tax.id,
                    group_tax.type_tax_use,
                    ARRAY_AGG(child_tax.id) AS child_tax_ids,
                    ARRAY_AGG(DISTINCT child_tax.type_tax_use) AS child_types
                FROM account_tax_filiation_rel group_tax_rel
                JOIN account_tax group_tax ON group_tax.id = group_tax_rel.parent_tax
                JOIN account_tax child_tax ON child_tax.id = group_tax_rel.child_tax
                WHERE group_tax.amount_type = 'group' AND group_tax.company_id IN %s
                GROUP BY group_tax.id
            """,
            [
                tuple(
                    comp["id"]
                    for comp in options.get("multi_company", self.env.company)
                )
            ],
        )
        group_of_taxes_info = {}
        child_to_group_of_taxes = {}
        for row in self._cr.dictfetchall():
            row["to_expand"] = row["child_types"] != ["none"]
            group_of_taxes_info[row["id"]] = row
            for child_id in row["child_tax_ids"]:
                child_to_group_of_taxes[child_id] = row["id"]

        results = defaultdict(
            lambda: {  # key: type_tax_use
                "base_amount": {
                    column_group_key: 0.0
                    for column_group_key in options["column_groups"]
                },
                "tax_amount": {
                    column_group_key: 0.0
                    for column_group_key in options["column_groups"]
                },
                "children": defaultdict(
                    lambda: {  # key: tax_id
                        "base_amount": {
                            column_group_key: 0.0
                            for column_group_key in options["column_groups"]
                        },
                        "tax_amount": {
                            column_group_key: 0.0
                            for column_group_key in options["column_groups"]
                        },
                    }
                ),
            }
        )

        for column_group_key, options in options_by_column_group.items():
            tables, where_clause, where_params = report._query_get(
                options, "strict_range"
            )

            balance_query = False
            if (
                options.get("selected_currency", False)
                and options.get("selected_currency") == self.env.company.currency_id.id
            ):
                balance_query = "SUM(account_move_line.balance) AS base_amount"
            else:
                balance_query = "SUM(account_move_line.balance_ref) AS base_amount"
            # Fetch the base amounts.
            self._cr.execute(
                f"""
                SELECT
                    tax.id AS tax_id,
                    tax.type_tax_use AS tax_type_tax_use,
                    src_group_tax.id AS src_group_tax_id,
                    src_group_tax.type_tax_use AS src_group_tax_type_tax_use,
                    src_tax.id AS src_tax_id,
                    src_tax.type_tax_use AS src_tax_type_tax_use,
                    {balance_query}
                FROM {tables}
                JOIN account_move_line_account_tax_rel tax_rel ON account_move_line.id = tax_rel.account_move_line_id
                JOIN account_tax tax ON tax.id = tax_rel.account_tax_id
                LEFT JOIN account_tax src_tax ON src_tax.id = account_move_line.tax_line_id
                LEFT JOIN account_tax src_group_tax ON src_group_tax.id = account_move_line.group_tax_id
                WHERE {where_clause}
                    AND (
                        /* CABA */
                        account_move_line__move_id.always_tax_exigible
                        OR account_move_line__move_id.tax_cash_basis_rec_id IS NOT NULL
                        OR tax.tax_exigibility != 'on_payment'
                    )
                    AND (
                        (
                            /* Tax lines affecting the base of others. */
                            account_move_line.tax_line_id IS NOT NULL
                            AND (
                                src_tax.type_tax_use IN ('sale', 'purchase')
                                OR src_group_tax.type_tax_use IN ('sale', 'purchase')
                            )
                        )
                        OR
                        (
                            /* For regular base lines. */
                            account_move_line.tax_line_id IS NULL
                            AND tax.type_tax_use IN ('sale', 'purchase')
                        )
                    )
                GROUP BY tax.id, src_group_tax.id, src_tax.id
                ORDER BY src_group_tax.sequence, src_group_tax.id, src_tax.sequence, src_tax.id, tax.sequence, tax.id
            """,
                where_params,
            )

            group_of_taxes_with_extra_base_amount = set()
            for row in self._cr.dictfetchall():
                is_tax_line = bool(row["src_tax_id"])
                if is_tax_line:
                    if (
                        row["src_group_tax_id"]
                        and not group_of_taxes_info[row["src_group_tax_id"]][
                            "to_expand"
                        ]
                        and row["tax_id"]
                        in group_of_taxes_info[row["src_group_tax_id"]]["child_tax_ids"]
                    ):
                        # Suppose a base of 1000 with a group of taxes 20% affect + 10%.
                        # The base of the group of taxes must be 1000, not 1200 because
                        # the group of taxes is not expanded. So the tax lines affecting
                        # the base of its own group of taxes are ignored.
                        pass
                    elif row[
                        "tax_type_tax_use"
                    ] == "none" and child_to_group_of_taxes.get(row["tax_id"]):
                        # The tax line is affecting the base of a 'none' tax belonging
                        # to a group of taxes.
                        # In that case, the amount is accounted as an extra base for
                        # that group. However, we need to account it only once.
                        # For example, suppose a tax 10% affect base of subsequent
                        # followed by a group of taxes 20% + 30%. On a base of 1000.0,
                        # the tax line for 10% will affect the base of 20% + 30%.
                        # However, this extra base must be accounted only once since
                        # the base of the group of taxes must be 1100.0 and not
                        # 1200.0.
                        group_tax_id = child_to_group_of_taxes[row["tax_id"]]
                        if group_tax_id not in group_of_taxes_with_extra_base_amount:
                            group_tax_info = group_of_taxes_info[group_tax_id]
                            results[group_tax_info["type_tax_use"]]["children"][
                                group_tax_id
                            ]["base_amount"][column_group_key] += row["base_amount"]
                            group_of_taxes_with_extra_base_amount.add(group_tax_id)
                    else:
                        tax_type_tax_use = (
                            row["src_group_tax_type_tax_use"]
                            or row["src_tax_type_tax_use"]
                        )
                        results[tax_type_tax_use]["children"][row["tax_id"]][
                            "base_amount"
                        ][column_group_key] += row["base_amount"]
                else:
                    if (
                        row["tax_id"] in group_of_taxes_info
                        and group_of_taxes_info[row["tax_id"]]["to_expand"]
                    ):
                        # Expand the group of taxes since it contains at least one tax with a type != 'none'.
                        group_info = group_of_taxes_info[row["tax_id"]]
                        for child_tax_id in group_info["child_tax_ids"]:
                            results[group_info["type_tax_use"]]["children"][
                                child_tax_id
                            ]["base_amount"][column_group_key] += row["base_amount"]
                    else:
                        results[row["tax_type_tax_use"]]["children"][row["tax_id"]][
                            "base_amount"
                        ][column_group_key] += row["base_amount"]

            if (
                options.get("selected_currency", False)
                and options.get("selected_currency") == self.env.company.currency_id.id
            ):
                balance_query = "SUM(account_move_line.balance) AS tax_amount"
            else:
                balance_query = "SUM(account_move_line.balance_ref) AS tax_amount"

            # Fetch the tax amounts.
            self._cr.execute(
                f"""
                SELECT
                    tax.id AS tax_id,
                    tax.type_tax_use AS tax_type_tax_use,
                    group_tax.id AS group_tax_id,
                    group_tax.type_tax_use AS group_tax_type_tax_use,
                    {balance_query}
                FROM {tables}
                JOIN account_tax tax ON tax.id = account_move_line.tax_line_id
                LEFT JOIN account_tax group_tax ON group_tax.id = account_move_line.group_tax_id
                WHERE {where_clause}
                    AND (
                        /* CABA */
                        account_move_line__move_id.always_tax_exigible
                        OR account_move_line__move_id.tax_cash_basis_rec_id IS NOT NULL
                        OR tax.tax_exigibility != 'on_payment'
                    )
                    AND (
                        (group_tax.id IS NULL AND tax.type_tax_use IN ('sale', 'purchase'))
                        OR
                        (group_tax.id IS NOT NULL AND group_tax.type_tax_use IN ('sale', 'purchase'))
                    )
                GROUP BY tax.id, group_tax.id
            """,
                where_params,
            )

            for row in self._cr.dictfetchall():
                # Manage group of taxes.
                # In case the group of taxes is mixing multiple
                # taxes having a type_tax_use != 'none', consider
                # them instead of the group.
                tax_id = row["tax_id"]
                if row["group_tax_id"]:
                    tax_type_tax_use = row["group_tax_type_tax_use"]
                    if not group_of_taxes_info[row["group_tax_id"]]["to_expand"]:
                        tax_id = row["group_tax_id"]
                else:
                    tax_type_tax_use = (
                        row["group_tax_type_tax_use"] or row["tax_type_tax_use"]
                    )

                results[tax_type_tax_use]["tax_amount"][column_group_key] += row[
                    "tax_amount"
                ]
                results[tax_type_tax_use]["children"][tax_id]["tax_amount"][
                    column_group_key
                ] += row["tax_amount"]

        return results
