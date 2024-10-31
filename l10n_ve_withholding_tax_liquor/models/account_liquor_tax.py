from odoo import fields, models


class AccountLiquorTax(models.Model):
    _name = "account.liquor.tax"
    _description = "Liquor tax"

    name = fields.Char(string="Name of the tax", required=True)
    rate = fields.Float(string="Percentage", digits=(5, 2))

    _sql_constraints = [
        (
            "check_rate",
            "CHECK(rate > 0 AND rate <= 100)",
            "The amount must be in a range greater than 0 and less than or equal to 100.",
        ),
    ]
