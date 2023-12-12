# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ContractSocialBenefitLiabilitiesField(models.Model):
    _inherit = 'hr.contract'

    social_benefits_generated = fields.Monetary(string="Social benefits generated", help="", currency_field='social_benefits_generated_currency', tracking=True)
    provisions_social_benefits_generated = fields.Monetary(string="Provisions Social benefits generated", help="", currency_field='social_benefits_generated_currency', tracking=True)
    social_benefits_generated_previous_amount = fields.Monetary(string="Social benefits generated previous amount", help="", currency_field='social_benefits_generated_currency', tracking=True)
    social_benefits_generated_currency = fields.Many2one(comodel_name='res.currency',default=lambda self: self.env.company.currency_id)

    accrued_social_benefits = fields.Monetary(string="Accrued social benefits", help="", currency_field='accrued_social_benefits_currency', tracking=True)
    accrued_social_benefits_previous_amount = fields.Monetary(string="Accrued social benefits _previous amount", help="", currency_field='accrued_social_benefits_currency', tracking=True)
    accrued_social_benefits_currency = fields.Many2one(comodel_name='res.currency',default=lambda self: self.env.company.currency_id)

    advances_of_social_benefits = fields.Monetary(string="Advances of social benefits", help="", currency_field='advances_of_social_benefits_currency', tracking=True)
    advances_of_social_benefits_previous_amount = fields.Monetary(string="Advances of social benefits _previous amount", help="", currency_field='advances_of_social_benefits_currency', tracking=True)
    advances_of_social_benefits_currency = fields.Many2one(comodel_name='res.currency',default=lambda self: self.env.company.currency_id)

    total_available_social_benefits_generated = fields.Monetary(string="Total Available Social benefits generated", help="", currency_field='total_available_social_benefits_generated_currency', tracking=True)
    total_available_social_benefits_generated_currency = fields.Many2one(comodel_name='res.currency',default=lambda self: self.env.company.currency_id)

    benefit_interest = fields.Monetary(string="Benefit interest", help="", currency_field='benefit_interest_currency', tracking=True)
    provisions_benefit_interest = fields.Monetary(string="Provisions Benefit interest", help="", currency_field='benefit_interest_currency', tracking=True)
    benefit_interest_previous_amount = fields.Monetary(string="Benefit interest previous amount", help="", currency_field='benefit_interest_currency', tracking=True)
    benefit_interest_currency = fields.Many2one(comodel_name='res.currency',default=lambda self: self.env.company.currency_id)

    days_per_year_accumulated = fields.Monetary(string="Days per year accumulated", help="", currency_field='days_per_year_accumulated_currency', tracking=True)
    provisions_days_per_year_accumulated = fields.Monetary(string="Provisions Days per year accumulated", help="", currency_field='days_per_year_accumulated_currency', tracking=True)
    days_per_year_accumulated_previous_amount = fields.Monetary(string="Days per year accumulated previous amount", help="", currency_field='days_per_year_accumulated_currency', tracking=True)
    days_per_year_accumulated_currency = fields.Many2one(comodel_name='res.currency',default=lambda self: self.env.company.currency_id)

    provisions_benefit_interest_date = fields.Date(string='Last Benefit interest Calculation', help='Indicates the date of the last Benefit interest payment calculation.')
    provisions_social_benefits_generated_date = fields.Date(string='Last Benefit social Calculation', help='Indicates the date of the last Benefit interest payment calculation.')
    provisions_days_per_year_accumulated_date = fields.Date(string='Last Benefit year accumulated Calculation', help='Indicates the date of the last Benefit interest payment calculation.')