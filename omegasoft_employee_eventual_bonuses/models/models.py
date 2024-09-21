from odoo import fields, models


class HrEmployeeInherit(models.Model):
    _inherit = "hr.employee"

    bonus_line_ids = fields.One2many(
        string="bonus lines",
        comodel_name="hr_employee_bonus_line",
        inverse_name="employee_id",
    )
