from odoo import fields, models


class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    is_payroll_rate = fields.Boolean(string="Payroll rate")
