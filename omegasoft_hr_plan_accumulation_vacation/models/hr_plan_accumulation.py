from dateutil import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrPlanAccumulation(models.Model):
    _name = "hr_plan_accumulation"
    _description = "accumulation plan"
    _inherit = ["mail.thread", "mail.activity.mixin", "image.mixin"]

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        help="Company employees with contracts in Process",
        tracking=True,
    )
    name = fields.Char(
        string="Employee Name",
        related="employee_id.name",
        store=True,
        readonly=False,
        tracking=True,
    )
    last_calculation = fields.Date(
        string="last calculation",
        default=False,
        readonly=True,
        help="It refers to the year to which the vacation days belong, Field will be increased automatically by the planned action.",
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        ondelete="restrict",
        string="Company",
        default=lambda self: self.env.company,
        tracking=True,
        readonly=True,
    )
    active = fields.Boolean(
        default=True,
        help="Set active to false to hide the children tag without removing it.",
    )
    # Line accumulated vacationes
    vacation_ids = fields.One2many(
        "hr_plan_accumulation.vacation", "accumulated_id", string="Vacation"
    )
    # Line accumulated absence enjoy
    enjoy_ids = fields.One2many(
        "hr_plan_accumulation.enjoy", "accumulated_id", string="Enjoy"
    )

    _sql_constraints = [
        (
            "Employee_unique",
            "unique (employee_id, company_id)",
            "The employee must be unique per company!",
        ),
    ]

    # employee file code

    employee_file = fields.Boolean("Employee file", related="company_id.employee_file")
    employee_file_code_id = fields.Many2one(
        "employee.file.code", string="Employee File", tracking=True
    )

    @api.onchange("employee_file_code_id")
    def _onchange_employee_file_code_id(self):
        if self.employee_file:
            if (
                self.employee_file_code_id
                and self.employee_file_code_id != self.employee_id.employee_file_code_id
            ):
                self.employee_id = self.employee_file_code_id.employee_id
            elif not self.employee_file_code_id and self.employee_id:
                self.employee_id = False

    @api.onchange("employee_id")
    def _onchange_employee(self):
        if self.employee_file:
            if (
                self.employee_id
                and self.employee_file_code_id != self.employee_id.employee_file_code_id
            ):
                self.employee_file_code_id = self.employee_id.employee_file_code_id
            elif not self.employee_id and self.employee_file_code_id:
                self.employee_file_code_id = False

    @api.constrains("employee_file_code_id")
    def _constrains_employee_file_code_id(self):
        if self.employee_file:
            if not self._context.get("bypass", False):
                if (
                    self.employee_file_code_id
                    and self.employee_file_code_id
                    != self.employee_id.employee_file_code_id
                ):
                    self.employee_id = self.employee_file_code_id.employee_id
                elif not self.employee_file_code_id and self.employee_id:
                    self.employee_id = False

    @api.constrains("employee_id")
    def _constrains_employee(self):
        if self.employee_file:
            if (
                self.employee_id
                and self.employee_file_code_id != self.employee_id.employee_file_code_id
            ):
                self.employee_file_code_id = self.employee_id.employee_file_code_id
            elif not self.employee_id and self.employee_file_code_id:
                self.employee_file_code_id = False

    # employee file code

    def _accumulated_vacation(self):
        employee_ids = (
            self.env["hr.employee"]
            .search([("active", "=", True)])
            .filtered(
                lambda self: self.contract_id.state == "open"
                and self.contracts_count >= 1
            )
        )
        today = fields.Date.from_string(fields.Date.today())
        leave_type_vacation = self.env["hr.leave.type"].search(
            [("is_plan_vacation", "=", True)],
            limit=1,
        )

        if not leave_type_vacation:
            raise UserError(
                _(
                    "You must indicate in the types of absence, an absence of vacations and one of enjoyment"
                )
            )

        for employee in employee_ids:
            accumulation_id = self.env["hr_plan_accumulation"].search(
                [("employee_id", "=", employee.id)]
            )
            create_vals = []
            current_contract = (
                employee.contract_id if employee.contract_id.state == "open" else False
            )
            if current_contract:
                # the vacation accumulation plan must be created for the employee
                if not accumulation_id:
                    create_vals.append(
                        {
                            "employee_id": employee.id,
                            "employee_file_code_id": employee.employee_file_code_id.id,
                        }
                    )
                    accumulation_id = self.create(create_vals)

                # It does not have the last date of the last calculation, so it will be your first calculation.
                if accumulation_id.last_calculation:
                    diff_date = relativedelta.relativedelta(
                        today, accumulation_id.last_calculation
                    )
                else:
                    diff_date = relativedelta.relativedelta(
                        today, current_contract.date_start
                    )

                if diff_date.years >= 1 or diff_date.months >= 10:
                    accumulation_id.last_calculation = today
                    additional_days = accumulation_id._get_additional_days(
                        current_contract
                    )
                    accumulation_id.vacation_ids.create(
                        {
                            "accumulated_id": accumulation_id.id,
                            "period": today,
                            "days_law": 15,
                            "vacation_bonus": 15 + additional_days,
                            "additional_days": additional_days,
                            "time_off_type_id": leave_type_vacation.id,
                        }
                    )

    def _get_additional_days(self, contact):
        if contact.years_of_seniority >= 2:
            return (
                (contact.years_of_seniority - 1)
                if contact.years_of_seniority <= 15
                else 15
            )
        else:
            return 0

    def unlink(self):
        self.vacation_ids.unlink()
        self.enjoy_ids.unlink()
        return super(HrPlanAccumulation, self).unlink()
