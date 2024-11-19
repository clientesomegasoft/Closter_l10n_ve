from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    family_information_ids = fields.One2many(
        comodel_name="hr_employee_family_information",
        inverse_name="employee_id",
        string="Famyli informarion",
    )
