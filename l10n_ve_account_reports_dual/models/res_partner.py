from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    currency_ref_id = fields.Many2one(
        "res.currency", compute="_get_company_currency_ref"
    )
    total_due_ref = fields.Monetary(
        string="Adeudado total ope.",
        compute="_compute_total_due",
        currency_field="currency_ref_id",
        groups="account.group_account_readonly,account.group_account_invoice",
    )
    total_overdue_ref = fields.Monetary(
        string="Total vencido ope.",
        compute="_compute_total_due",
        currency_field="currency_ref_id",
        groups="account.group_account_readonly,account.group_account_invoice",
    )

    def _get_company_currency_ref(self):
        for partner in self:
            if partner.company_id:
                partner.currency_ref_id = partner.sudo().company_id.currency_ref_id
            else:
                partner.currency_ref_id = self.env.company.currency_ref_id

    @api.depends("unreconciled_aml_ids", "followup_next_action_date")
    @api.depends_context("company", "allowed_company_ids")
    def _compute_total_due(self):
        today = fields.Date.context_today(self)
        for partner in self:
            total_overdue, total_overdue_ref = 0, 0
            total_due, total_due_ref = 0, 0
            for aml in partner.unreconciled_aml_ids:
                is_overdue = (
                    today > aml.date_maturity if aml.date_maturity else today > aml.date
                )
                if aml.company_id == self.env.company and not aml.blocked:
                    total_due += aml.amount_residual
                    total_due_ref += aml.amount_residual_ref
                    if is_overdue:
                        total_overdue += aml.amount_residual
                        total_overdue_ref += aml.amount_residual_ref
            partner.total_due = total_due
            partner.total_due_ref = total_due_ref
            partner.total_overdue = total_overdue
            partner.total_overdue_ref = total_overdue_ref
