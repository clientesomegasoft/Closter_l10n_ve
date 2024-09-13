# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    is_payroll_rate = fields.Boolean(string="Payroll rate")
