from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    bank_information_ids = fields.One2many(
        comodel_name="hr_employee_bank_information",
        inverse_name="employee_id",
        string="Bank information",
    )

    @api.constrains("bank_information_ids")
    def _constrain_bank_information_ids(self):
        count_is_payroll_account = 0
        for record in self:
            if record.bank_information_ids:
                count_is_payroll_account = len(
                    record.bank_information_ids.filtered(lambda x: x.is_payroll_account)
                )
            else:
                pass
            if count_is_payroll_account > 1:
                raise ValidationError(
                    _("Sólo se permiten seleccionar una cuenta, como cuenta de nomina")
                )
            elif count_is_payroll_account == 0 and record.bank_information_ids:
                raise ValidationError(
                    _("Es necesario marcar en una de las "
                    "lineas el check de cuenta nomina.")
                )
