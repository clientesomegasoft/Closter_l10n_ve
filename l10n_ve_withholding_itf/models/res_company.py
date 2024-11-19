from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    apply_itf = fields.Boolean(string="Automatic retention of ITF")
    itf_percentage = fields.Float(string="ITF Percentage", digits=(5, 2))
    itf_account_id = fields.Many2one(
        "account.account",
        string="ITF Account",
        domain="[('internal_group', '=', 'expense')]",
    )

    _sql_constraints = [
        (
            "check_apply_itf",
            "CHECK(apply_itf = FALSE OR ((itf_percentage > 0 AND itf_percentage <= 100) AND (itf_account_id IS NOT NULL)))",  # noqa: B950
            "The ITF retention percentage must be in a higher range "
            "to 0 and less or equal to 100 and ITF account is required!",
        )
    ]
