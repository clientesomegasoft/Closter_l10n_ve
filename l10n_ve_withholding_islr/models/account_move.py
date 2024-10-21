from collections import defaultdict

from odoo import Command, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    withholding_islr_id = fields.Many2one(
        "account.withholding.islr",
        string="Retencion de ISLR",
        readonly=True,
        copy=False,
    )

    def _post(self, soft=True):
        to_post = super()._post(soft)
        for move in to_post:
            if move._apply_withholding_islr():
                values = move._get_withholding_islr_properties()
                if move.withholding_islr_id:
                    move.withholding_islr_id.write(values)
                else:
                    move.withholding_islr_id = self.env[
                        "account.withholding.islr"
                    ].create(values)
            elif move.withholding_islr_id:
                move.withholding_islr_id.button_cancel()
        return to_post

    def button_draft(self):
        res = super().button_draft()
        for move in self:
            if move.withholding_islr_id.state == "posted":
                move.withholding_islr_id.button_draft()
        return res

    def button_cancel(self):
        res = super().button_cancel()
        for move in self:
            if move.withholding_islr_id.state == "draft":
                move.withholding_islr_id.button_cancel()
        return res

    def button_open_withholding_islr(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.withholding.islr",
            "context": {"create": False},
            "view_mode": "form",
            "res_id": self.withholding_islr_id.id,
        }

    def _apply_withholding_islr(self):
        self.ensure_one()
        return self.invoice_line_ids.filtered(
            lambda line: line.product_id.apply_withholding_islr
        ) and (
            (
                self.is_sale_document()
                and self.partner_id.is_islr_agent
                and not self.company_id.partner_id.is_islr_exempt
            )
            or (
                self.is_purchase_document()
                and self.company_id.partner_id.is_islr_agent
                and not self.partner_id.is_islr_exempt
            )
        )

    def _get_withholding_islr_properties(self):
        self.ensure_one()

        field_balance = (
            self.company_id.fiscal_currency_id.id == self.company_currency_id.id
            and "balance"
            or "balance_ref"
        )
        concepts = defaultdict(float)
        for line in self.invoice_line_ids:
            if line.product_id.islr_concept_id:
                concepts[line.product_id.islr_concept_id] += abs(
                    getattr(line, field_balance)
                )

        person_type_id = (
            self.partner_id.is_a_society
            and self.env.ref("l10n_ve_fiscal_identification.person_type_pnre")
            or self.partner_id.person_type_id
        )
        ut = self.env["account.ut"].get_current_ut()
        line_ids = [Command.clear()]

        for concept, base in concepts.items():
            rate_id = concept.get_concept_rate(
                person_type_id, base_ut=(base / ut.amount)
            )
            subtraction = rate_id["subtraction"] * ut.amount
            line_ids.append(
                Command.create(
                    {
                        "islr_concept_id": concept.id,
                        "rate_id": rate_id["id"],
                        "base_amount": base,
                        "amount": base * rate_id["base"] * rate_id["rate"]
                        - subtraction,
                        "percent": rate_id["rate"] * 100,
                        "subtraction": subtraction,
                    }
                )
            )

        if self.is_sale_document():
            return {
                "type": "customer",
                "agent_id": self.partner_id.id,
                "subject_id": self.company_id.partner_id.id,
                "journal_id": self.company_id.out_islr_journal_id.id,
                "withholding_account_id": self.company_id.out_islr_account_id.id,
                "destination_account_id": self.partner_id.property_account_receivable_id.id,
                "invoice_id": self.id,
                "date": self.date,
                "line_ids": line_ids,
            }
        elif self.is_purchase_document():
            return {
                "type": "supplier",
                "agent_id": self.company_id.partner_id.id,
                "subject_id": self.partner_id.id,
                "journal_id": self.company_id.in_islr_journal_id.id,
                "withholding_account_id": self.company_id.in_islr_account_id.id,
                "destination_account_id": self.company_id.partner_id.property_account_payable_id.id,
                "invoice_id": self.id,
                "date": self.date,
                "line_ids": line_ids,
            }
