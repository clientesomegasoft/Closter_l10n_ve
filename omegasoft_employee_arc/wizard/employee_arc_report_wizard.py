from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class EmployeeARCReport(models.TransientModel):
    _name = "employee.arc.report.wizard"
    _description = "Reporte ARC Empleados"

    type = fields.Selection(
        [
            ("company", "Compañia"),
            ("deparment", "Departamento"),
            ("employee", "Empleado"),
        ],
        string="Tipo de plantilla",
        default="employee",
        required=True,
    )
    year = fields.Integer(
        string="Período", required=True, default=fields.Date.today().year
    )
    employee_ids = fields.Many2many(
        "hr.employee",
        string="Empleados",
        compute="_compute_employee_ids",
        store=True,
        required=True,
        domain="[('company_id', '=', company_id)]",
    )
    department_id = fields.Many2one(
        "hr.department",
        string="Departamento",
        domain="[('company_id', '=', company_id)]",
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
        readonly=True,
    )

    @api.depends("type", "department_id", "company_id")
    def _compute_employee_ids(self):
        for rec in self:
            rec.employee_ids = [(5,)]
            if rec.type == "company":
                rec.employee_ids = self.env["hr.employee"].search(
                    [("company_id", "=", rec.company_id.id)]
                )
            elif rec.type == "deparment" and rec.department_id:
                rec.employee_ids = self.env["hr.employee"].search(
                    [
                        ("company_id", "=", rec.company_id.id),
                        ("department_id", "=", rec.department_id.id),
                    ]
                )

    @api.onchange("type")
    def _onchange_type(self):
        self.department_id = False

    def get_pdf(self):
        return self.env.ref(
            "omegasoft_employee_arc.action_employee_arc_report"
        ).report_action(self)

    def get_months_table(self):
        params = []
        for month in range(1, 13):
            date_from = fields.Date.from_string(f"{self.year}-{month}-01")
            date_to = date_from + relativedelta(day=31)
            month_name = format_date(
                self.env, date_from, date_format="MMMM"
            ).capitalize()
            params += [month_name, date_from, date_to]
        return self.env.cr.mogrify(
            "(VALUES %s) AS months_table(month_name, date_from, date_to)"
            % ",".join(["(%s, %s, %s)"] * 12),
            params,
        ).decode(self.env.cr.connection.encoding)

    def get_pdf_and_send(self):
        self.ensure_one()
        if self.company_id.arc_template_id:
            active_ids = self.env.context.get("active_ids", self.employee_ids.ids)
            active_employee = self.env["hr.employee"].browse(active_ids)
            value = self.employee_ids.filtered(lambda employee: not employee.work_email)
            if value:
                message = ""
                for val in value:
                    message += val.employee_file_code_id.name + " - " + val.name + "\n"
                raise UserError(_("Empleados no tiene corre asociado: \n%s", message))
            for employee in active_employee:
                self.employee_ids = [(6, 0, employee.ids)]
                self.company_id.arc_template_id.send_mail(self.id)
            self.employee_ids = [(6, 0, active_employee.ids)]
            return self.env.ref(
                "omegasoft_employee_arc.action_employee_arc_report"
            ).report_action(self)
        else:
            raise UserError(
                _(
                    "No existe plantilla para el envio de "
                    "ARC configurada en ajuste de nomina."
                )
            )

    # employee file code

    employee_file = fields.Boolean("Employee file", related="company_id.employee_file")
    employee_file_code_ids = fields.Many2many(
        "employee.file.code", relation="employee_code_arc_rel", string="Employee File"
    )

    @api.onchange("employee_file_code_ids")
    def _onchange_employee_file_code_ids(self):
        if self.employee_file:
            if (
                self.employee_file_code_ids
                and self.employee_file_code_ids.employee_id.ids != self.employee_ids.ids
            ):
                self.employee_ids = [
                    (6, 0, self.employee_file_code_ids.employee_id.ids)
                ]
            elif not self.employee_file_code_ids and self.employee_ids:
                self.employee_ids = [(6, 0, [])]

    @api.onchange("employee_ids")
    def _onchange_employee(self):
        if self.employee_file:
            if (
                self.employee_ids
                and self.employee_ids.ids != self.employee_file_code_ids.employee_id.ids
            ):
                self.employee_file_code_ids = [
                    (6, 0, self.employee_ids.employee_file_code_id.ids)
                ]
            elif not self.employee_ids and self.employee_file_code_ids:
                self.employee_file_code_ids = [(6, 0, [])]

    @api.constrains("employee_file_code_ids")
    def _constrains_employee_file_code_ids(self):
        if self.employee_file:
            if not self._context.get("bypass", False):
                if (
                    self.employee_file_code_ids
                    and self.employee_file_code_ids.employee_id.ids
                    != self.employee_ids.ids
                ):
                    self.employee_ids = [
                        (6, 0, self.employee_file_code_ids.employee_id.ids)
                    ]
                elif not self.employee_file_code_ids and self.employee_ids:
                    self.employee_ids = [(6, 0, [])]

    @api.constrains("employee_ids")
    def _constrains_employee(self):
        if self.employee_file:
            if (
                self.employee_ids
                and self.employee_ids.ids != self.employee_file_code_ids.employee_id.ids
            ):
                self.employee_file_code_ids = [
                    (6, 0, self.employee_ids.employee_file_code_id.ids)
                ]
            elif not self.employee_ids and self.employee_file_code_ids:
                self.employee_file_code_ids = [(6, 0, [])]

    # employee file code
