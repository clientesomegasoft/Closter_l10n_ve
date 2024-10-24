from odoo import Command, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    withholding_municipal_ids = fields.One2many(
        "account.withholding.municipal",
        "invoice_id",
        string="Retenciones de municipales",
        readonly=True,
        domain=[("state", "!=", "cancel")],
    )
    municipal_concept_ids = fields.Many2many(
        "account.municipal.concept",
        string="Conceptos de retención municipal",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
    )
    apply_withholding_municipal = fields.Boolean(
        compute="_compute_apply_withholding_municipal"
    )

    @api.depends("partner_id", "move_type")
    def _compute_apply_withholding_municipal(self):
        for move in self:
            move.apply_withholding_municipal = (
                move.is_sale_document() and move.partner_id.is_municipal_agent
            ) or (
                move.is_purchase_document()
                and move.company_id.partner_id.is_municipal_agent
            )

    def _post(self, soft=True):
        to_post = super()._post(soft)
        withholding_ids = self.env["account.withholding.municipal"]

        for move in to_post:
            if move.apply_withholding_municipal and move.municipal_concept_ids:
                values = move._get_withholding_municipal_properties()
                base_amount = abs(
                    self.company_id.fiscal_currency_id.id == self.company_currency_id.id
                    and self.amount_untaxed_signed
                    or self.amount_untaxed_ref
                )

                for concept_id in move.municipal_concept_ids:
                    line_ids = {
                        "municipal_concept_id": concept_id.id,
                        "base_amount": base_amount,
                        "amount": base_amount * concept_id.rate / 100,
                    }
                    withholding_id = move.withholding_municipal_ids.filtered(
                        lambda w: w.line_ids.municipal_concept_id.id == concept_id.id
                        and w.state == "draft"
                    )
                    if withholding_id:
                        values["line_ids"] = [
                            Command.update(withholding_id.line_ids.id, line_ids)
                        ]
                        withholding_id.write(values)
                    else:
                        values["line_ids"] = [Command.create(line_ids)]
                        withholding_id = self.env[
                            "account.withholding.municipal"
                        ].create(values)
                    withholding_ids |= withholding_id

        if self.withholding_municipal_ids:
            (self.mapped("withholding_municipal_ids") - withholding_ids).button_cancel()

        return to_post

    def button_draft(self):
        res = super().button_draft()
        self.mapped("withholding_municipal_ids").filtered(
            lambda w: w.state == "posted"
        ).button_draft()
        return res

    def button_cancel(self):
        res = super().button_cancel()
        self.mapped("withholding_municipal_ids").filtered(
            lambda w: w.state == "draft"
        ).button_cancel()
        return res

    def button_open_withholding_municipal(self):
        self.ensure_one()
        action = {
            "type": "ir.actions.act_window",
            "name": "Retención municipal",
            "res_model": "account.withholding.municipal",
            "context": {"create": False},
        }
        if len(self.withholding_municipal_ids) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": self.withholding_municipal_ids.id,
                }
            )
        else:
            action.update(
                {
                    "view_mode": "tree,form",
                    "domain": [("id", "in", self.withholding_municipal_ids.ids)],
                }
            )
        return action

    def _get_withholding_municipal_properties(self):
        self.ensure_one()
        if self.is_sale_document():
            return {
                "type": "customer",
                "invoice_id": self.id,
                "date": self.date,
                "agent_id": self.partner_id.id,
                "subject_id": self.company_id.partner_id.id,
                "journal_id": self.company_id.out_municipal_journal_id.id,
                "withholding_account_id": self.company_id.out_municipal_account_id.id,
                "destination_account_id": self.partner_id.property_account_receivable_id.id,
            }
        elif self.is_purchase_document():
            return {
                "type": "supplier",
                "invoice_id": self.id,
                "date": self.date,
                "agent_id": self.company_id.partner_id.id,
                "subject_id": self.partner_id.id,
                "journal_id": self.company_id.in_municipal_journal_id.id,
                "withholding_account_id": self.company_id.in_municipal_account_id.id,
                "destination_account_id": self.company_id.partner_id.property_account_payable_id.id,  # noqa: B950
            }
