from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrLeave(models.Model):
    _inherit = "hr.leave"

    history_ids = fields.One2many(
        comodel_name="hr_plan_accumulation.history",
        inverse_name="leave_id",
        string="History",
        readonly=False,
        states={
            "confirm": [("readonly", True)],
            "refuse": [("readonly", True)],
            "validate": [("readonly", True)],
            "vaidate1": [("readonly", True)],
        },
    )
    is_plan_vacation = fields.Boolean(related="holiday_status_id.is_plan_vacation")
    is_plan_enjoy = fields.Boolean(related="holiday_status_id.is_plan_enjoy")
    state = fields.Selection(default="draft")
    liquidate = fields.Boolean(string="Liquidate", default=False)

    @api.onchange(
        "holiday_type",
        "employee_ids",
        "holiday_status_id",
        "department_id",
        "mode_company_id",
        "category_id",
    )
    def _search_accumulated(self):
        if (self.is_plan_vacation or self.is_plan_enjoy) and self.holiday_status_id:
            employees = self._holiday_type_search_employee()

            if employees:
                self.history_ids = [fields.Command.clear()]
                for employee in employees:
                    accumulated_id = (
                        self.env["hr_plan_accumulation"]
                        .sudo()
                        .search([("employee_id", "=", employee._origin.id)])
                    )
                    if accumulated_id:
                        if self.is_plan_vacation:
                            lines = accumulated_id.vacation_ids
                        elif self.is_plan_enjoy:
                            lines = accumulated_id.enjoy_ids

                        for line in lines:
                            # Condición para verificar si todos los campos son mayores a cero
                            if (
                                line.days_law > 0
                                or line.vacation_bonus > 0
                                or line.additional_days > 0
                            ):
                                self.history_ids.create(
                                    {
                                        "employee_id": employee._origin.id,
                                        "leave_id": self.id,
                                        "period": line.period,
                                        "days_law": line.days_law,
                                        "vacation_bonus": line.vacation_bonus,
                                        "additional_days": line.additional_days,
                                        "time_off_type_id": self.holiday_status_id.id,
                                    }
                                )

    def action_confirm(self):
        for leave in self:
            if leave.is_plan_vacation or leave.is_plan_enjoy:
                for history_line in leave.history_ids:
                    accumulated_id = (
                        leave.env["hr_plan_accumulation"]
                        .sudo()
                        .search(
                            [("employee_id", "=", history_line.employee_id.id)], limit=1
                        )
                    )

                    if accumulated_id:
                        line = None

                        if leave.is_plan_vacation:
                            line = accumulated_id.vacation_ids.filtered(
                                lambda x: x.period.year == history_line.period.year
                            )
                        elif leave.is_plan_enjoy:
                            line = accumulated_id.enjoy_ids.filtered(
                                lambda x: x.period.year == history_line.period.year
                            )

                        if line:
                            days_law = line.days_law - history_line.days_law
                            vacation_bonus = (
                                line.vacation_bonus - history_line.vacation_bonus
                            )
                            additional_days = (
                                line.additional_days - history_line.additional_days
                            )

                            if (
                                days_law >= 0
                                and vacation_bonus >= 0
                                and additional_days >= 0
                            ):
                                line.write(
                                    {
                                        "days_law": days_law,
                                        "vacation_bonus": vacation_bonus,
                                        "additional_days": additional_days,
                                    }
                                )
                            else:
                                raise UserError(
                                    _(
                                        "Error: The legal days, vacation days, and additional days cannot be less than zero"
                                    )
                                )

        return super(HrLeave, self).action_confirm()

    def action_refuse(self):
        for leave in self:
            if leave.is_plan_vacation or leave.is_plan_enjoy:
                for history_line in leave.history_ids:
                    accumulated_id = (
                        leave.env["hr_plan_accumulation"]
                        .sudo()
                        .search(
                            [("employee_id", "=", history_line.employee_id.id)], limit=1
                        )
                    )

                    if accumulated_id:
                        line = None

                        if leave.is_plan_vacation:
                            line = accumulated_id.vacation_ids.filtered(
                                lambda x: x.period.year == history_line.period.year
                            )
                        elif leave.is_plan_enjoy:
                            line = accumulated_id.enjoy_ids.filtered(
                                lambda x: x.period.year == history_line.period.year
                            )

                        if line:
                            line.write(
                                {
                                    "days_law": (line.days_law + history_line.days_law),
                                    "vacation_bonus": (
                                        line.vacation_bonus
                                        + history_line.vacation_bonus
                                    ),
                                    "additional_days": (
                                        line.additional_days
                                        + history_line.additional_days
                                    ),
                                }
                            )

        return super(HrLeave, self).action_refuse()

    def _holiday_type_search_employee(self):
        employees = self.env["hr.employee"]
        if self.is_plan_vacation or self.is_plan_enjoy and self.holiday_status_id:
            if self.holiday_type == "employee":
                employees = self.employee_ids
            elif self.holiday_type == "category":
                employees = self.category_id.employee_ids
            elif self.holiday_type == "department":
                employees = self.department_id.member_ids
            else:
                employees = self.env["hr.employee"].search(
                    [("company_id", "=", self.mode_company_id.id)]
                )
        return employees

    def unlink(self):
        self.history_ids.unlink()
        return super(HrLeave, self).unlink()

    @api.constrains("employee_ids")
    def _check_history_ids(self):
        for record in self:
            if record.is_plan_vacation or record.is_plan_enjoy:
                if not record.history_ids:
                    raise UserError(
                        _(
                            "This type of absence cannot be generated without their respective lines"
                        )
                    )

    @api.constrains("request_date_from", "request_date_to", "liquidate")
    def _valid_number_day(self):
        if (
            not self.liquidate
            and self.leave_type_request_unit == "day"
            and (self.is_plan_vacation or self.is_plan_enjoy)
        ):
            days = 0
            for record in self.history_ids:
                days += record.days_law + record.additional_days
            if self.number_of_days_display != days:
                raise UserError(
                    _(
                        "The number of days to be deducted does not match the number of days of the permission"
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get("parent_id") and "history_ids" not in values:
                leave_parent = self.env["hr.leave"].search(
                    [("id", "=", values.get("parent_id"))]
                )
                if (
                    leave_parent.holiday_status_id.is_plan_vacation
                    or leave_parent.holiday_status_id.is_plan_enjoy
                ):
                    # Obtén las líneas de historial filtradas para el empleado en particular
                    history_lines = leave_parent.history_ids.filtered(
                        lambda x: x.employee_id.id == values.get("employee_id")
                    )

                    # Asigna la lista de identificadores a 'history_ids' en el valor
                    values["history_ids"] = [(4, line.id) for line in history_lines]

        holidays = super(
            HrLeave, self.with_context(mail_create_nosubscribe=True)
        ).create(vals_list)

        for holiday in holidays:
            if not self._context.get("leave_fast_create"):
                leave_types = self.env["hr.leave.type"].browse(
                    [
                        values.get("holiday_status_id")
                        for values in vals_list
                        if values.get("holiday_status_id")
                    ]
                )
                if leave_types.is_plan_vacation or leave_types.is_plan_enjoy:
                    mapped_validation_type = {
                        leave_type.id: leave_type.leave_validation_type
                        for leave_type in leave_types
                    }
                    for values in vals_list:
                        employee_id = values.get("employee_id", False)
                        leave_type_id = values.get("holiday_status_id")

                        # Establecer el estado en "borrador"
                        if mapped_validation_type[leave_type_id] == "no_validation":
                            holiday.state = "draft"

        return holidays
