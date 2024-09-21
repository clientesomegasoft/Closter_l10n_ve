from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    history_ids = fields.One2many(
        "hr_plan_accumulation.history",
        "employee_id",
        string="Accumulated",
        domain=[
            ("state", "in", ["draft", "confirm", "refuse", "validate1", "validate"])
        ],
    )
