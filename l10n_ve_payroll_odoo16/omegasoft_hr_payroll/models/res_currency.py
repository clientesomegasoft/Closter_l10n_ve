# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    currency_rate_active = fields.Boolean(related='currency_id.active')