# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class ContractEmployeeSeniority(models.Model):
    _inherit = 'hr.contract'
    
    days_of_seniority = fields.Float(string="Days of seniority", help="Indicates the days of employee seniority.", tracking=True)

    months_of_seniority = fields.Float(string="Months of seniority", help="Indicates the months of employee seniority.", tracking=True)

    years_of_seniority = fields.Float(string="Years of seniority", help="Indicates the years of employee seniority.", tracking=True)

    # Return the current contract of the employee
    def _get_current_contract(self, employee):
        # Active contract(s) of the employee
        actives_contracts = employee._get_first_contracts()
        date_current_contract = max(actives_contracts.mapped(
            'date_start')) if actives_contracts else False
        current_contract = actives_contracts.filtered(
            lambda c: c.date_start == date_current_contract)
        if len(current_contract) > 1:
            current_contract = current_contract[0]
        return current_contract

    def _employee_seniority(self):
        current_contract = False
        seniority = False
        today = fields.Date.from_string(fields.Date.today())
        employee_obj = self.env['hr.employee'].search([('active', '=', True)]).filtered(lambda self: self.contracts_count >= 1)
        for employee in employee_obj:
            current_contract = self._get_current_contract(employee)
            if current_contract and not current_contract.date_end:
                seniority = relativedelta(today, current_contract.date_start)
            elif current_contract and current_contract.date_end:
                seniority = relativedelta(current_contract.date_end, current_contract.date_start)
            if seniority:
                current_contract.days_of_seniority = seniority.days
                current_contract.months_of_seniority = seniority.months
                current_contract.years_of_seniority = seniority.years