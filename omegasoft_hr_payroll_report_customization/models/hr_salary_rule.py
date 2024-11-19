from odoo import models


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    def name_get(self):
        if self.env.context.get("show_code_for_salary_rule"):
            return [(record.id, f"[{record.code}] {record.name}") for record in self]
        else:
            return super(__class__, self).name_get()
