from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HRLeaveType(models.Model):
    _inherit = "hr.leave.type"

    is_plan_vacation = fields.Boolean(string="is plan vacation", default=False)
    is_plan_enjoy = fields.Boolean(string="is plan enjoy", default=False)

    @api.constrains("is_plan_vacation", "is_plan_enjoy")
    def _check_vacation_enjony(self):
        types_leave_vacation = self.env["hr.leave.type"].search(
            [
                "|",
                ("active", "=", True),
                ("active", "=", False),
                ("is_plan_vacation", "=", True),
            ]
        )
        types_leave_enjoy = self.env["hr.leave.type"].search(
            [
                "|",
                ("active", "=", True),
                ("active", "=", False),
                ("is_plan_enjoy", "=", True),
            ]
        )
        if len(types_leave_vacation) > 1:
            raise UserError(
                _(
                    "There can only be one type of absence with the is_plan_vacation check active, including in archived records"
                )
            )
        if len(types_leave_enjoy) > 1:
            raise UserError(
                _(
                    "There can only be one type of absence with the is_plan_enjoy check active, including in archived records"
                )
            )
