from odoo import _, fields, models
from odoo.exceptions import ValidationError


class HrReportLetters(models.TransientModel):
    _name = "hr.report.letters"
    _description = "Hr Report Letters"

    date = fields.Date("Date")
    letter_type = fields.Selection(
        [("txt", "Bank Letter (txt)"), ("work", "Work Letter")], string="Letter Type"
    )

    employee_id = fields.Many2one("hr.employee", string="Employee")
    export_bank_payment_id = fields.Many2one(
        "export.bank.payments", string="TXT Number"
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    def button_print(self):
        if self.letter_type == "work":
            if not self.employee_id:
                raise ValidationError(_("Debe seleccionar un Empleado!"))
            # self.employee_id
            return self.env.ref(
                "omegasoft_hr_report_letters.report_hr_work_letter_action"
            ).report_action(None)

        elif self.letter_type == "txt":
            if not self.export_bank_payment_id:
                raise ValidationError(_("Debe seleccionar un Número de TXT!"))
            return self.env.ref(
                "omegasoft_hr_report_letters.report_hr_txt_letter_action"
            ).report_action(None)

    def get_account_move(self):
        moves = self.export_bank_payment_id._get_payslips().mapped("move_id")
        return ",".join(moves.mapped("name"))

    def get_payslip_amount(self):
        return sum(self.export_bank_payment_id._get_payslips().mapped("net_wage"))
