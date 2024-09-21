from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrContractAllocation(models.Model):
    _name = "contract_allocation"
    _description = "Contract allocations"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin"]
    _order = "allocation_date desc, state desc"

    name = fields.Selection(
        selection=[("employee", "Employee")],
        string="Type of endowment",
        help="Indicates the type of endowment to be generated",
        tracking=True,
    )

    employee_ids = fields.Many2many(
        string="Employees",
        comodel_name="hr.employee",
        ondelete="restrict",
        domain=lambda self: self.env[
            "hr.employee"
        ]._get_employee_l10n_ve_payroll_domain(),
    )

    employee_contract_ids = fields.Many2many(
        comodel_name="hr.contract",
        string="Employee contract",
        ondelete="restrict",
        store=True,
        tracking=True,
    )

    job_title = fields.Char(string="Job Title", tracking=True)

    department_ids = fields.Many2many(
        comodel_name="hr.department",
        ondelete="restrict",
        string="Departments",
        tracking=True,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        ondelete="restrict",
        string="Company",
        default=lambda self: self.env.company,
        tracking=True,
    )

    allocation_date = fields.Date(
        string="Allocation date",
        default=fields.Date.context_today,
        tracking=True,
        help="Start date for delivery of the endowment",
    )

    allocation_line_ids = fields.One2many(
        string="Allocation line",
        comodel_name="contract_allocation_lines",
        inverse_name="allocation_id",
        tracking=True,
    )

    active = fields.Boolean(
        default=True,
        help="Set active to false to hide the allocation tag without removing it.",
    )

    compute_state = fields.Boolean(compute="_compute_state")

    state = fields.Selection(
        selection=[
            ("draft", "To be delivered"),
            ("partial_delivery", "Partial delivery"),
            ("delivered", "Delivered"),
        ],
        string="Status",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        store=True,
        default="draft",
    )

    description = fields.Char(string="Description", tracking=True)

    def get_employee_allocation_domain(self):
        employee_obj = (
            self.employee_ids if self.employee_ids else self.env["hr.employee"]
        )
        return self.env["hr.employee"].search(
            employee_obj._get_employee_l10n_ve_payroll_domain()
        )

    @api.onchange("employee_ids")
    def _check_employee_ids(self):
        if self.name == "employee" and len(self.employee_ids) > 1:
            raise ValidationError(
                "Las dotaciones por empleado sólo aceptan un máximo de 1 empleado"
            )

    @api.onchange("employee_ids", "name")
    def _onchange_employee_ids(self):
        if self.name == "employee":
            self.write({"employee_contract_ids": [(5, 0, 0)]})
            self.write({"department_ids": [(5, 0, 0)]})
            self.job_title = False
            if self.employee_ids:
                self.job_title = (
                    self.employee_ids.job_title
                    if self.name == "employee" and len(self.employee_ids) == 1
                    else " "
                )
                self.write(
                    {
                        "employee_contract_ids": [
                            (6, 0, self.employee_ids.contract_ids.ids)
                        ]
                    }
                )
                self.write(
                    {"department_ids": [(6, 0, self.employee_ids.department_id.ids)]}
                )
                self.company_id = self.employee_ids.company_id

    @api.onchange("department_ids", "name")
    def _onchange_department_ids(self):
        if self.name == "department":
            self.write({"employee_ids": [(5, 0, 0)]})
            self.write({"employee_contract_ids": [(5, 0, 0)]})
            self.job_title = False
            if self.department_ids:
                self.job_title = (
                    self.employee_ids.job_title if len(self.employee_ids) == 1 else " "
                )
                employees = self.get_employee_allocation_domain().filtered(
                    lambda x: x.id in self.department_ids.member_ids.ids
                )
                if not employees:
                    raise ValidationError(
                        "El departamento seleccionado no tiene empleados con contratos En Proceso"
                    )
                else:
                    self.write({"employee_ids": [(6, 0, employees.ids)]})
                    self.write(
                        {
                            "employee_contract_ids": [
                                (6, 0, self.employee_ids.contract_ids.ids)
                            ]
                        }
                    )
                    self.company_id = self.employee_ids.company_id

    @api.onchange("company_id", "name")
    def _onchange_company_id(self):
        if self.name == "company":
            employee_obj = self.get_employee_allocation_domain()
            self.write({"employee_ids": [(5, 0, 0)]})
            self.write({"employee_contract_ids": [(5, 0, 0)]})
            self.write({"department_ids": [(5, 0, 0)]})
            self.job_title = False
            if self.company_id:
                self.write({"employee_ids": [(6, 0, employee_obj.ids)]})
                self.write(
                    {
                        "employee_contract_ids": [
                            (6, 0, self.employee_ids.contract_ids.ids)
                        ]
                    }
                )
                self.write(
                    {"department_ids": [(6, 0, self.employee_ids.department_id.ids)]}
                )

    def get_lines_to_delivered(self):
        self.ensure_one()
        lines_tree_view = self.env.ref(
            "omegasoft_contract_allocation.contract_allocation_lines_tree",
            raise_if_not_found=False,
        )
        return {
            "name": ("Líneas de Dotaciones a entregar"),
            "view_mode": "tree",
            "res_model": "contract_allocation_lines",
            "view_id": lines_tree_view.id,
            "type": "ir.actions.act_window",
            "domain": [
                ("allocation_id.id", "=", self.id),
                ("employee_id", "in", self.employee_ids.ids),
            ],
            "context": "{'create': False}",
            "target": "new",
        }

    def write(self, vals):
        return super(HrContractAllocation, self).write(vals)

    @api.depends("allocation_line_ids.state")
    def _compute_state(self):
        self.compute_state = True
        list_state = self.allocation_line_ids.mapped("state")
        if "draft" in list_state or not list_state:
            self.write({"state": "draft"})
        elif "partial_delivery" in list_state:
            self.write({"state": "partial_delivery"})
        else:
            self.write({"state": "delivered"})

    @api.constrains("allocation_line_ids")
    def _constrain_allocation_line_ids(self):
        if self.allocation_line_ids:
            for record in self.allocation_line_ids:
                if record.allocated_quantity <= 0:
                    raise ValidationError("La cantidad asignada debe ser mayor a cero")
                if record.frequency <= 0:
                    raise ValidationError("La frecuencia debe ser mayor a cero")

    # employee file code
    employee_file = fields.Boolean("Employee file", related="company_id.employee_file")
    employee_file_code_ids = fields.Many2many(
        "employee.file.code",
        relation="employee_code_contract_allocation_rel",
        string="Employee File",
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
