from odoo import fields, models


class PlanningTemplate(models.Model):
    _inherit = "planning.slot.template"

    employee_crew_id = fields.Many2one(
        "hr.employee.crew", string="Employee Crew", ondelete="restrict"
    )
