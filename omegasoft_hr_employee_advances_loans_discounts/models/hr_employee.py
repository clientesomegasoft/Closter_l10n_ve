# -*- coding: utf-8 -*-

from odoo import models, fields, api

from dataclasses import dataclass
from typing import Any

from logging import getLogger

_logger = getLogger(__name__)

@dataclass
class AvailableBenefitsData:
    available_benefits_currency: Any = 0
    available_benefits_amount_limit: float = False

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.model
    def _get_currency_for_employee_available_benefits(self):
        # PATCH: Fix this mess in Odoo 17.0
        ves = self.env['res.currency'].search( [('name', '=', 'VES')] )
        if not ves:
            ves = self.env.company.currency_id
            _logger.warning('USING env.company.currency_id {ves} as default value for employee advances')
        return ves

    def _get_employee_available_benefits(self, type_advance_loan, currency_id = None, rate_id = None):
        """
            Return an object that can be converted to a dict with
            dataclasses.asdict() function.
        """

        result           = AvailableBenefitsData()
        current_contract = self.contract_id
        currency_id      = self.env.company.currency_id
        rate_id          = getattr(rate_id, 'name', None) or fields.Datetime.today()

        if not current_contract:
            return result

        amount   = 0
        currency = self._get_currency_for_employee_available_benefits()

        limit_amount = 0
        if type_advance_loan == 'profits':
            limit_amount = current_contract.earnings_generated_total_available
        elif type_advance_loan == 'social_benefits':
            amount   = current_contract.total_available_social_benefits_generated
            limit_amount = 0.75 * amount
        elif type_advance_loan == 'benefit_interest':
            limit_amount = current_contract.benefit_interest
        elif type_advance_loan == 'days_per_year':
            limit_amount = current_contract.days_per_year_accumulated

        result.available_benefits_currency = currency

        if not currency:
            result.available_benefits_amount_limit = 0
        else:
            result.available_benefits_amount_limit = currency_id.round(
                currency._convert(
                    limit_amount,
                    currency_id, 
                    current_contract.company_id,
                    rate_id)
            )
        
        return result
