from odoo import fields, models


# Removes the computed behavior defined in the module omegasoft_employee_arc
class ResCompany(models.Model):
    _inherit = "res.company"

    salary_rules_categories_extras = fields.Many2many(
        "hr.salary.rule.category",
        relation="res_company_hr_salary_rule_category_extras",
        string="Extra categories for payslip reports",
    )

    salary_rules_extras = fields.Many2many(
        "hr.salary.rule",
        relation="res_company_hr_salary_rule_extras",
        string="Extra salary rules for payslip reports",
        readonly=False,
    )
