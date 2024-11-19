from odoo import fields, models


class HrEmployeeDisability(models.Model):
    _name = "hr_employee_disability"
    _description = "Employees disability"

    name = fields.Char(string="Disability")
    company_id = fields.Many2one(
        comodel_name="res.company",
        ondelete="restrict",
        string="Company",
        default=lambda self: self.env.company,
    )
