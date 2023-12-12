# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EmployeeFileCode(models.Model):
    _name = 'employee.file.code'
    _description = 'Employee File Code'

    active = fields.Boolean('Active', default=True)

    name = fields.Char('Name')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', default=lambda s: s.env.company)

    _sql_constraints = [
        ('uniq_employee_code', 'UNIQUE (name, company_id)', 'There cannot be two cards with the same name.'),
        ('uniq_employee', 'UNIQUE (employee_id, company_id)', 'There cannot be two cards with the same employee.')
        ]

    @api.model
    def create(self, data_list):
        new_ids = super().create(data_list)
        for new_id in new_ids:
            if not new_id.name:
                new_id.name = self.env['ir.sequence'].next_by_code('hr.employee.code')
            new_id.employee_id.employee_file_code_id = new_id
            new_id._set_contract_loans_allocation()
        return new_ids
    
    def write(self, vals):
        pre_employee = self.env['hr.employee']
        if 'employee_id' in vals:
            if self.employee_id.id != vals['employee_id']:
                pre_employee = self.employee_id
        res = super().write(vals)
        if pre_employee and pre_employee != self.employee_id:
            pre_employee.employee_file_code_id = False
            self.employee_id.employee_file_code_id = self
            self._set_contract_loans_allocation(pre_employee)
        return res
    
    def valid_module_state(self, name):
        if name:
            module = self.env['ir.module.module'].search([('name', '=', name)])
            if module.state == 'installed':
                return True
    
    def _set_contract_loans_allocation(self, pre_employee=None):
        self = self.with_context(bypass=True)
        if pre_employee:
            pre_employee = pre_employee.with_context(bypass=True)
            pre_employee.contract_ids.employee_file_code_id = False
            if self.valid_module_state('omegasoft_hr_employee_advances_loans_discounts'):
                pre_employee.advances_loans_discounts_line_ids._constrains_employee()
                self.env['hr_employee_advances_loans_discounts'].search([('employee_ids', 'in', pre_employee.id)])._constrains_employee()
            if self.valid_module_state('omegasoft_contract_allocation'):
                self.env['contract_allocation_lines'].search([('employee_id', '=', pre_employee.id)])._constrains_employee()
                self.env['contract_allocation'].search([('employee_ids', 'in', self.employee_id.id)])._constrains_employee()

        self.employee_id.contract_ids.employee_file_code_id = self
        if self.valid_module_state('omegasoft_hr_employee_advances_loans_discounts'):
            self.employee_id.advances_loans_discounts_line_ids._constrains_employee()
            self.env['hr_employee_advances_loans_discounts'].search([('employee_ids', 'in', self.employee_id.id)])._constrains_employee()
        if self.valid_module_state('omegasoft_contract_allocation'):
            self.env['contract_allocation_lines'].search([('employee_id', '=', self.employee_id.id)])._constrains_employee()
            self.env['contract_allocation'].search([('employee_ids', 'in', self.employee_id.id)])._constrains_employee()

        self = self.with_context(bypass=False)
        