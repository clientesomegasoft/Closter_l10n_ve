# -*- coding: utf-8 -*-

from odoo import models, fields

# Removes the computed behavior defined in the module omegasoft_employee_arc 
class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    salary_rules_categories_extras = fields.Many2many(
        'hr.salary.rule.category',
        relation = 'res_company_hr_salary_rule_category_extras',
        related  = 'company_id.salary_rules_categories_extras',
        string   = 'Extra categories for payslip reports',
        readonly = False)

    salary_rules_extras = fields.Many2many(
        'hr.salary.rule',
        relation = 'res_company_hr_salary_rule_extras',
        related  = 'company_id.salary_rules_extras',
        domain   = "[('category_id', 'in', salary_rules_categories_extras)]",
        string   = 'Extra salary rules for payslip reports',
        readonly = False)
