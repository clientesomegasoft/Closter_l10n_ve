from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrPlanAccumulationEnjoy(models.Model):
    _name = "hr_plan_accumulation.enjoy"
    _description = "Lines Absence Enjoy Plan"
    _order = "period asc"

    accumulated_id = fields.Many2one("hr_plan_accumulation", string="Vacations")
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
    year_period = fields.Char(
        "year of period", compute="_compute_year_period", store=True
    )

    # El periodo deberia ser unico o en efecto el año
    _sql_constraints = [
        (
            "period_unique",
            "unique (year_period, accumulated_id)",
            "The period must be unique per year!",
        ),
    ]

    @api.depends("period")
    def _compute_year_period(self):
        for record in self:
            record.year_period = record.period.year

    @api.model_create_multi
    def create(self, vals_list):
        leave_type_enjoy = self.env["hr.leave.type"].search(
            [("is_plan_enjoy", "=", True)],
            limit=1,
        )
        if not leave_type_enjoy:
            raise UserError(
                _(
                    "You must indicate in the types of absence, an absence of vacations and one of enjoyment"
                )
            )
        for vals in vals_list:
            if "time_off_type_id" not in vals and not vals.get("time_off_type_id"):
                vals["time_off_type_id"] = leave_type_enjoy.id
        return super(HrPlanAccumulationEnjoy, self).create(vals_list)
