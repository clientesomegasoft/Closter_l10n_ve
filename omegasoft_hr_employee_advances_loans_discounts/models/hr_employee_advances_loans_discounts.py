from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrEmployeeAdvancesLoansDiscounts(models.Model):
    _name = "hr_employee_advances_loans_discounts"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin"]
    _order = "date_issue desc"
    _description = "Employee Advances, loans and discounts"

    active = fields.Boolean(
        default=True,
        help="Set active to false to hide the salary advance tag without removing it.",
    )

    name = fields.Selection(
        [
            ("employee", "Employee"),
            ("department", "Department"),
            ("company", "Company"),
        ],
        string="Advance type",
        help="""It refers to whether the Advance, Loan or discount is
        for an employee, specific department or the entire company.""",
        tracking=True,
    )

    date_issue = fields.Date(
        string="Date of issue",
        help="Date of issue of the advance, loan or discount",
        default=fields.Date.context_today,
        tracking=True,
    )

    employee_ids = fields.Many2many(
        string="Employees",
        comodel_name="hr.employee",
        help="Employees",
        tracking=True,
        ondelete="restrict",
        domain=lambda self: self.env[
            "hr.employee"
        ]._get_employee_l10n_ve_payroll_domain(),
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        ondelete="restrict",
        string="Company",
        default=lambda self: self.env.company,
        tracking=True,
    )
    employee_contract_ids = fields.Many2many(
        comodel_name="hr.contract",
        string="Employee contract",
        ondelete="restrict",
        tracking=True,
    )
    department_ids = fields.Many2many(
        comodel_name="hr.department",
        ondelete="restrict",
        string="Departments",
        tracking=True,
    )

    employee_reference = fields.Char(
        string="Employee reference",
        help="reference of the loan or advance to be requested.",
        tracking=True,
    )

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("open", "Open"),
            ("paid", "Paid"),
            ("rejected", "Rejected"),
        ],
        string="Status",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        store=True,
        default="draft",
    )

    company_currency = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.company.currency_id,
        tracking=True,
    )
    rate_id = fields.Many2one("res.currency.rate", string="Rate", tracking=True)
    rate_amount = fields.Float(string="Rate amount", tracking=True)

    @api.onchange("rate_id")
    def _rate_onchange(self):
        if self.rate_id:
            self.rate_amount = self.rate_id.inverse_company_rate
        else:
            self.rate_amount = 0

    advances_loans_discounts_line_ids = fields.One2many(
        comodel_name="hr_employee_advances_loans_discounts_lines",
        inverse_name="advances_loans_discounts_id",
        string="Employee Advances, loans and discounts lines",
    )

    def get_employee_advance_domain(self):
        employee_obj = (
            self.employee_ids if self.employee_ids else self.env["hr.employee"]
        )
        return self.env["hr.employee"].search(
            employee_obj._get_employee_l10n_ve_payroll_domain()
        )

    @api.model_create_multi
    def create(self, values):
        res = super(__class__, self).create(values)
        res.state = "draft"
        return res

    def write(self, vals):
        res = super(__class__, self).write(vals)
        for record in self.employee_ids:
            employee_contract = record.contract_id
            if employee_contract.state == "open" and self.state in ["open"]:
                record._compute_advance_social_benefits(employee_contract)
                record._compute_advance_granted(employee_contract)
                record._compute_advance_vacations(employee_contract)
                record._compute_advance_benefit_interest(
                    employee_contract, self.advances_loans_discounts_line_ids
                )
                record._compute_advance_days_per_year(
                    employee_contract, self.advances_loans_discounts_line_ids
                )
        return res

    def unlink(self):
        return super(__class__, self).unlink()

    @api.onchange("company_id", "employee_ids", "department_ids", "name")
    def _onchange_hr_dependent_data(self):
        if self.name == "employee":
            self._dispatch_hr_data_from_employee_ids()
        elif self.name == "department":
            self._dispatch_hr_data_from_department_ids()
        elif self.name == "company":
            self._dispatch_hr_data_from_company_id()

    def _dispatch_hr_data_from_employee_ids(self):
        employee_contract_ids = [fields.Command.clear()]
        department_ids = [fields.Command.clear()]
        if self.employee_ids:
            employee_contract_ids.append(
                fields.Command.set(self.employee_ids.contract_ids.ids)
            )
            department_ids.append(
                fields.Command.set(self.employee_ids.department_id.ids)
            )

        self.company_id = self.env.company
        self.employee_contract_ids = employee_contract_ids
        self.department_ids = department_ids

    def _dispatch_hr_data_from_department_ids(self):
        employee_contract_ids = [fields.Command.clear()]
        employee_ids = [fields.Command.clear()]

        maybe_employees = self.env["hr.employee"]
        if self.department_ids:
            maybe_employees = self.get_employee_advance_domain().filtered(
                lambda x: x.id in self.department_ids.member_ids.ids
            )
            if not maybe_employees:
                raise ValidationError(
                    _(
                        "El departamento seleccionado no tiene "
                        "empleados con contratos En Proceso"
                    )
                )

        employee_ids.append(fields.Command.set(maybe_employees.ids))
        employee_contract_ids.append(
            fields.Command.set(maybe_employees.contract_ids.ids)
        )

        self.company_id = self.env.company
        self.employee_ids = employee_ids
        self.employee_contract_ids = employee_contract_ids

    def _dispatch_hr_data_from_company_id(self):
        maybe_employees = self.get_employee_advance_domain()
        employee_contract_ids = [fields.Command.clear()]
        employee_ids = [fields.Command.clear()]
        department_ids = [fields.Command.clear()]

        if self.company_id:
            employee_ids.append(fields.Command.set(maybe_employees.ids))
            employee_contract_ids.append(
                fields.Command.set(maybe_employees.contract_ids.ids)
            )
            department_ids.append(fields.Command.set(maybe_employees.department_id.ids))

        self.employee_ids = employee_ids
        self.employee_contract_ids = employee_contract_ids
        self.department_ids = department_ids

    def action_confirm(self):
        self.write({"state": "paid"})
        for record in self.advances_loans_discounts_line_ids:
            record.write({"discount_state": "paid"})

    def action_open(self):
        if self.state != "open":
            self.write({"state": "open"})
            for record in self.advances_loans_discounts_line_ids:
                record.write({"discount_state": "open"})

    def action_cancel(self):
        # self._clean_lines()
        self.write({"state": "rejected"})
        for record in self.advances_loans_discounts_line_ids:
            record.write({"discount_state": "rejected"})
            record.product_employee_ids._unlink_advance_loans_discounts(
                record.product_employee_ids.contract_id, record
            )

    def action_draft(self):
        # self._clean_lines()
        self.write({"state": "draft"})
        for record in self.advances_loans_discounts_line_ids:
            record.write({"discount_state": "draft"})
            record.employee_ids._unlink_advance_loans_discounts(
                record.product_employee_ids.contract_id, record
            )

    @api.constrains("advances_loans_discounts_line_ids")
    def _constrain_advances_loans_discounts_line_ids(self):
        if self.advances_loans_discounts_line_ids:
            for record in self.advances_loans_discounts_line_ids:
                if record.amount <= 0:
                    raise ValidationError(
                        _("El monto en las lineas debe ser mayor a cero.")
                    )
                if (
                    record.type_advance_loan in ["loan", "discount", "per_diem"]
                    and record.fees <= 0
                ):
                    raise ValidationError(
                        _("Las Cuotas en las lineas no pueden ser menor o igual a cero")
                    )

    # employee file code

    employee_file = fields.Boolean("Employee file", related="company_id.employee_file")

    # NOTE: Needs to be computed. Otherwise we could
    # have problems with the execution order of
    #       every field involved with these records.
    employee_file_code_ids = fields.Many2many(
        "employee.file.code",
        relation="employee_code_loans_rel",
        compute="_compute_file_code_ids",
        inverse="_inverse_file_code_ids",
        store=True,
        string="Employee File",
    )

    @api.depends("employee_ids")
    def _compute_file_code_ids(self):
        if self.employee_file:
            for record in self:
                record.employee_file_code_ids = [
                    fields.Command.clear(),
                    fields.Command.set(record.employee_ids.employee_file_code_id.ids),
                ]

    @api.onchange("employee_file_code_ids")
    def _inverse_file_code_ids(self):
        if self.employee_file:
            for record in self:
                record.employee_ids = [
                    fields.Command.clear(),
                    fields.Command.set(record.employee_file_code_ids.employee_id.ids),
                ]

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
