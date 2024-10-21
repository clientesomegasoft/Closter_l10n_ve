from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    currency_ref_id = fields.Many2one(related="company_id.currency_ref_id")
    currency_rate_ref = fields.Many2one(
        "res.currency.rate",
        string="Tasa",
        compute="_compute_currency_rate_ref",
        store=True,
        readonly=False,
        domain="[('currency_id', '=', currency_ref_id)]",
    )

    @api.depends("payment_date", "currency_ref_id")
    def _compute_currency_rate_ref(self):
        for wizard in self:
            wizard.currency_rate_ref = wizard.currency_ref_id.get_currency_rate(
                date=wizard.payment_date
            )

    def _get_total_amount_in_wizard_currency_to_full_reconcile(
        self, batch_result, early_payment_discount=True
    ):
        """Compute the total amount needed in the currency of the wizard
        to fully reconcile the batch of journal items passed as
        parameter.

        :param batch_result:    A batch returned by '_get_batches'.
        :return:                An amount in the currency of the wizard.
        """
        self.ensure_one()
        comp_curr = self.company_id.currency_id
        if self.source_currency_id == self.currency_id:
            # Same currency (manage the early payment discount).
            return self._get_total_amount_using_same_currency(
                batch_result, early_payment_discount=early_payment_discount
            )
        elif self.source_currency_id != comp_curr and self.currency_id == comp_curr:
            # Foreign currency on source line but the company
            # currency one on the opposite line.
            if self.source_currency_id == self.currency_ref_id:
                return comp_curr.round(
                    self.source_amount_currency / self.currency_rate_ref.rate
                ), False
            else:
                return self.source_currency_id._convert(
                    self.source_amount_currency,
                    comp_curr,
                    self.company_id,
                    self.payment_date,
                ), False
        elif self.source_currency_id == comp_curr and self.currency_id != comp_curr:
            # Company currency on source line but a foreign
            # currency one on the opposite line.
            if self.currency_id == self.currency_ref_id:
                return abs(
                    sum(
                        self.currency_id.round(
                            aml.amount_residual * aml.move_id.currency_rate_ref.rate
                        )
                        for aml in batch_result["lines"]
                    )
                ), False
            else:
                return abs(
                    sum(
                        comp_curr._convert(
                            aml.amount_residual,
                            self.currency_id,
                            self.company_id,
                            aml.date,
                        )
                        for aml in batch_result["lines"]
                    )
                ), False
        else:
            # Foreign currency on payment different than
            # the one set on the journal entries.
            return comp_curr._convert(
                self.source_amount, self.currency_id, self.company_id, self.payment_date
            ), False

    @api.depends(
        "can_edit_wizard",
        "source_amount",
        "source_amount_currency",
        "source_currency_id",
        "company_id",
        "currency_id",
        "payment_date",
        "currency_rate_ref",
    )
    def _compute_amount(self):
        res = super(__class__, self)._compute_amount()
        return res

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = {
            "date": self.payment_date,
            "amount": self.amount,
            "payment_type": self.payment_type,
            "partner_type": self.partner_type,
            "ref": self.communication,
            "journal_id": self.journal_id.id,
            "currency_id": self.currency_id.id,
            "partner_id": self.partner_id.id,
            "partner_bank_id": self.partner_bank_id.id,
            "payment_method_line_id": self.payment_method_line_id.id,
            "destination_account_id": self.line_ids[0].account_id.id,
            "write_off_line_vals": [],
            "currency_rate_ref": self.currency_rate_ref.id,
        }

        conversion_rate = (
            self.currency_rate_ref.rate
            if self.currency_id == self.currency_ref_id
            else self.env["res.currency"]._get_conversion_rate(
                self.currency_id,
                self.company_id.currency_id,
                self.company_id,
                self.payment_date,
            )
        )

        if self.payment_difference_handling == "reconcile":
            if self.early_payment_discount_mode:
                epd_aml_values_list = []
                for aml in batch_result["lines"]:
                    if aml._is_eligible_for_early_payment_discount(
                        self.currency_id, self.payment_date
                    ):
                        epd_aml_values_list.append(
                            {
                                "aml": aml,
                                "amount_currency": -aml.amount_residual_currency,
                                "balance": aml.company_currency_id.round(
                                    -aml.amount_residual_currency * conversion_rate
                                ),
                            }
                        )

                open_amount_currency = self.payment_difference * (
                    -1 if self.payment_type == "outbound" else 1
                )
                open_balance = self.company_id.currency_id.round(
                    open_amount_currency * conversion_rate
                )
                early_payment_values = self.env[
                    "account.move"
                ]._get_invoice_counterpart_amls_for_early_payment_discount(
                    epd_aml_values_list, open_balance
                )
                for aml_values_list in early_payment_values.values():
                    payment_vals["write_off_line_vals"] += aml_values_list

            elif not self.currency_id.is_zero(self.payment_difference):
                if self.payment_type == "inbound":
                    # Receive money.
                    write_off_amount_currency = self.payment_difference
                else:  # if self.payment_type == 'outbound':
                    # Send money.
                    write_off_amount_currency = -self.payment_difference

                write_off_balance = self.company_id.currency_id.round(
                    write_off_amount_currency * conversion_rate
                )
                payment_vals["write_off_line_vals"].append(
                    {
                        "name": self.writeoff_label,
                        "account_id": self.writeoff_account_id.id,
                        "partner_id": self.partner_id.id,
                        "currency_id": self.currency_id.id,
                        "amount_currency": write_off_amount_currency,
                        "balance": write_off_balance,
                    }
                )
        return payment_vals
