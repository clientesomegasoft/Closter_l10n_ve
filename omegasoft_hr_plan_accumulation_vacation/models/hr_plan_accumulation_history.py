from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrPlanAccumulationHistory(models.Model):
    _name = "hr_plan_accumulation.history"
    _description = "registration lines for what was consumed in the vacation plan and in the enjoyment plan"
    _order = "period asc"

    leave_id = fields.Many2one("hr.leave", string="Record")
    employee_ids = fields.Many2many(related="leave_id.employee_ids")  # per filter line
    request_date_from = fields.Date(
        "Request Start Date", related="leave_id.request_date_from"
    )
    request_date_to = fields.Date(
        "Request End Date", related="leave_id.request_date_to"
    )
    state = fields.Selection(related="leave_id.state")
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        help="Company employees with contracts in Process",
        tracking=True,
    )
    period = fields.Date(
        string="Period",
        required=True,
        help="It refers to the year to which the vacation days belong, Field will be increased automatically by the planned action.",
    )
    days_law = fields.Float(
        string="Day Law",
        help="It refers to the 15 fixed legal days that are increased by the planned action or by adding lines.",
    )
    vacation_bonus = fields.Float(
        string="Vacation bonus",
        help="It refers to the fixed 15-day Vacation Bonus that is increased by the planned action or by adding lines.",
    )
    additional_days = fields.Float(
        string="Additional Days",
        help="This calculation of the field of additional days depends on the seniority in years, it is one day for each year of services from the second year with a cap of 15 days",
    )
    time_off_type_id = fields.Many2one(
        "hr.leave.type",
        string="Time Off Type",
        readonly=True,
        help="""It is the absence that will be used to create, update and recalculate the accumulated vacation plan for all fields.""",
    )

    @api.onchange("period", "employee_id")
    def _onchange_search_period(self):
        if self.employee_id and self.period:
            accumulated_id = (
                self.env["hr_plan_accumulation"]
                .sudo()
                .search([("employee_id", "=", self.employee_id.id)])
            )
            if self.leave_id.is_plan_vacation:
                line = (
                    self.env["hr_plan_accumulation.vacation"]
                    .search([("accumulated_id", "=", accumulated_id.id)])
                    .filtered(lambda x: x.period.year == self.period.year)
                )
            elif self.leave_id.is_plan_enjoy:
                line = (
                    self.env["hr_plan_accumulation.enjoy"]
                    .search([("accumulated_id", "=", accumulated_id.id)])
                    .filtered(lambda x: x.period.year == self.period.year)
                )

            if line:
                self.period = line.period
                self.days_law = line.days_law
                self.vacation_bonus = line.vacation_bonus
                self.additional_days = line.additional_days
                self.time_off_type_id = (line.time_off_type_id.id,)
            else:
                raise ValidationError(
                    _("Do not have vacations for the selected period")
                )

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if "leave_id" in values and "time_off_type_id" not in values:
                leave = self.env["hr.leave"].browse(values["leave_id"])
                values["time_off_type_id"] = leave.holiday_status_id.id
        return super(HrPlanAccumulationHistory, self).create(vals_list)
