from odoo import fields, models


class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    currency_rate_active = fields.Boolean(related="currency_id.active")
