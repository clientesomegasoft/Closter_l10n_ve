from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Employee(models.Model):
    _inherit = "hr.employee"

    employee_file = fields.Boolean("Employee File", related="company_id.employee_file")
    employee_file_code_id = fields.Many2one(
        "employee.file.code", string="Employee File"
    )
    registration_number = fields.Char(readonly=True)

    name_file_code_id = fields.Char(
        string="Name Employee File",
        compute="_compute_name_file_code_id",
        inverse="_inverse_name_file_code_id",
        store=True,
        readonly=False,
    )

    @api.depends("employee_file_code_id", "employee_file_code_id.name")
    def _compute_name_file_code_id(self):
        for record in self:
            if self.env.company.employee_file:
                record.name_file_code_id = record.employee_file_code_id.name
            else:
                record.name_file_code_id = False

    # NOTE: This avoids problems with multiple calls to write() on creation time.
    def _inverse_name_file_code_id(self):
        if not self.env.company.employee_file:
            return

        for record in self:
            if record.employee_file_code_id:
                record.employee_file_code_id.name = record.name_file_code_id
            else:
                record.employee_file_code_id = self.env["employee.file.code"].create(
                    {
                        "name": record.name_file_code_id,
                        "employee_id": record.id,
                    }
                )

    @api.model
    def create(self, data_list):
        new_ids = super().create(data_list)
        if not self.env.company.employee_file:
            return new_ids

        for new_id in new_ids:
            if new_id.employee_file_code_id or new_id.name_file_code_id:
                continue

            new_id.employee_file_code_id = self.env["employee.file.code"].create(
                {
                    "employee_id": new_id.id,
                }
            )
        return new_ids

    @api.ondelete(at_uninstall=False)
    def _ondelete_check_payslips(self):
        for record in self:
            if record.slip_ids:
                show_id = (
                    lambda record: record.id
                    if self.env.user.has_group("base.group_no_one")
                    else ""
                )
                LIMIT = 4
                details = "\n".join(
                    f"- ({show_id(slip)}) {slip.name}"
                    for slip in record.slip_ids[:LIMIT]
                )
                more_than_limit = record.slip_ids[LIMIT:]
                if more_than_limit:
                    details = "\n".join([details, _("And more...")])

                raise ValidationError(
                    _(
                        "The employee %s cannot be deleted because it has the following payslip entries:\n%s",
                        record.name,
                        details,
                    )
                )

    @api.constrains("active")
    def _constrains_active(self):
        if self.employee_file:
            if not self.active:
                self.employee_file_code_id.active = False
            else:
                self.employee_file_code_id.active = True

    @api.constrains("employee_file_code_id")
    def _constrains_employee_file_code_id(self):
        if self.employee_file:
            if self.employee_file_code_id:
                self.registration_number = self.employee_file_code_id.name
            else:
                self.registration_number = False
