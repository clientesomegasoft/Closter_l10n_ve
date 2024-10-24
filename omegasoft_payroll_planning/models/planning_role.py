from odoo import api, fields, models


class PlanningRole(models.Model):
    _inherit = "planning.role"

    hr_job_id = fields.Many2one(
        comodel_name="hr.job", string="Workstation", ondelete="restrict"
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    jobs_with_roles = fields.Boolean(related="company_id.planning_workstation")

    @api.onchange("hr_job_id")
    def onchange_hr_job(self):
        employees_ids = []
        self.resource_ids = [(5, False, False)]
        self.name = self.hr_job_id.name if self.hr_job_id.name else " "
        if self.hr_job_id:
            employees = self.env["hr.employee"].search([])
            for record in employees:
                roles = list(
                    set(
                        [role.name for role in record.default_planning_role_id]
                        + [role.name for role in record.planning_role_ids]
                    )
                )
                if self.name in roles:
                    employees_ids.append(record.id)

            employees = self.env["hr.employee"].search([("id", "in", employees_ids)])
            for record in employees:
                self.write({"employee_ids": [(4, record.id)]})

            return {"domain": {"employee_ids": [("id", "in", employees_ids)]}}
