from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    apply_withholding_islr = fields.Boolean(
        string="Aplica retención de ISLR", default=False
    )
    islr_concept_id = fields.Many2one(
        "account.islr.concept", string="Concepto de ISLR", ondelete="restrict"
    )

    _sql_constraints = [
        (
            "check_islr_concept",
            "CHECK((type != 'service') OR apply_withholding_islr = FALSE OR (type = 'service' AND apply_withholding_islr = TRUE AND islr_concept_id IS NOT NULL))",  # noqa: B950
            "Para los productos de tipo servicio el concepto de ISLR es requerido.",
        )
    ]

    @api.onchange("type", "apply_withholding_islr")
    def _clean_islr_concept(self):
        if self.type != "service" or not self.apply_withholding_islr:
            self.islr_concept_id = False
