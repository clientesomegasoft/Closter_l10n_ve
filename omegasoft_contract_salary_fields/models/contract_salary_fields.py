from dateutil.relativedelta import MO, relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ContractSalaryField(models.Model):
    _inherit = "hr.contract"

    custom_contract_currency = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.company.currency_id
    )
    custom_wage_currency = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.company.currency_id
    )
    custom_hourly_wage_currency = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.company.currency_id
    )

    cestaticket_salary = fields.Monetary(
        string="Salary Cestaticket",
        help="Monthly food benefit",
        currency_field="cestaticket_salary_currency",
        tracking=True,
    )
    cestaticket_salary_currency = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.company.currency_id
    )

    average_wage = fields.Monetary(
        string="Average wage",
        help="The average amount of money received by a worker in a given period",
        currency_field="average_wage_currency",
        tracking=True,
        compute="_compute_average_wage",
        store=True,
    )
    average_wage_currency = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.company.currency_id
    )
    is_average_wage = fields.Boolean("boolean the average", default=False)

    average_wage_date_start = fields.Date(
        string="Date start", help="Starting date from average wage"
    )

    average_wage_date_end = fields.Date(
        string="Date end", help="End date up to average wage"
    )

    salary_overtime_hours = fields.Monetary(
        string="Overtime hours",
        help="""These are the hours of work that are performed on a voluntary
        basis, over the maximum duration of the ordinary working day.""",
        currency_field="salary_overtime_hours_currency",
        tracking=True,
    )
    salary_overtime_hours_currency = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.company.currency_id
    )

    @api.constrains(
        "cestaticket_salary",
        "average_wage",
        "wage",
        "hourly_wage",
        "salary_overtime_hours",
    )
    def _constrains_field_salary(self):
        for record in self:
            if record.wage_type == "hourly" and record.hourly_wage <= 0:
                raise ValidationError(
                    _("El monto del Salario no puede ser menor o igual a cero")
                )
            elif record.wage_type == "monthly" and record.wage <= 0:
                raise ValidationError(
                    _("El monto del Salario no puede ser menor o igual a cero")
                )

            if record.cestaticket_salary <= 0:
                raise ValidationError(
                    _("El monto del Salario Cesta Ticke no puede ser menor o igual a cero")
                )
            if (
                record.average_wage_date_start
                and record.average_wage_date_end
                and record.average_wage < 0
            ):
                raise ValidationError(
                    _("El monto del Salario Promedio no puede ser "
                    "menor a cero si existen fechas de inicio y fin")
                )
            if record.salary_overtime_hours < 0:
                raise ValidationError(_("Las Horas Extras deben ser superiores a cero."))

    def _net_amount(self, payslip_obj, to_currency, average_salary=False):
        # neto = 0
        struct_type = False
        rule_category_code = False
        neto = 0

        struct_type = self.env["average_wage_lines"].search(
            [("payroll_structure_type", "=", self.structure_type_id.id)], limit=1
        )

        if payslip_obj and struct_type:
            rule_category_code = struct_type.salary_rule_category.mapped("code")
            if not struct_type.best_weeks_check:
                for payslip in payslip_obj:
                    currency_id = (
                        payslip.currency_id
                        if not average_salary
                        else self.average_wage_currency
                    )
                    neto += sum(
                        currency_id._convert(
                            total.total,
                            to_currency,
                            payslip.company_id,
                            fields.Date.today(),
                        )
                        for total in payslip.line_ids.filtered(
                            lambda x: x.category_id.code in rule_category_code
                        )
                    )
            else:
                neto = {}
                for payslip in payslip_obj:
                    currency_id = (
                        payslip.currency_id
                        if not average_salary
                        else self.average_wage_currency
                    )
                    neto[payslip.id] = sum(
                        currency_id._convert(
                            total.total,
                            to_currency,
                            payslip.company_id,
                            fields.Date.today(),
                        )
                        for total in payslip.line_ids.filtered(
                            lambda x: x.category_id.code in rule_category_code
                        )
                    )

        return {
            "neto": neto,
            "struct_type": struct_type,
            "average_days": struct_type.average_days,
        }

    @api.onchange("average_wage_date_start")
    def _onchange_average_wage_date_start(self):
        if self.wage_type == "hourly" and self.average_wage_date_start:
            self.average_wage_date_start = self.average_wage_date_start + relativedelta(
                weekday=MO(-1)
            )

    @api.depends(
        "average_wage_date_start", "average_wage_date_end", "average_wage_currency"
    )
    def _compute_average_wage(self):
        for record in self:
            average_wage = 0

            if record.average_wage_date_start and record.average_wage_date_end:
                if record.average_wage_date_start > record.average_wage_date_end:
                    raise ValidationError(
                        _("La fecha de inicio no puede ser mayor a la fecha fin")
                    )

                payslip_obj = self.env["hr.payslip"].search(
                    [
                        ("employee_id", "=", record.employee_id.id),
                        ("state", "in", ["done", "paid"]),
                        ("date_from", ">=", record.average_wage_date_start),
                        ("date_to", "<=", record.average_wage_date_end),
                    ]
                )

                neto = record._net_amount(
                    payslip_obj, record.average_wage_currency, True
                )

                if neto.get("struct_type") and neto.get("average_days") > 0:
                    if record.wage_type == "hourly":
                        weeks_between_start_end = (
                            record.average_wage_date_end
                            - (record.average_wage_date_start + relativedelta(days=-1))
                        ).days
                        weeks_between_start_end = weeks_between_start_end / 7
                    else:
                        weeks_between_start_end = (
                            record.average_wage_date_end
                            - record.average_wage_date_start
                        ).days
                        weeks_between_start_end = int(weeks_between_start_end / 7)

                    if weeks_between_start_end < neto["struct_type"].number_of_weeks:
                        raise ValidationError(
                            _("The number of weeks is less than established")
                        )

                    if weeks_between_start_end > neto["struct_type"].number_of_weeks:
                        if (
                            record.wage_type == "monthly"
                            and neto["struct_type"].number_of_weeks == 0
                            and neto["struct_type"].number_of_best_weeks == 0
                        ):
                            pass
                        else:
                            raise ValidationError(
                                _("exceeds the number of weeks established")
                            )

                if payslip_obj or record.is_average_wage:
                    if neto["struct_type"].best_weeks_check:
                        values = neto.get("neto")
                        for iterator in range(
                            int(neto["struct_type"].number_of_best_weeks)
                        ):
                            max_value = max(values, key=values.get) if values else False
                            if max_value:
                                average_wage += values[max_value]
                                values.pop(max_value)
                        average_wage = average_wage / neto.get("average_days")
                    else:
                        average_wage += neto.get("neto") / neto.get("average_days")

                    record.average_wage = average_wage

            elif not (
                record.average_wage_date_start
                and record.average_wage_date_end
                and record.is_average_wage
            ):
                record.average_wage = 0.0

    @api.constrains("average_wage")
    def _check_average_wage(self):
        module = self.env["ir.module.module"].search(
            [("name", "=", "omegasoft_contract_salary_fields")]
        )
        for record in self:
            if record.average_wage < 0:
                raise ValidationError(
                    _("El monto del salario promedio debe ser superior a cero.")
                )
            elif module and module.state == "installed" and record.average_wage:
                record.is_average_wage = True
            else:
                pass

    @api.onchange(
        "average_wage_date_start",
        "average_wage_date_end",
    )
    def _onchange_average_date(self):
        if (
            not self.average_wage_date_start
            and not self.average_wage_date_end
            and self.is_average_wage
        ):
            return {
                "warning": {
                    "title": _("Alerta en fechas del campo Salario Promedio"),
                    "message": _(
                        "Fecha de inicio Y fecha de fin en Salario Promedio Vacias.\n"
                        "El salario promedio quedara con valor cero "
                        "0"
                        ".\n"
                    ),
                }
            }

    # employee file code

    employee_file = fields.Boolean("Employee file", related="company_id.employee_file")
    employee_file_code_id = fields.Many2one(
        "employee.file.code", string="Employee File", ondelete="set null"
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
