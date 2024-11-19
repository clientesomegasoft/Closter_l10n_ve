from odoo import models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def _get_categories_extras(self):
        return (
            self.company_id.salary_rules_categories_extras.mapped("code")
            if self.company_id.salary_rules_categories_extras
            else []
        )

    def _get_rules_extras(self):
        return (
            self.company_id.salary_rules_extras.mapped("code")
            if self.company_id.salary_rules_extras
            else []
        )
