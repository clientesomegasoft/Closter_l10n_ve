from odoo import fields, models


class WithholdingIvaRate(models.Model):
    _name = "withholding.iva.rate"
    _description = "VAT withholding rate"

    name = fields.Float(string="Rate")
    description = fields.Char(string="Description")

    _sql_constraints = [
        (
            "check_percentage",
            "CHECK(name > 0 AND name <= 100)",
            "The VAT withholding rate must be greater than zero and less than or equal to 100.",
        )
    ]

    def name_get(self):
        return [(rate.id, f"{rate.name}%") for rate in self]
