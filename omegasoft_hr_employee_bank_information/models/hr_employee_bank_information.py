from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrEmployeeBankInformation(models.Model):
    _name = "hr_employee_bank_information"
    _description = "Employees bank information"

    active = fields.Boolean(
        default=True,
        help="""Set active to false to hide the fam,ily
        information tag without removing it.""",
    )
    name = fields.Many2one(
        "res.bank", "Bank", help="Bank to which the beneficiary's bank account belongs."
    )
    bank_account_number = fields.Char(
        string="Bank account number",
        groups="hr.group_hr_user",
        help="Employee Salary Bank Account",
    )
    account_type = fields.Selection(
        [
            ("current_account", "Current account"),
            ("savings_account", "Savings account"),
        ],
        string="Type of account",
        groups="hr.group_hr_user",
        help="Type of employees bank account.",
    )
    account_holder = fields.Char(
        string="Account holder", groups="hr.group_hr_user", help="Bank account holder"
    )
    letter = fields.Selection(
        [("v", "V - Venezolano"), ("e", "E - Extranjero"), ("j", "J - Jurídica")],
        string="Qualifying Letter",
        groups="hr.group_hr_user",
        help="Qualifying Letter",
    )
    holder_account_id = fields.Char(
        string="C.I. of the account holder",
        groups="hr.group_hr_user",
        help="ID of the account holder",
    )
    is_payroll_account = fields.Boolean(string="This is a payroll account")
    employee_id = fields.Many2one(
        comodel_name="hr.employee", string="Employee bank information"
    )

    @api.constrains("name")
    def constrains_name(self):
        for record in self:
            if record.name and record.name.bic == False:
                raise ValidationError(
                    _(
                        "Por favor establezca el Código de identificación "
                        "bancaria (BIC/SWIFT) para el banco seleccionado"
                    )
                )
            elif record.name and record.name.bic and len(record.name.bic) > 12:
                raise ValidationError(
                    _(
                        "La longitud del Código de identificación bancaria "
                        "(BIC/SWIFT) no debe ser mayor a 12 caracteres"
                    )
                )

    @api.constrains("bank_account_number")
    def _check_bank_account_number(self):
        for record in self:
            if record.bank_account_number and (
                not record.bank_account_number.isnumeric()
                or len(record.bank_account_number) != 20
            ):
                raise ValidationError(
                    _(
                        "Sólo se permiten caracteres numéricos [0-9] y la "
                        "longitud total del número de cuenta bancaria debe ser "
                        "igual a 20 caracteres."
                    )
                )

    @api.constrains("account_holder")
    def _check_account_holder(self):
        for record in self:
            account_holder_len = len(record.account_holder)
            account_holder_name = record.account_holder.replace(" ", "")
            if record.account_holder and (
                not account_holder_name.isalpha() or account_holder_len > 25
            ):
                raise ValidationError(
                    _(
                        "El nombre del titular de la cuenta debe contener "
                        "únicamente caracteres alfabéticos [a-z,A-Z] y su "
                        "longitud no debe superar los 25 caracteres."
                    )
                )

    @api.constrains("holder_account_id")
    def _check_holder_account_id(self):
        for record in self:
            if record.holder_account_id and (
                not record.holder_account_id.isnumeric()
                or len(record.holder_account_id) != 8
            ):
                raise ValidationError(
                    _(
                        "Sólo se permiten caracteres numéricos [0-9] y "
                        "la longitud total del número de identificación del "
                        "titular de la cuenta debe ser igual a 8 caracteres."
                    )
                )
