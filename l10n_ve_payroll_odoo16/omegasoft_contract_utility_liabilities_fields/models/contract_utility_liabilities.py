# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ContractLaborLiabilitiesField(models.Model):
    _inherit = 'hr.contract'

    
    earnings_generated = fields.Monetary(string="Earnings generated", help="", currency_field='earnings_generated_currency', tracking=True)
    earnings_generated_previous_amount = fields.Monetary(string="Earnings generated previous amount", help="", currency_field='earnings_generated_currency')
    earnings_generated_currency = fields.Many2one(comodel_name='res.currency',default=lambda self: self.env.company.currency_id)

    advances_granted = fields.Monetary(string="Advances granted", help="", currency_field='advances_granted_currency', tracking=True)
    advances_granted_previous_amount = fields.Monetary(string="Advances granted_previous amount", help="", currency_field='advances_granted_currency')
    advances_granted_currency = fields.Many2one(comodel_name='res.currency',default=lambda self: self.env.company.currency_id)

    earnings_generated_total_available = fields.Monetary(string="Earnings generated Total available", help="", currency_field='earnings_generated_total_available_currency', tracking=True)
    earnings_generated_total_available_currency = fields.Many2one(comodel_name='res.currency',default=lambda self: self.env.company.currency_id)