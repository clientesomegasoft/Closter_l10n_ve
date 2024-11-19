from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    is_islr_agent = fields.Boolean(
        string="Are you an ISLR withholding agent?", copy=False
    )
    is_islr_exempt = fields.Boolean(
        string="Are you exempt from income tax on purchases?", copy=False
    )
    is_a_society = fields.Boolean(string="Is it a partnership?", copy=False)

    def write(self, vals):
        if vals.get("is_islr_agent", self.is_islr_agent) and (
            (
                "partner_type" in vals
                and vals["partner_type"] not in ("customer", "customer_supplier")
            )
            or (
                "person_type_id" in vals
                and vals["person_type_id"]
                not in (
                    self.env.ref("l10n_ve_fiscal_identification.person_type_pjdo").id,
                    self.env.ref("l10n_ve_fiscal_identification.person_type_pnre").id,
                )
            )
        ):
            vals["is_islr_agent"] = False
        return super(__class__, self).write(vals)
