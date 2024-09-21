from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    is_municipal_agent = fields.Boolean(
        string="¿Es agente de retención municipal?", copy=False
    )

    def write(self, vals):
        if vals.get("is_municipal_agent", self.is_municipal_agent) and (
            (
                "partner_type" in vals
                and vals["partner_type"] not in ("customer", "customer_supplier")
            )
            or (
                "person_type_id" in vals
                and vals["person_type_id"]
                != self.env.ref("l10n_ve_fiscal_identification.person_type_pjdo").id
            )
        ):
            vals["is_municipal_agent"] = False
        return super(Partner, self).write(vals)
