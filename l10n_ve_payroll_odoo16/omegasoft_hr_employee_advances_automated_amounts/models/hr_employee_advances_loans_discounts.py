# -*- coding: utf-8 -*-

from odoo import models, fields, api

SHARED_ADVANCE_LOAN_TYPES = [
    ('social_benefits', 'Social benefits'),
    ('profits', 'Profits'),
    ('benefit_interest', 'Benefit interest'),
    ('days_per_year', 'Days per year'),
]


class HrEmployeeAdvancesLoansDiscounts(models.Model):
    _inherit = "hr_employee_advances_loans_discounts"

    use_available_amount_per_employee = fields.Boolean('Use Available Amount')
    shared_type_advance_loan = fields.Selection(
        SHARED_ADVANCE_LOAN_TYPES,
        string = 'Global type advance loan',
        default = 'profits',
    )

    @api.onchange('name', 'company_id', 'employee_ids', 'use_available_amount_per_employee', 'shared_type_advance_loan')
    def _create_loans_lines_onchange_global_context(self):
        for record in self:
            if not record.name == 'company':
                record.use_available_amount_per_employee = False
                continue

            if record.use_available_amount_per_employee:
                record._load_employee_advances_loans_discounts_lines()
                

    def _load_employee_advances_loans_discounts_lines(self):
        result = [fields.Command.clear()]
        result.extend(self._employee_advances_loans_discounts_lines_to_create())
        self.advances_loans_discounts_line_ids = result

    def _employee_advances_loans_discounts_lines_to_create(self):
        result = []
        for employee in self.employee_ids:
            benefits = employee._get_employee_available_benefits(
                            self.shared_type_advance_loan,
                            self.company_currency,
                            self.rate_id)
            if benefits.available_benefits_amount_limit > 0:
                to_append = fields.Command.create({
                    'product_employee_ids': [fields.Command.link(employee.id)],
                    'employee_file_code_ids': [fields.Command.link(employee.employee_file_code_id.id)],
                    'type_advance_loan': (self.shared_type_advance_loan
                                        if self.use_available_amount_per_employee
                                        else False),
                    'currency_id': employee._get_currency_for_employee_available_benefits(),
                    'amount': benefits.available_benefits_amount_limit,
                })
                result.append(to_append)
        return result
        