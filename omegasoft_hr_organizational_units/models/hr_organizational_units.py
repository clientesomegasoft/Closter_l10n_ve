from odoo import api, fields, models


class HrOrganizatioanlUnits(models.Model):
    _name = "hr.organizational.units"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _description = "Hr Organizational Units"

    # OU master
    name = fields.Char()
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        index=True,
        default=lambda self: self.env.company,
    )
    manager_id = fields.Many2one(
        "hr.employee",
        string="Manager",
        tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    active = fields.Boolean("Active", default=True)
    department_id = fields.Many2one(
        "hr.department",
        "Department",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    jobs_ids = fields.Many2many(
        "hr.job", string="Jobs", domain="[('company_id', '=', company_id)]"
    )
    active_organizational_units = fields.Boolean(
        string="active organizational units",
        related="company_id.active_organizational_units",
    )

    # check template
    appraisals_to_process_count = fields.Integer(
        compute="_compute_appraisals_to_process", string="Appraisals to Process"
    )
    employee_feedback_template = fields.Html(
        compute="_compute_appraisal_feedbacks", store=True, readonly=False
    )
    manager_feedback_template = fields.Html(
        compute="_compute_appraisal_feedbacks", store=True, readonly=False
    )
    custom_appraisal_templates = fields.Boolean(
        string="Custom Appraisal Templates", default=False
    )

    def _compute_appraisals_to_process(self):
        appraisals = self.env["hr.appraisal"].read_group(
            [
                ("organizational_units_id", "in", self.ids),
                ("state", "in", ["new", "pending"]),
            ],
            ["organizational_units_id"],
            ["organizational_units_id"],
        )
        result = dict(
            (data["organizational_units_id"][0], data["organizational_units_id_count"])
            for data in appraisals
        )
        for units in self:
            units.appraisals_to_process_count = result.get(units.id, 0)

    @api.depends("company_id")
    def _compute_appraisal_feedbacks(self):
        for units in self:
            units.employee_feedback_template = (
                units.company_id.appraisal_employee_feedback_template
                or self.env.company.appraisal_employee_feedback_template
            )
            units.manager_feedback_template = (
                units.company_id.appraisal_manager_feedback_template
                or self.env.company.appraisal_manager_feedback_template
            )

    # (Booton)plan action by organizational unit

    plan_ids = fields.One2many("hr.plan", "organizational_units_id")
    plans_count = fields.Integer(compute="_compute_plan_count")

    def _compute_plan_count(self):
        plans_data = self.env["hr.plan"]._read_group(
            [("organizational_units_id", "in", self.ids)],
            ["organizational_units_id"],
            ["organizational_units_id"],
        )
        plans_count = {
            x["organizational_units_id"][0]: x["organizational_units_id_count"]
            for x in plans_data
        }
        for unit in self:
            unit.plans_count = plans_count.get(unit.id, 0)

    def action_plan_from_organizational_units(self):
        action = self.env["ir.actions.actions"]._for_xml_id("hr.hr_plan_action")
        action["context"] = {
            "default_organizational_units_id": self.id,
            "search_default_organizational_units_id": self.id,
        }
        action["domain"] = [("organizational_units_id", "=", self.id)]
        return action

    # (Booton) Employee
    total_employee = fields.Integer(
        compute="_compute_total_employee", string="Total Employee"
    )
    member_ids = fields.One2many(
        "hr.employee", "organizational_units_id", string="Members", readonly=True
    )

    def _compute_total_employee(self):
        emp_data = self.env["hr.employee"]._read_group(
            [("organizational_units_id", "in", self.ids)],
            ["organizational_units_id"],
            ["organizational_units_id"],
        )
        result = dict(
            (data["organizational_units_id"][0], data["organizational_units_id_count"])
            for data in emp_data
        )
        for units in self:
            units.total_employee = result.get(units.id, 0)

    def act_employee_from_hr_organizational_units(self):
        #     action = self.env['ir.actions.actions']._for_xml_id('hr.view_act_employee_from_hr_organizational_units')
        #     action['context'] = {'default_organizational_units_id': self.id, 'search_default_organizational_units_id': self.id}
        #     action['domain'] = [('organizational_units_id', '=', self.id)]
        #     return action
        return {
            "type": "ir.actions.act_window",
            "name": "employee",
            "view_mode": "tree",
            "res_model": "hr.employee",
            "domain": [("organizational_units_id", "=", self.id)],
            "context": "{'create': True}",
        }
