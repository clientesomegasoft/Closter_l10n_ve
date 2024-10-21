import calendar
from calendar import monthrange
from datetime import date, datetime

from dateutil.relativedelta import MO, relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression


class HrPayslip(models.Model):
    _inherit = "hr.payslip.run"

    struct_id = fields.Many2one("hr.payroll.structure", string="Structure")

    rate_id = fields.Many2one(
        "res.currency.rate",
        string="Rate",
        tracking=True,
        default=lambda self: self.env.company.currency_ref_id.rate_ids.filtered(
            lambda aml: aml.is_payroll_rate
        ).sorted("name")[-1],
        domain="[('currency_id', '=', currency_ref_id), ('is_payroll_rate', '=', True)]",
    )
    payroll_structure_for_rate = fields.Many2many(
        related="company_id.payroll_structure_for_rate"
    )
    structure_for_rate = fields.Boolean(default=False)
    rate_amount = fields.Float(string="Rate amount")
    company_currency = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.company.currency_id
    )

    number_of_mondays = fields.Float(
        string="Number of Mondays",
        help="Number of Mondays in the selected period.",
        default=0,
    )

    number_of_saturdays_sundays = fields.Float(
        string="Number of Saturdays and Sundays",
        help="Number of Saturdays and Sundays in the period selected ",
        default=0,
    )

    fortnight = fields.Selection(
        [
            ("first_fortnight", "First fortnight"),
            ("second_fortnight", "Second fortnight"),
        ],
        string="Fortnights",
        help="""Indicates whether the structure associated with
        the payroll is first or second fortnight""",
    )

    struct_fortnight = fields.Selection(related="struct_id.schedule_pay")
    week_number = fields.Integer("number of week", default=False)

    @api.onchange("struct_id")
    def _check_fields_structure_for_rate(self):
        self.structure_for_rate = (
            True if self.struct_id.id in self.payroll_structure_for_rate.ids else False
        )

    @api.onchange("rate_id")
    def _rate_onchange(self):
        if self.rate_id:
            self.rate_amount = self.rate_id.inverse_company_rate
        else:
            self.rate_amount = 0

    @api.onchange("name", "struct_id", "date_start", "date_end")
    def _onchange_number_of_week(self):
        if (
            self.date_end
            and self.date_start
            and self.struct_id
            and self.struct_id.schedule_pay == "weekly"
        ):
            self.week_number = (
                self.date_end.isocalendar()[1]
                if self.date_end.isocalendar()[1] == self.date_start.isocalendar()[1]
                and self.date_end > self.date_start
                else False
            )

    @api.onchange("week_number")
    def _onchange_date_week(self):
        if (
            self.date_end > self.date_start
            and self.struct_id
            and self.struct_id.schedule_pay == "weekly"
        ):
            self.date_start = datetime(1997, 1, 1) + relativedelta(
                weekday=MO(-1), weeks=int(self.week_number), year=self.date_start.year
            )
            self.date_end = self.date_start + relativedelta(days=6)

    @api.onchange("name", "date_start", "date_end")
    def _onchange_number_of_mondays_saturdays_sundays(self):
        if self.name:
            days = self._get_number_of_mondays_saturdays_sundays(
                self.date_start, self.date_end
            )
            self.number_of_mondays = days.get("number_of_mondays")
            self.number_of_saturdays_sundays = days.get("number_of_saturdays_sundays")

    def _get_number_of_mondays_saturdays_sundays(self, start_of_period, end_of_period):
        """
        Receives a date range (start_of_period and end_of_period)
        and calculates the number of Mondays, Saturdays and Sundays within the range.
        """

        number_of_mondays = 0
        number_of_saturdays_sundays = 0

        if start_of_period.month == end_of_period.month:
            # The start and end of the payroll period are in the same month.
            num_days = monthrange(start_of_period.year, start_of_period.month)
            for dia in range(start_of_period.day, end_of_period.day + 1):
                if (
                    datetime(start_of_period.year, start_of_period.month, dia).weekday()
                    == 0
                ):
                    number_of_mondays += 1
                if datetime(
                    start_of_period.year, start_of_period.month, dia
                ).weekday() in [5, 6]:
                    number_of_saturdays_sundays += 1

                if dia == 30 and num_days[1] > 30 and end_of_period.day == 30:
                    if (
                        datetime(
                            start_of_period.year, start_of_period.month, 31
                        ).weekday()
                        == 0
                    ):
                        number_of_mondays += 1

        elif end_of_period.month > start_of_period.month:
            # The payroll start and end periods have different months.

            day_month = calendar.monthrange(
                start_of_period.year, start_of_period.month
            )[1]

            for dia in range(start_of_period.day, day_month + 1):
                if (
                    datetime(start_of_period.year, start_of_period.month, dia).weekday()
                    == 0
                ):
                    number_of_mondays += 1
                if datetime(
                    start_of_period.year, start_of_period.month, dia
                ).weekday() in [5, 6]:
                    number_of_saturdays_sundays += 1

            for dia in range(1, end_of_period.day + 1):
                if (
                    datetime(end_of_period.year, end_of_period.month, dia).weekday()
                    == 0
                ):
                    number_of_mondays += 1
                if datetime(end_of_period.year, end_of_period.month, dia).weekday() in [
                    5,
                    6,
                ]:
                    number_of_saturdays_sundays += 1

        return {
            "number_of_mondays": number_of_mondays,
            "number_of_saturdays_sundays": number_of_saturdays_sundays,
        }

    @api.onchange("struct_id", "fortnight")
    def _onchange_fortnight(self):
        today = fields.Date.today()

        for record in self:
            if record.struct_id and record.struct_id.schedule_pay != "bi-weekly":
                record.date_start = date(today.year, today.month, 1)
                record.date_end = fields.Date.to_string(
                    (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()
                )
                if record.fortnight:
                    record.fortnight = False
            elif record.fortnight:
                if record.fortnight == "first_fortnight":
                    record.date_start = date(today.year, today.month, 1)
                    record.date_end = date(today.year, today.month, 15)
                elif record.fortnight == "second_fortnight":
                    record.date_start = date(today.year, today.month, 16)
                    record.date_end = fields.Date.to_string(
                        (
                            datetime.now() + relativedelta(months=+1, day=1, days=-1)
                        ).date()
                    )
                    if record.date_end.day == 31:
                        record.date_end = record.date_end + relativedelta(days=-1)

    def _get_available_contracts_domain(self):
        return [
            ("contract_ids.state", "=", ("open")),
            ("company_id", "=", self.env.company.id),
        ]

    def _compute_employee_ids(self):  # noqa: C901
        new_payroll_ids = self.env["hr.employee"]
        domain = self._get_available_contracts_domain()
        added_record_ids = set()
        employee_ids = self.env["hr.employee"].search(domain)
        if (
            self.struct_id.is_bonus
            or self.struct_id.complementary_payroll
            or self.struct_id.is_perfect_attendance
            or self.struct_id.is_mobility_bonus_applies
            or self.struct_id.is_night_bonus
            or self.struct_id.is_productivity_bonus_applies
            or self.struct_id.is_special_bonus
            or self.struct_id.is_seniority_bonus_applies
        ):
            if self.struct_id.is_bonus:
                for record in employee_ids:
                    if record.bonus_line_ids and record.bonus_line_ids.filtered(
                        lambda x: x.bonus_id.state == "assigned"
                        and x.bonus_id.date >= self.date_start
                        and x.bonus_id.date <= self.date_end
                    ):
                        if record.id not in added_record_ids:
                            new_payroll_ids += record
                            added_record_ids.add(record.id)

            if self.struct_id.complementary_payroll:
                for record in employee_ids:
                    if (
                        record.contract_id.complementary_bonus_check
                        and record.contract_id.complementary_bonus > 0
                    ):
                        if record.id not in added_record_ids:
                            new_payroll_ids += record
                            added_record_ids.add(record.id)

            if self.struct_id.is_perfect_attendance:
                for record in employee_ids:
                    if (
                        record.contract_id.perfect_attendance_bonus_check
                        and record.contract_id.perfect_attendance_bonus > 0
                    ):
                        if record.id not in added_record_ids:
                            new_payroll_ids += record
                            added_record_ids.add(record.id)

            if self.struct_id.is_mobility_bonus_applies:
                for record in employee_ids:
                    if (
                        record.contract_id.mobility_bonus_applies
                        and record.contract_id.mobility_bonus_amount > 0
                    ):
                        if record.id not in added_record_ids:
                            new_payroll_ids += record
                            added_record_ids.add(record.id)

            if self.struct_id.is_night_bonus:
                for record in employee_ids:
                    if (
                        record.contract_id.night_bonus
                        and record.contract_id.night_bonus_amount > 0
                    ):
                        if record.id not in added_record_ids:
                            new_payroll_ids += record
                            added_record_ids.add(record.id)

            if self.struct_id.is_productivity_bonus_applies:
                for record in employee_ids:
                    if (
                        record.contract_id.productivity_bonus_applies
                        and record.contract_id.productivity_bonus_amount > 0
                    ):
                        if record.id not in added_record_ids:
                            new_payroll_ids += record
                            added_record_ids.add(record.id)

            if self.struct_id.is_special_bonus:
                for record in employee_ids:
                    if (
                        record.contract_id.special_bonus_applies
                        and record.contract_id.special_bonus_amount > 0
                    ):
                        if record.id not in added_record_ids:
                            new_payroll_ids += record
                            added_record_ids.add(record.id)

            if self.struct_id.is_seniority_bonus_applies:
                for record in employee_ids:
                    if (
                        record.contract_id.seniority_bonus_applies
                        and record.contract_id.seniority_bonus_amount > 0
                    ):
                        if record.id not in added_record_ids:
                            new_payroll_ids += record
                            added_record_ids.add(record.id)
            added_record_ids.clear()
            return new_payroll_ids

        else:
            for record in self:
                department = False
                if record.struct_id:
                    department = record.struct_id.department_ids.ids

                domain = expression.AND(
                    [domain, [("department_id", "child_of", department)]]
                )
            return self.env["hr.employee"].search(domain)

    def contex_payslip_by_employee(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.payslip.employees",
            "target": "new",
            "view_id": self.env.ref("hr_payroll.view_hr_payslip_by_employees").id,
            "view_mode": "form",
            "context": {
                "default_structure_id": self.struct_id.id,
                "default_fortnight": self.fortnight,
                "default_employee_ids": self._compute_employee_ids().ids,
                "default_week_number": self.week_number,
            },
        }

    def action_draft(self):
        self.valid_state_payslib()
        for record in self.slip_ids:
            if record.state in ["done", "paid"]:
                record.action_payslip_cancel()
        res = super(__class__, self).action_draft()
        return res

    def valid_state_payslib(self):
        for record in self.slip_ids:
            if record.move_id.state in ["posted"]:
                name = record.name
                raise UserError(
                    _(
                        "No se puede llevar a borrador una nomina "
                        "con asientos publicados: \n"
                        "%(name)s",
                        name=name,
                    )
                )
