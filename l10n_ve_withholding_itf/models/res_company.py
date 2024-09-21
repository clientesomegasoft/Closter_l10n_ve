from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    apply_itf = fields.Boolean(string="Retención automática de ITF")
    itf_percentage = fields.Float(string="Porcentaje ITF", digits=(5, 2))
    itf_account_id = fields.Many2one(
        "account.account",
        string="Cuenta ITF",
        domain="[('internal_group', '=', 'expense')]",
    )

    _sql_constraints = [
        (
            "check_apply_itf",
            "CHECK(apply_itf = FALSE OR ((itf_percentage > 0 AND itf_percentage <= 100) AND (itf_account_id IS NOT NULL)))",
            "El porcentaje de retención ITF debe estar en un rango mayor a 0 y menor o igual a 100 y la cuenta ITF es requerida !",
        )
    ]
