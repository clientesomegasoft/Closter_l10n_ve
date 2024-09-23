from odoo import Command, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    withholding_iva_id = fields.Many2one(
        "account.withholding.iva", string="Retencion de IVA", readonly=True, copy=False
    )

    def _post(self, soft=True):
        to_post = super()._post(soft)
        for move in to_post:
            if move._apply_withholding_iva():
                values = move._get_withholding_iva_properties()
                if move.withholding_iva_id:
                    move.withholding_iva_id.write(values)
                else:
                    move.withholding_iva_id = self.env[
                        "account.withholding.iva"
                    ].create(values)
            elif move.withholding_iva_id:
                move.withholding_iva_id.button_cancel()
        return to_post

    def button_draft(self):
        super().button_draft()
        for move in self:
            if move.withholding_iva_id.state == "posted":
                move.withholding_iva_id.button_draft()

    def button_cancel(self):
        res = super().button_cancel()
        for move in self:
            if move.withholding_iva_id.state == "draft":
                move.withholding_iva_id.button_cancel()
        return res

    def button_open_withholding_iva(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.withholding.iva",
            "context": {"create": False},
            "view_mode": "form",
            "res_id": self.withholding_iva_id.id,
        }

    def _apply_withholding_iva(self):
        self.ensure_one()
        return (
            self.partner_id.person_type_code in ("PJDO", "PNRE")
            and self.line_ids.tax_line_id
            and (
                (
                    self.is_sale_document()
                    and self.partner_id.is_iva_agent
                    and self.company_id.partner_id.iva_rate_id
                )
                or (
                    self.is_purchase_document()
                    and self.company_id.partner_id.is_iva_agent
                    and self.partner_id.iva_rate_id
                )
            )
        )

    def _get_withholding_iva_properties(self):
        self.ensure_one()
        if self.is_sale_document():
            iva_rate = self.company_id.partner_id.iva_rate_id.name / 100
            values = {
                "type": "customer",
                "agent_id": self.partner_id.id,
                "subject_id": self.company_id.partner_id.id,
                "iva_rate_id": self.company_id.partner_id.iva_rate_id.id,
                "journal_id": self.company_id.out_iva_journal_id.id,
                "withholding_account_id": self.company_id.out_iva_account_id.id,
                "destination_account_id": self.partner_id.property_account_receivable_id.id,
            }
        elif self.is_purchase_document():
            iva_rate = self.partner_id.iva_rate_id.name / 100
            values = {
                "type": "supplier",
                "agent_id": self.company_id.partner_id.id,
                "subject_id": self.partner_id.id,
                "iva_rate_id": self.partner_id.iva_rate_id.id,
                "journal_id": self.company_id.in_iva_journal_id.id,
                "withholding_account_id": self.company_id.in_iva_account_id.id,
                "destination_account_id": self.partner_id.property_account_payable_id.id,
            }

        exempt_amount = 0.0
        line_ids = [Command.clear()]
        tax_base_amount, balance = (
            self.company_id.fiscal_currency_id.id == self.company_currency_id.id
            and ("tax_base_amount", "balance")
            or ("tax_base_amount_ref", "balance_ref")
        )

        for line in self.line_ids:
            if (
                line.display_type == "product"
                and line.price_total == line.price_subtotal
            ):
                exempt_amount += abs(getattr(line, balance))
            elif line.display_type == "tax" and line.tax_line_id:
                line_ids.append(
                    Command.create(
                        {
                            "tax_line_id": line.tax_line_id.id,
                            # -- MONTOS EN MONEDA FISCAL --#
                            "tax_base_amount": getattr(line, tax_base_amount),
                            "tax_amount": abs(getattr(line, balance)),
                            # -- MONTOS BASE EN OTRAS MONEDAS--#
                            "base_amount_currency": abs(
                                line.amount_currency
                            ),  # in invoice currency
                            "base_amount_company_currency": abs(
                                line.balance
                            ),  # in company currency
                            "base_amount_currency_ref": abs(
                                line.balance_ref
                            ),  # in referencial currency
                        }
                    )
                )

        return {
            **values,
            "invoice_id": self.id,
            "date": self.date,
            "exempt_amount": exempt_amount,
            "line_ids": line_ids,
        }
