from datetime import date, timedelta
from functools import lru_cache

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    currency_ref_id = fields.Many2one(related="company_id.currency_ref_id")
    currency_rate_ref = fields.Many2one(
        "res.currency.rate",
        string="Tasa de cambio",
        compute="_compute_currency_rate_ref",
        store=True,
        precompute=True,
        required=True,
        readonly=False,
        ondelete="restrict",
        domain="[('currency_id', '=', currency_ref_id)]",
    )
    debit_ref = fields.Monetary(
        string="Débito ope.",
        compute="_compute_debit_credit_ref",
        store=True,
        currency_field="currency_ref_id",
    )
    credit_ref = fields.Monetary(
        string="Crédito ope.",
        compute="_compute_debit_credit_ref",
        store=True,
        currency_field="currency_ref_id",
    )
    balance_ref = fields.Monetary(
        string="Balance ope.",
        compute="_compute_balance_ref",
        store=True,
        currency_field="currency_ref_id",
    )
    amount_residual_ref = fields.Monetary(
        string="Importe adeudado ope.",
        compute="_compute_amount_residual",
        store=True,
        currency_field="currency_ref_id",
    )
    tax_base_amount_ref = fields.Monetary(
        string="Base ope.",
        compute="_compute_tax_base_amount_ref",
        store=True,
        currency_field="currency_ref_id",
    )

    _sql_constraints = [
        (
            "check_credit_debit_ref",
            "CHECK(display_type IN ('line_section', 'line_note') OR debit_ref * credit_ref = 0)",
            "Wrong credit or debit value in accounting entry !",
        )
    ]

    @api.depends("move_id.currency_rate_ref")
    def _compute_currency_rate_ref(self):
        for line in self:
            line.currency_rate_ref = (
                line.move_id.currency_rate_ref
                or line.currency_rate_ref
                or line.currency_ref_id.get_currency_rate()
            )

    @api.depends("currency_id", "company_id", "move_id.date", "currency_rate_ref")
    def _compute_currency_rate(self):
        @lru_cache
        def get_rate(from_currency, to_currency, company, date):
            return self.env["res.currency"]._get_conversion_rate(
                from_currency, to_currency, company, date
            )

        for line in self:
            line.currency_rate = (
                line.currency_rate_ref.rate
                if line.currency_id == line.currency_ref_id
                else get_rate(
                    from_currency=line.company_currency_id,
                    to_currency=line.currency_id,
                    company=line.company_id,
                    date=line.move_id.invoice_date
                    or line.move_id.date
                    or fields.Date.context_today(line),
                )
            )

    @api.depends("balance", "amount_currency", "currency_rate_ref")
    def _compute_balance_ref(self):
        if self._context.get("skip_compute_balance_ref"):
            return

        payment_term_lines = self.filtered(
            lambda l: l.display_type == "payment_term"
            and not l.move_id.invoice_payment_term_id
        )

        for line in self - payment_term_lines:
            if line.display_type in ("line_section", "line_note"):
                line.balance_ref = False
            elif line.currency_id == line.currency_ref_id:
                line.balance_ref = line.amount_currency
            else:
                line.balance_ref = line.currency_ref_id.round(
                    line.balance * line.currency_rate_ref.rate
                )

        for line in payment_term_lines:
            line.balance_ref = -sum(
                line.move_id.line_ids.filtered(
                    lambda l: l.display_type in ("product", "tax", "rounding")
                ).mapped("balance_ref")
            )

    @api.depends("balance_ref", "move_id.is_storno")
    def _compute_debit_credit_ref(self):
        for line in self:
            if not line.is_storno:
                line.debit_ref = line.balance_ref if line.balance_ref > 0.0 else 0.0
                line.credit_ref = -line.balance_ref if line.balance_ref < 0.0 else 0.0
            else:
                line.debit_ref = line.balance_ref if line.balance_ref < 0.0 else 0.0
                line.credit_ref = -line.balance_ref if line.balance_ref > 0.0 else 0.0

    @api.depends("tax_base_amount", "currency_rate_ref")
    def _compute_tax_base_amount_ref(self):
        for line in self:
            if line.display_type == "tax":
                line.tax_base_amount_ref = line.currency_ref_id.round(
                    line.tax_base_amount * line.currency_rate_ref.rate
                )
            else:
                line.tax_base_amount_ref = 0.0

    @api.depends(
        "debit",
        "credit",
        "amount_currency",
        "account_id",
        "currency_id",
        "company_id",
        "matched_debit_ids",
        "matched_credit_ids",
    )
    def _compute_amount_residual(self):
        """Computes the residual amount of a move line from a reconcilable
        account in the company currency and the line's currency.
        This amount will be 0 for fully reconciled lines or lines from a
        non-reconcilable account, the original line amount
        for unreconciled lines, and something in-between for partially
        reconciled lines.
        """
        need_residual_lines = self.filtered(
            lambda x: x.account_id.reconcile
            or x.account_id.account_type in ("asset_cash", "liability_credit_card")
        )
        stored_lines = need_residual_lines.filtered("id")

        if stored_lines:
            self.env["account.partial.reconcile"].flush_model()
            self.env["res.currency"].flush_model(["decimal_places"])

            aml_ids = tuple(stored_lines.ids)
            self._cr.execute(
                """
                SELECT
                    part.debit_move_id AS line_id,
                    'debit' AS flag,
                    COALESCE(SUM(part.amount), 0.0) AS amount,
                    COALESCE(SUM(part.amount_ref), 0.0) AS amount_ref,
                    ROUND(SUM(part.debit_amount_currency), curr.decimal_places) AS amount_currency
                FROM account_partial_reconcile part
                JOIN res_currency curr ON curr.id = part.debit_currency_id
                WHERE part.debit_move_id IN %s
                GROUP BY part.debit_move_id, curr.decimal_places
                UNION ALL
                SELECT
                    part.credit_move_id AS line_id,
                    'credit' AS flag,
                    COALESCE(SUM(part.amount), 0.0) AS amount,
                    COALESCE(SUM(part.amount_ref), 0.0) AS amount_ref,
                    ROUND(SUM(part.credit_amount_currency), curr.decimal_places) AS amount_currency
                FROM account_partial_reconcile part
                JOIN res_currency curr ON curr.id = part.credit_currency_id
                WHERE part.credit_move_id IN %s
                GROUP BY part.credit_move_id, curr.decimal_places
            """,
                [aml_ids, aml_ids],
            )
            amounts_map = {
                (line_id, flag): (amount, amount_ref, amount_currency)
                for (
                    line_id,
                    flag,
                    amount,
                    amount_ref,
                    amount_currency,
                ) in self.env.cr.fetchall()
            }
        else:
            amounts_map = {}

        # Lines that can't be reconciled with anything
        # since the account doesn't allow that.
        for line in self - need_residual_lines:
            line.amount_residual = 0.0
            line.amount_residual_currency = 0.0
            line.reconciled = False

        for line in need_residual_lines:
            # Since this part could be call on 'new' records,
            # 'company_currency_id'/'currency_id' could be not set.
            comp_curr = line.company_currency_id or self.env.company.currency_id
            ref_curr = self.env.company.currency_ref_id
            foreign_curr = line.currency_id or comp_curr

            # Retrieve the amounts in both foreign/company currencies.
            # If the record is 'new', the amounts_map is empty.
            debit_amount, debit_amount_ref, debit_amount_currency = amounts_map.get(
                (line.id, "debit"), (0.0, 0.0, 0.0)
            )
            credit_amount, credit_amount_ref, credit_amount_currency = amounts_map.get(
                (line.id, "credit"), (0.0, 0.0, 0.0)
            )

            # Subtract the values from the account.partial.reconcile
            # to compute the residual amounts.
            line.amount_residual = comp_curr.round(
                line.balance - debit_amount + credit_amount
            )
            line.amount_residual_currency = foreign_curr.round(
                line.amount_currency - debit_amount_currency + credit_amount_currency
            )
            line.amount_residual_ref = ref_curr.round(
                line.balance_ref - debit_amount_ref + credit_amount_ref
            )
            line.reconciled = (
                comp_curr.is_zero(line.amount_residual)
                and foreign_curr.is_zero(line.amount_residual_currency)
                and ref_curr.is_zero(line.amount_residual_ref)
            )

    @api.onchange("amount_currency", "currency_id", "currency_rate_ref")
    def _inverse_amount_currency(self):
        super(__class__, self)._inverse_amount_currency()

    @api.model
    def _prepare_reconciliation_single_partial(self, debit_vals, credit_vals):
        """Prepare the values to create an account.partial.reconcile later
        when reconciling the dictionaries passed
        as parameters, each one representing an account.move.line.
        :param debit_vals:  The values of account.move.line to consider
                            for a debit line.
        :param credit_vals: The values of account.move.line to consider
                            for a credit line.
        :return:            A dictionary:
                * debit_vals:   None if the line has nothing left to reconcile.
                * credit_vals:  None if the line has nothing left to reconcile.
                * partial_vals: The newly computed values for the partial.
        """

        def get_odoo_rate(vals):
            if (
                vals.get("record")
                and vals["record"].currency_ref_id.id == recon_currency.id
            ):
                return vals["record"].currency_rate_ref.rate
            else:
                if vals.get("record") and vals["record"].move_id.is_invoice(
                    include_receipts=True
                ):
                    exchange_rate_date = vals["record"].move_id.invoice_date
                else:
                    exchange_rate_date = vals["date"]
                return recon_currency._get_conversion_rate(
                    company_currency,
                    recon_currency,
                    vals["company"],
                    exchange_rate_date,
                )

        def get_accounting_rate(vals):
            if company_currency.is_zero(vals["balance"]) or vals["currency"].is_zero(
                vals["amount_currency"]
            ):
                return None
            elif (
                vals.get("record")
                and vals["record"].currency_ref_id.id == vals["currency"].id
            ):
                return vals["record"].currency_rate_ref.rate
            else:
                return abs(vals["amount_currency"]) / abs(vals["balance"])

        # ==== Determine the currency in which the reconciliation will be done ====
        # In this part, we retrieve the residual amounts, check
        # if they are zero or not and determine in which currency
        # and at which rate the reconciliation will be done.

        res = {
            "debit_vals": debit_vals,
            "credit_vals": credit_vals,
        }
        remaining_debit_amount_curr = debit_vals["amount_residual_currency"]
        remaining_credit_amount_curr = credit_vals["amount_residual_currency"]
        remaining_debit_amount = debit_vals["amount_residual"]
        remaining_credit_amount = credit_vals["amount_residual"]
        remaining_debit_amount_curr_ref = debit_vals["amount_residual_ref"]
        remaining_credit_amount_curr_ref = credit_vals["amount_residual_ref"]

        company_currency = debit_vals["company"].currency_id
        currency_ref_id = debit_vals["company"].currency_ref_id
        has_debit_zero_residual = company_currency.is_zero(remaining_debit_amount)
        has_credit_zero_residual = company_currency.is_zero(remaining_credit_amount)
        has_debit_zero_residual_currency = debit_vals["currency"].is_zero(
            remaining_debit_amount_curr
        )
        has_credit_zero_residual_currency = credit_vals["currency"].is_zero(
            remaining_credit_amount_curr
        )
        has_debit_zero_residual_currency_ref = currency_ref_id.is_zero(
            remaining_debit_amount_curr_ref
        )
        has_credit_zero_residual_currency_ref = currency_ref_id.is_zero(
            remaining_credit_amount_curr_ref
        )
        is_rec_pay_account = debit_vals.get("record") and debit_vals[
            "record"
        ].account_type in ("asset_receivable", "liability_payable")

        if (
            debit_vals["currency"] == credit_vals["currency"] == company_currency
            and not has_debit_zero_residual
            and not has_credit_zero_residual
        ):
            # Everything is expressed in company's currency
            # and there is something left to reconcile.
            recon_currency = company_currency
            debit_rate = credit_rate = 1.0
            recon_debit_amount = remaining_debit_amount
            recon_credit_amount = -remaining_credit_amount
        elif (
            debit_vals["currency"] == company_currency
            and is_rec_pay_account
            and not has_debit_zero_residual
            and credit_vals["currency"] != company_currency
            and not has_credit_zero_residual_currency
        ):
            # The credit line is using a foreign currency
            # but not the opposite line.
            # In that case, convert the amount in company
            # currency to the foreign currency one.
            recon_currency = credit_vals["currency"]
            debit_rate = get_odoo_rate(debit_vals)
            credit_rate = get_accounting_rate(credit_vals)
            recon_debit_amount = recon_currency.round(
                remaining_debit_amount * debit_rate
            )
            recon_credit_amount = -remaining_credit_amount_curr
        elif (
            debit_vals["currency"] != company_currency
            and is_rec_pay_account
            and not has_debit_zero_residual_currency
            and credit_vals["currency"] == company_currency
            and not has_credit_zero_residual
        ):
            # The debit line is using a foreign currency
            # but not the opposite line.
            # In that case, convert the amount in company
            # currency to the foreign currency one.
            recon_currency = debit_vals["currency"]
            debit_rate = get_accounting_rate(debit_vals)
            credit_rate = get_odoo_rate(credit_vals)
            recon_debit_amount = remaining_debit_amount_curr
            recon_credit_amount = recon_currency.round(
                -remaining_credit_amount * credit_rate
            )
        elif (
            debit_vals["currency"] == credit_vals["currency"]
            and debit_vals["currency"] != company_currency
            and not has_debit_zero_residual_currency
            and not has_credit_zero_residual_currency
        ):
            # Both lines are sharing the same foreign currency.
            recon_currency = debit_vals["currency"]
            debit_rate = get_accounting_rate(debit_vals)
            credit_rate = get_accounting_rate(credit_vals)
            recon_debit_amount = remaining_debit_amount_curr
            recon_credit_amount = -remaining_credit_amount_curr
        elif (
            (
                (has_debit_zero_residual and has_debit_zero_residual_currency)
                or (has_credit_zero_residual and has_credit_zero_residual_currency)
            )
            and not has_debit_zero_residual_currency_ref
            and not has_credit_zero_residual_currency_ref
        ):
            # Case when reconcile an exchange difference line
            recon_currency = currency_ref_id
            debit_rate = credit_rate = None
            recon_debit_amount = recon_credit_amount = 0.0
        elif (
            debit_vals["currency"] == credit_vals["currency"]
            and debit_vals["currency"] != company_currency
            and (has_debit_zero_residual_currency or has_credit_zero_residual_currency)
        ):
            # Special case for exchange difference lines. In that case,
            # both lines are sharing the same foreign currency but at
            # least one has no amount in foreign currency.
            # In that case, we don't want a rate for the opposite line
            # because the exchange difference is supposed to reduce only
            # the amount in company currency but not the foreign one.
            recon_currency = company_currency
            debit_rate = None
            credit_rate = None
            recon_debit_amount = remaining_debit_amount
            recon_credit_amount = -remaining_credit_amount
        else:
            # Multiple involved foreign currencies. The
            # reconciliation is done using the currency of the company.
            recon_currency = company_currency
            debit_rate = get_accounting_rate(debit_vals)
            credit_rate = get_accounting_rate(credit_vals)
            recon_debit_amount = remaining_debit_amount
            recon_credit_amount = -remaining_credit_amount

        # Check if there is something left to reconcile.
        # Move to the next loop iteration if not.
        skip_reconciliation = False
        if (
            recon_currency.is_zero(recon_debit_amount)
            and has_debit_zero_residual_currency_ref
        ):
            res["debit_vals"] = None
            skip_reconciliation = True
        if (
            recon_currency.is_zero(recon_credit_amount)
            and has_credit_zero_residual_currency_ref
        ):
            res["credit_vals"] = None
            skip_reconciliation = True
        if skip_reconciliation:
            return res

        # ==== Match both lines together and compute amounts to reconcile ====

        # Determine which line is fully matched by the other.
        compare_amounts = recon_currency.compare_amounts(
            recon_debit_amount, recon_credit_amount
        )
        min_recon_amount = min(recon_debit_amount, recon_credit_amount)
        debit_fully_matched = compare_amounts <= 0
        credit_fully_matched = compare_amounts >= 0

        # ==== Computation of partial amounts ====
        if recon_currency == company_currency:
            # Compute the partial amount expressed in company currency.
            partial_amount = min_recon_amount

            # Compute the partial amount expressed in foreign currency.
            if debit_rate:
                partial_debit_amount_currency = debit_vals["currency"].round(
                    debit_rate * min_recon_amount
                )
                partial_debit_amount_currency = min(
                    partial_debit_amount_currency, remaining_debit_amount_curr
                )
            else:
                partial_debit_amount_currency = 0.0
            if credit_rate:
                partial_credit_amount_currency = credit_vals["currency"].round(
                    credit_rate * min_recon_amount
                )
                partial_credit_amount_currency = min(
                    partial_credit_amount_currency, -remaining_credit_amount_curr
                )
            else:
                partial_credit_amount_currency = 0.0

        else:
            # recon_currency != company_currency
            # Compute the partial amount expressed in company currency.
            if debit_rate:
                partial_debit_amount = company_currency.round(
                    min_recon_amount / debit_rate
                )
                partial_debit_amount = min(partial_debit_amount, remaining_debit_amount)
            else:
                partial_debit_amount = 0.0
            if credit_rate:
                partial_credit_amount = company_currency.round(
                    min_recon_amount / credit_rate
                )
                partial_credit_amount = min(
                    partial_credit_amount, -remaining_credit_amount
                )
            else:
                partial_credit_amount = 0.0
            partial_amount = min(partial_debit_amount, partial_credit_amount)

            # Compute the partial amount expressed in foreign currency.
            # Take care to handle the case when a line expressed in
            # company currency is mimicking the foreign currency of
            # the opposite line.
            if debit_vals["currency"] == company_currency:
                partial_debit_amount_currency = partial_amount
            else:
                partial_debit_amount_currency = min_recon_amount
            if credit_vals["currency"] == company_currency:
                partial_credit_amount_currency = partial_amount
            else:
                partial_credit_amount_currency = min_recon_amount

        # Compute the partial amount expressed in referencial currency.
        debit_rate_ref = (
            debit_vals.get("record")
            and debit_vals["record"].currency_rate_ref.rate
            or None
        )
        credit_rate_ref = (
            credit_vals.get("record")
            and credit_vals["record"].currency_rate_ref.rate
            or None
        )
        if debit_rate_ref and debit_rate:
            min_recon_amount_ref = (
                min_recon_amount
                if recon_currency == company_currency
                else min_recon_amount / debit_rate
            )
            partial_debit_amount_currency_ref = currency_ref_id.round(
                min_recon_amount_ref * debit_rate_ref
            )
            partial_debit_amount_currency_ref = min(
                partial_debit_amount_currency_ref, remaining_debit_amount_curr_ref
            )
        else:
            partial_debit_amount_currency_ref = remaining_debit_amount_curr_ref
        if credit_rate_ref and credit_rate:
            min_recon_amount_ref = (
                min_recon_amount
                if recon_currency == company_currency
                else min_recon_amount / credit_rate
            )
            partial_credit_amount_currency_ref = currency_ref_id.round(
                min_recon_amount_ref * credit_rate_ref
            )
            partial_credit_amount_currency_ref = min(
                partial_credit_amount_currency_ref, -remaining_credit_amount_curr_ref
            )
        else:
            partial_credit_amount_currency_ref = -remaining_credit_amount_curr_ref
        partial_amount_ref = min(
            partial_debit_amount_currency_ref, partial_credit_amount_currency_ref
        )

        # Computation of the partial exchange difference.
        # You can skip this part using the `no_exchange_difference`
        # context key (when reconciling an exchange
        # difference for example).
        if not self._context.get("no_exchange_difference"):
            exchange_lines_to_fix = self.env["account.move.line"]
            amounts_list = []
            if recon_currency == company_currency:
                if debit_fully_matched:
                    debit_exchange_amount = (
                        remaining_debit_amount_curr - partial_debit_amount_currency
                    )
                    if not debit_vals["currency"].is_zero(debit_exchange_amount):
                        if debit_vals.get("record"):
                            exchange_lines_to_fix += debit_vals["record"]
                        amounts_list.append(
                            {"amount_residual_currency": debit_exchange_amount}
                        )
                        remaining_debit_amount_curr -= debit_exchange_amount
                if credit_fully_matched:
                    credit_exchange_amount = (
                        remaining_credit_amount_curr + partial_credit_amount_currency
                    )
                    if not credit_vals["currency"].is_zero(credit_exchange_amount):
                        if credit_vals.get("record"):
                            exchange_lines_to_fix += credit_vals["record"]
                        amounts_list.append(
                            {"amount_residual_currency": credit_exchange_amount}
                        )
                        remaining_credit_amount_curr += credit_exchange_amount

            else:
                if debit_fully_matched:
                    # Create an exchange difference on the remaining
                    # amount expressed in company's currency.
                    debit_exchange_amount = remaining_debit_amount - partial_amount
                    if not company_currency.is_zero(debit_exchange_amount):
                        if debit_vals.get("record"):
                            exchange_lines_to_fix += debit_vals["record"]
                        amounts_list.append({"amount_residual": debit_exchange_amount})
                        remaining_debit_amount -= debit_exchange_amount
                        if debit_vals["currency"] == company_currency:
                            remaining_debit_amount_curr -= debit_exchange_amount
                else:
                    # Create an exchange difference ensuring the rate
                    # between the residual amounts expressed in
                    # both foreign and company's currency is still
                    # consistent regarding the rate between
                    # 'amount_currency' & 'balance'.
                    debit_exchange_amount = partial_debit_amount - partial_amount
                    if company_currency.compare_amounts(debit_exchange_amount, 0.0) > 0:
                        if debit_vals.get("record"):
                            exchange_lines_to_fix += debit_vals["record"]
                        amounts_list.append({"amount_residual": debit_exchange_amount})
                        remaining_debit_amount -= debit_exchange_amount
                        if debit_vals["currency"] == company_currency:
                            remaining_debit_amount_curr -= debit_exchange_amount

                if credit_fully_matched:
                    # Create an exchange difference on the remaining
                    # amount expressed in company's currency.
                    credit_exchange_amount = remaining_credit_amount + partial_amount
                    if not company_currency.is_zero(credit_exchange_amount):
                        if credit_vals.get("record"):
                            exchange_lines_to_fix += credit_vals["record"]
                        amounts_list.append({"amount_residual": credit_exchange_amount})
                        remaining_credit_amount += credit_exchange_amount
                        if credit_vals["currency"] == company_currency:
                            remaining_credit_amount_curr -= credit_exchange_amount
                else:
                    # Create an exchange difference ensuring the rate
                    # between the residual amounts expressed in
                    # both foreign and company's currency is still
                    # consistent regarding the rate between
                    # 'amount_currency' & 'balance'.
                    credit_exchange_amount = partial_amount - partial_credit_amount
                    if (
                        company_currency.compare_amounts(credit_exchange_amount, 0.0)
                        < 0
                    ):
                        if credit_vals.get("record"):
                            exchange_lines_to_fix += credit_vals["record"]
                        amounts_list.append({"amount_residual": credit_exchange_amount})
                        remaining_credit_amount -= credit_exchange_amount
                        if credit_vals["currency"] == company_currency:
                            remaining_credit_amount_curr -= credit_exchange_amount

            # Create an exchange difference to referencial currency
            if debit_fully_matched:
                debit_exchange_amount_ref = (
                    remaining_debit_amount_curr_ref - partial_amount_ref
                )
                if not currency_ref_id.is_zero(debit_exchange_amount_ref):
                    if debit_vals.get("record"):
                        exchange_lines_to_fix += debit_vals["record"]
                    amounts_list.append(
                        {"amount_residual_currency_ref": debit_exchange_amount_ref}
                    )
            else:
                debit_exchange_amount_ref = (
                    partial_debit_amount_currency_ref - partial_amount_ref
                )
                if currency_ref_id.compare_amounts(debit_exchange_amount_ref, 0.0) > 0:
                    if debit_vals.get("record"):
                        exchange_lines_to_fix += debit_vals["record"]
                    amounts_list.append(
                        {"amount_residual_currency_ref": debit_exchange_amount_ref}
                    )
            if credit_fully_matched:
                credit_exchange_amount_ref = (
                    remaining_credit_amount_curr_ref + partial_amount_ref
                )
                if not currency_ref_id.is_zero(credit_exchange_amount_ref):
                    if credit_vals.get("record"):
                        exchange_lines_to_fix += credit_vals["record"]
                    amounts_list.append(
                        {"amount_residual_currency_ref": credit_exchange_amount_ref}
                    )
            else:
                credit_exchange_amount_ref = (
                    partial_amount_ref - partial_credit_amount_currency_ref
                )
                if currency_ref_id.compare_amounts(credit_exchange_amount_ref, 0.0) < 0:
                    if credit_vals.get("record"):
                        exchange_lines_to_fix += credit_vals["record"]
                    amounts_list.append(
                        {"amount_residual_currency_ref": credit_exchange_amount_ref}
                    )

            if exchange_lines_to_fix:
                res[
                    "exchange_vals"
                ] = exchange_lines_to_fix._prepare_exchange_difference_move_vals(
                    amounts_list,
                    exchange_date=max(debit_vals["date"], credit_vals["date"]),
                )

        # ==== Create partials ====

        remaining_debit_amount -= partial_amount
        remaining_credit_amount += partial_amount
        remaining_debit_amount_curr -= partial_debit_amount_currency
        remaining_credit_amount_curr += partial_credit_amount_currency

        res["partial_vals"] = {
            "amount": partial_amount,
            "amount_ref": partial_amount_ref,
            "debit_amount_currency": partial_debit_amount_currency,
            "credit_amount_currency": partial_credit_amount_currency,
            "debit_move_id": debit_vals.get("record") and debit_vals["record"].id,
            "credit_move_id": credit_vals.get("record") and credit_vals["record"].id,
        }

        debit_vals["amount_residual"] = remaining_debit_amount
        debit_vals["amount_residual_currency"] = remaining_debit_amount_curr
        credit_vals["amount_residual"] = remaining_credit_amount
        credit_vals["amount_residual_currency"] = remaining_credit_amount_curr

        if debit_fully_matched:
            res["debit_vals"] = None
        if credit_fully_matched:
            res["credit_vals"] = None
        return res

    @api.model
    def _prepare_reconciliation_partials(self, vals_list):
        """Prepare the partials on the current journal items to
        perform the reconciliation.
        Note: The order of records in self is important because
        the journal items will be reconciled using this order.
        :return: a tuple of 1) list of vals for partial reconciliation
                 creation, 2) the list of vals for the exchange difference
                 entries to be created
        """
        debit_vals_list = iter(
            [
                x
                for x in vals_list
                if x["balance"] > 0.0
                or x["amount_currency"] > 0.0
                or x["balance_ref"] > 0.0
            ]
        )
        credit_vals_list = iter(
            [
                x
                for x in vals_list
                if x["balance"] < 0.0
                or x["amount_currency"] < 0.0
                or x["balance_ref"] < 0.0
            ]
        )
        debit_vals = None
        credit_vals = None

        partials_vals_list = []
        exchange_data = {}

        while True:
            # ==== Find the next available lines ====
            # For performance reasons, the partials are created
            # all at once meaning the residual amounts can't be
            # trusted from one iteration to another. That's the
            # reason why all residual amounts are kept as variables
            # and reduced "manually" every time we append a
            # dictionary to 'partials_vals_list'.

            # Move to the next available debit line.
            if not debit_vals:
                debit_vals = next(debit_vals_list, None)
                if not debit_vals:
                    break

            # Move to the next available credit line.
            if not credit_vals:
                credit_vals = next(credit_vals_list, None)
                if not credit_vals:
                    break

            # ==== Compute the amounts to reconcile ====

            res = self._prepare_reconciliation_single_partial(debit_vals, credit_vals)
            if res.get("partial_vals"):
                if res.get("exchange_vals"):
                    exchange_data[len(partials_vals_list)] = res["exchange_vals"]
                partials_vals_list.append(res["partial_vals"])
            if res["debit_vals"] is None:
                debit_vals = None
            if res["credit_vals"] is None:
                credit_vals = None

        return partials_vals_list, exchange_data

    def _create_reconciliation_partials(self):
        """create the partial reconciliation between all the records in self
        :return: A recordset of account.partial.reconcile.
        """
        partials_vals_list, exchange_data = self._prepare_reconciliation_partials(
            [
                {
                    "record": line,
                    "balance": line.balance,
                    "balance_ref": line.balance_ref,
                    "amount_currency": line.amount_currency,
                    "amount_residual": line.amount_residual,
                    "amount_residual_currency": line.amount_residual_currency,
                    "amount_residual_ref": line.amount_residual_ref,
                    "company": line.company_id,
                    "currency": line.currency_id,
                    "date": line.date,
                }
                for line in self
            ]
        )
        partials = self.env["account.partial.reconcile"].create(partials_vals_list)

        # ==== Create exchange difference moves ====
        for index, exchange_vals in exchange_data.items():
            partials[index].exchange_move_id = self._create_exchange_difference_move(
                exchange_vals
            )

        return partials

    def _prepare_exchange_difference_move_vals(
        self, amounts_list, company=None, exchange_date=None
    ):
        """Prepare values to create later the exchange difference journal entry.
        The exchange difference journal entry is there to fix the debit/credit
        of lines when the journal items are fully reconciled in foreign currency.
        :param amounts_list:    A list of dict, one for each aml.
        :param company:         The company in case there is no aml in self.
        :param exchange_date:   Optional date object providing the date to
                                consider for the exchange difference.
        :return:                A python dictionary containing:
                * move_vals:    A dictionary to be passed to the
                                account.move.create method.
                * to_reconcile: A list of tuple <move_line, sequence> in
                                order to perform the reconciliation after
                                the move creation.
        """
        company = self.company_id or company
        if not company:
            return

        journal = company.currency_exchange_journal_id
        expense_exchange_account = company.expense_currency_exchange_account_id
        income_exchange_account = company.income_currency_exchange_account_id

        move_vals = {
            "move_type": "entry",
            "date": max(
                exchange_date or date.min,
                company._get_user_fiscal_lock_date() + timedelta(days=1),
            ),
            "journal_id": journal.id,
            "line_ids": [],
            "always_tax_exigible": True,
            "global_rate_ref": False,
        }
        to_reconcile = []

        for line, amounts in zip(self, amounts_list):
            move_vals["date"] = max(move_vals["date"], line.date)

            if "amount_residual" in amounts:
                amount_residual = amounts["amount_residual"]
                amount_residual_currency = 0.0
                amount_residual_currency_ref = 0.0
                if line.currency_id == line.company_id.currency_id:
                    amount_residual_currency = amount_residual
                amount_residual_to_fix = amount_residual
                if line.company_currency_id.is_zero(amount_residual):
                    continue
            elif "amount_residual_currency" in amounts:
                amount_residual = 0.0
                amount_residual_currency = amounts["amount_residual_currency"]
                amount_residual_currency_ref = 0.0
                amount_residual_to_fix = amount_residual_currency
                if line.currency_id.is_zero(amount_residual_currency):
                    continue
            elif "amount_residual_currency_ref" in amounts:
                amount_residual = 0.0
                amount_residual_currency = 0.0
                amount_residual_currency_ref = amounts["amount_residual_currency_ref"]
                amount_residual_to_fix = amount_residual_currency_ref
                if line.currency_ref_id.is_zero(amount_residual_currency_ref):
                    continue
            else:
                continue

            if amount_residual_to_fix > 0.0:
                exchange_line_account = expense_exchange_account
            else:
                exchange_line_account = income_exchange_account

            sequence = len(move_vals["line_ids"])
            move_vals["line_ids"] += [
                Command.create(
                    {
                        "name": _("Currency exchange rate difference"),
                        "debit": -amount_residual if amount_residual < 0.0 else 0.0,
                        "credit": amount_residual if amount_residual > 0.0 else 0.0,
                        "balance_ref": -amount_residual_currency_ref,
                        "amount_currency": -amount_residual_currency,
                        "currency_rate_ref": line.currency_rate_ref.id,
                        "account_id": line.account_id.id,
                        "currency_id": line.currency_id.id,
                        "partner_id": line.partner_id.id,
                        "sequence": sequence,
                    }
                ),
                Command.create(
                    {
                        "name": _("Currency exchange rate difference"),
                        "debit": amount_residual if amount_residual > 0.0 else 0.0,
                        "credit": -amount_residual if amount_residual < 0.0 else 0.0,
                        "balance_ref": amount_residual_currency_ref,
                        "amount_currency": amount_residual_currency,
                        "currency_rate_ref": line.currency_rate_ref.id,
                        "account_id": exchange_line_account.id,
                        "currency_id": line.currency_id.id,
                        "partner_id": line.partner_id.id,
                        "sequence": sequence + 1,
                    }
                ),
            ]
            to_reconcile.append((line, sequence))

        return {"move_vals": move_vals, "to_reconcile": to_reconcile}

    @api.model
    def _create_exchange_difference_move(self, exchange_diff_vals):
        """Create the exchange difference journal
        entry on the current journal items.
        :param exchange_diff_vals:  The current vals of the exchange difference
                                    journal entry created by the
                                    '_prepare_exchange_difference_move_vals' method.
        :return:                    An account.move record.
        """
        move_vals = exchange_diff_vals["move_vals"]
        if not move_vals["line_ids"]:
            return

        # Check the configuration of the exchange difference journal.
        journal = self.env["account.journal"].browse(move_vals["journal_id"])
        if not journal:
            raise UserError(
                _(
                    "You should configure the 'Exchange Gain or Loss Journal' "
                    "in your company settings, to manage automatically the "
                    "booking of accounting entries related to differences "
                    "between exchange rates."
                )
            )
        if not journal.company_id.expense_currency_exchange_account_id:
            raise UserError(
                _(
                    "You should configure the 'Loss Exchange Rate Account' "
                    "in your company settings, to manage automatically the "
                    "booking of accounting entries related to differences "
                    "between exchange rates."
                )
            )
        if not journal.company_id.income_currency_exchange_account_id.id:
            raise UserError(
                _(
                    "You should configure the 'Gain Exchange Rate Account' "
                    "in your company settings, to manage automatically the "
                    "booking of accounting entries related to differences "
                    "between exchange rates."
                )
            )

        # Create the move.
        exchange_move = (
            self.env["account.move"]
            .with_context(skip_invoice_sync=True, skip_compute_balance_ref=True)
            .create(move_vals)
        )
        exchange_move._post(soft=False)

        # Reconcile lines to the newly created exchange difference
        # journal entry by creating more partials.
        for source_line, sequence in exchange_diff_vals["to_reconcile"]:
            exchange_diff_line = exchange_move.line_ids[sequence]
            (exchange_diff_line + source_line).with_context(
                no_exchange_difference=True
            ).reconcile()

        return exchange_move

    def _copy_data_extend_business_fields(self, values):
        super(__class__, self)._copy_data_extend_business_fields(values)
        values["balance_ref"] = self.balance_ref or 0.0
