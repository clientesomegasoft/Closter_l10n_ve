from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    apply_igtf = fields.Selection(
        [("cash", "Cash"), ("bank", "Bank")], compute="_compute_apply_igtf"
    )
    calculate_igtf = fields.Boolean(string="Permitir IGTF", default=True)
    igtf_journal_id = fields.Many2one(
        "account.journal",
        string="Diario IGTF",
        check_company=True,
        domain="[('type', 'in', ('bank', 'cash'))]",
    )
    igtf_amount = fields.Monetary(string="Importe IGTF", compute="_compute_igtf_amount")

    @api.depends(
        "payment_type",
        "currency_id",
        "journal_id.type",
        "partner_id.apply_igtf",
        "company_id.partner_id.apply_igtf",
    )
    def _compute_apply_igtf(self):
        for pay in self:
            pay.apply_igtf = False
            if pay.currency_id != pay.company_id.fiscal_currency_id:
                if pay.journal_id.type == "cash" and (
                    (
                        pay.payment_type == "inbound"
                        and pay.company_id.partner_id.apply_igtf
                    )
                    or (pay.payment_type == "outbound" and pay.partner_id.apply_igtf)
                ):
                    pay.apply_igtf = "cash"
                elif (
                    pay.journal_id.type == "bank"
                    and pay.payment_type == "outbound"
                    and pay.partner_id.apply_igtf
                ):
                    pay.apply_igtf = "bank"

    @api.depends("amount", "currency_id", "apply_igtf", "company_id.igtf_percentage")
    def _compute_igtf_amount(self):
        for pay in self:
            pay.igtf_amount = (
                self.apply_igtf
                and self.currency_id.round(
                    self.amount * self.company_id.igtf_percentage / 100
                )
                or 0.0
            )

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super(__class__, self)._create_payment_vals_from_wizard(
            batch_result
        )
        payment_vals.update(
            {
                "apply_igtf": self.apply_igtf,
                "calculate_igtf": self.calculate_igtf,
                "igtf_journal_id": self.igtf_journal_id.id,
            }
        )
        return payment_vals
