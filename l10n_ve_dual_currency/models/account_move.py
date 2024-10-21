from collections import defaultdict

from odoo import Command, _, api, fields, models
from odoo.tools import float_is_zero
from odoo.tools.misc import groupby

from odoo.addons.account.models.account_move import TYPE_REVERSE_MAP
from odoo.addons.purchase_stock.models.account_invoice import AccountMove as AM


class AccountMove(models.Model):
    _inherit = "account.move"

    currency_ref_id = fields.Many2one(related="company_id.currency_ref_id")
    global_rate_ref = fields.Boolean(
        string="Tasa global",
        default=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    currency_rate_ref = fields.Many2one(
        "res.currency.rate",
        string="Tasa de cambio",
        tracking=True,
        default=lambda self: self.env.company.currency_ref_id.get_currency_rate(),
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain="[('currency_id', '=', currency_ref_id)]",
    )
    amount_total_ref = fields.Monetary(
        string="Total ope.",
        compute="_compute_amount_ref",
        store=True,
        currency_field="currency_ref_id",
    )
    amount_untaxed_ref = fields.Monetary(
        string="Base imponible ope.",
        compute="_compute_amount_ref",
        store=True,
        currency_field="currency_ref_id",
    )
    amount_residual_ref = fields.Monetary(
        string="Importe adeudado ope.",
        compute="_compute_amount_ref",
        store=True,
        currency_field="currency_ref_id",
    )

    @api.depends("line_ids.balance_ref", "amount_residual")
    def _compute_amount_ref(self):
        for move in self:
            total_untaxed, total = 0.0, 0.0
            total_residual = 0.0
            for line in move.line_ids:
                if move.is_invoice(True):
                    if line.display_type == "tax" or (
                        line.display_type == "rounding" and line.tax_repartition_line_id
                    ):
                        total += line.balance_ref
                    elif line.display_type in ("product", "rounding"):
                        total_untaxed += line.balance_ref
                        total += line.balance_ref
                    elif line.display_type == "payment_term":
                        total_residual += line.amount_residual_ref
                elif line.debit:
                    total += line.balance_ref
            move.amount_untaxed_ref = -total_untaxed
            move.amount_total_ref = abs(total) if move.move_type == "entry" else -total
            move.amount_residual_ref = total_residual

    @api.onchange("global_rate_ref", "date")
    def _onchange_global_rate_ref(self):
        if self.global_rate_ref:
            self.currency_rate_ref = self.currency_ref_id.get_currency_rate(
                date=self.date
            )
        else:
            self.currency_rate_ref = False

    def _compute_payments_widget_to_reconcile_info(self):
        for move in self:
            move.invoice_outstanding_credits_debits_widget = False
            move.invoice_has_outstanding = False

            if (
                move.state != "posted"
                or move.payment_state not in ("not_paid", "partial")
                or not move.is_invoice(include_receipts=True)
            ):
                continue

            pay_term_lines = move.line_ids.filtered(
                lambda line: line.account_id.account_type
                in ("asset_receivable", "liability_payable")
            )

            domain = [
                ("account_id", "in", pay_term_lines.account_id.ids),
                ("parent_state", "=", "posted"),
                ("partner_id", "=", move.commercial_partner_id.id),
                ("reconciled", "=", False),
                "|",
                ("amount_residual", "!=", 0.0),
                ("amount_residual_currency", "!=", 0.0),
            ]

            payments_widget_vals = {
                "outstanding": True,
                "content": [],
                "move_id": move.id,
            }

            if move.is_inbound():
                domain.append(("balance", "<", 0.0))
                payments_widget_vals["title"] = _("Outstanding credits")
            else:
                domain.append(("balance", ">", 0.0))
                payments_widget_vals["title"] = _("Outstanding debits")

            for line in self.env["account.move.line"].search(domain):
                if line.currency_id == move.currency_id:
                    # Same foreign currency.
                    amount = abs(line.amount_residual_currency)
                elif move.currency_id == move.currency_ref_id:
                    amount = move.currency_id.round(
                        abs(line.amount_residual) * line.currency_rate_ref.rate
                    )
                else:
                    # Different foreign currencies.
                    amount = line.company_currency_id._convert(
                        abs(line.amount_residual),
                        move.currency_id,
                        move.company_id,
                        line.date,
                    )

                if move.currency_id.is_zero(amount):
                    continue

                payments_widget_vals["content"].append(
                    {
                        "journal_name": line.ref or line.move_id.name,
                        "amount": amount,
                        "currency_id": move.currency_id.id,
                        "id": line.id,
                        "move_id": line.move_id.id,
                        "date": fields.Date.to_string(line.date),
                        "account_payment_id": line.payment_id.id,
                    }
                )

            if not payments_widget_vals["content"]:
                continue

            move.invoice_outstanding_credits_debits_widget = payments_widget_vals
            move.invoice_has_outstanding = True

    def _reverse_moves(self, default_values_list=None, cancel=False):
        """Reverse a recordset of account.move.
        If cancel parameter is true, the reconcilable or liquidity lines
        of each original move will be reconciled with its reverse's.
        :param default_values_list: A list of default values to consider per move.
                                    ('type' & 'reversed_entry_id' are computed in
                                    the method).
        :return:                    An account.move recordset, reverse of the current
                                    self.
        """
        if not default_values_list:
            default_values_list = [{} for move in self]

        if cancel:
            lines = self.mapped("line_ids")
            # Avoid maximum recursion depth.
            if lines:
                lines.remove_move_reconcile()

        reverse_moves = self.env["account.move"]
        for move, default_values in zip(self, default_values_list, strict=True):
            default_values.update(
                {
                    "move_type": TYPE_REVERSE_MAP[move.move_type],
                    "reversed_entry_id": move.id,
                }
            )
            reverse_moves += move.with_context(
                move_reverse_cancel=cancel,
                include_business_fields=True,
                skip_invoice_sync=move.move_type == "entry",
            ).copy(default_values)

        reverse_moves.with_context(skip_invoice_sync=cancel).write(
            {
                "line_ids": [
                    Command.update(
                        line.id,
                        {
                            "balance": -line.balance,
                            "amount_currency": -line.amount_currency,
                            "balance_ref": -line.balance_ref,
                        },
                    )
                    for line in reverse_moves.line_ids.with_context(
                        skip_compute_balance_ref=True
                    )
                    if line.move_id.move_type == "entry" or line.display_type == "cogs"
                ]
            }
        )

        # Reconcile moves together to cancel the previous one.
        if cancel:
            reverse_moves.with_context(
                move_reverse_cancel=cancel, skip_compute_balance_ref=True
            )._post(soft=False)
            for move, reverse_move in zip(self, reverse_moves, strict=True):
                group = defaultdict(list)
                for line in (move.line_ids + reverse_move.line_ids).filtered(
                    lambda L: not L.reconciled
                ):
                    group[(line.account_id, line.currency_id)].append(line.id)
                for (account, dummy), line_ids in group.items():
                    if account.reconcile or account.account_type in (
                        "asset_cash",
                        "liability_credit_card",
                    ):
                        self.env["account.move.line"].browse(line_ids).with_context(
                            move_reverse_cancel=cancel
                        ).reconcile()

        return reverse_moves


def _post(self, soft=True):
    if not self._context.get("move_reverse_cancel"):
        self.env["account.move.line"].create(
            self._stock_account_prepare_anglo_saxon_in_lines_vals()
        )

    # Create correction layer and impact accounts if invoice price is different
    stock_valuation_layers = self.env["stock.valuation.layer"].sudo()
    valued_lines = self.env["account.move.line"].sudo()
    for invoice in self:
        if invoice.sudo().stock_valuation_layer_ids:
            continue
        if invoice.move_type in ("in_invoice", "in_refund", "in_receipt"):
            valued_lines |= invoice.invoice_line_ids.filtered(
                lambda line: line.product_id
                and line.product_id.cost_method != "standard"
            )
    if valued_lines:
        svls, _amls = valued_lines._apply_price_difference()
        stock_valuation_layers |= svls

    for (product, company), dummy in groupby(
        stock_valuation_layers, key=lambda svl: (svl.product_id, svl.company_id)
    ):
        product = product.with_company(company.id)
        if not float_is_zero(
            product.quantity_svl, precision_rounding=product.uom_id.rounding
        ):
            product.sudo().with_context(disable_auto_svl=True).write(
                {
                    "standard_price": product.value_svl / product.quantity_svl,
                    "standard_price_ref": product.value_svl_ref / product.quantity_svl,
                }
            )

    if stock_valuation_layers:
        stock_valuation_layers._validate_accounting_entries()

    posted = super(AM, self)._post(soft)
    # The invoice reference is set during the super call
    for layer in stock_valuation_layers:
        description = f"{layer.account_move_line_id.move_id.display_name} - {layer.product_id.display_name}"
        layer.description = description
        if layer.product_id.valuation != "real_time":
            continue
        layer.account_move_id.ref = description
        layer.account_move_id.line_ids.write({"name": description})

    return posted


AM._post = _post
