from odoo import api, fields, models


class AccountUT(models.Model):
    _name = "account.ut"
    _description = "Tax Unit"
    _order = "date desc"

    name = fields.Char(
        string="Reference number",
        required=True,
        help="Reference number according to law.",
    )
    date = fields.Date(
        string="Date",
        required=True,
        help="Date on which the new tax unit becomes effective.",
    )
    amount = fields.Float(string="Amount")

    _sql_constraints = [
        (
            "check_amount",
            "CHECK(amount > 0)",
            "The amount of the tax unit must be greater than zero (0).",
        )
    ]

    @api.model
    def get_current_ut(self):
        return self.search([("date", "<=", fields.Date.today())], limit=1)
