import base64
import re
import time
from datetime import datetime

import pytz

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ExportBankPayments(models.Model):
    _name = "export.bank.payments"
    _description = "Export Payroll Payments"

    _READONLY_STATES = {"done": [("readonly", True)]}

    name = fields.Char("Nombre", default="Nuevo", readonly=True)
    state = fields.Selection(
        [("draft", "Borrador"), ("done", "Confirmado")],
        string="Estado de transacción",
        default="draft",
        copy=False,
    )
    date_start = fields.Date("Fecha inicio", states=_READONLY_STATES)
    date_end = fields.Date("Fecha fin", states=_READONLY_STATES)
    txt_file = fields.Binary("Archivo TXT", copy=False)
    txt_name = fields.Char("Filename txt", copy=False)
    bank_id = fields.Many2one("res.bank", "Banco", states=_READONLY_STATES)
    bank_account_id = fields.Many2one(
        "res.partner.bank",
        "Número de Cuenta Bancaria",
        states=_READONLY_STATES,
        help="Cuenta bancaria de la compañía de donde será debitado el dinero.",
    )
    by_employee = fields.Boolean(
        string="Por empleado",
        default=False,
        help="Indica si el txt se genera para determinados empleados.",
        states=_READONLY_STATES,
    )
    employee_ids = fields.Many2many(
        "hr.employee",
        string="Empleados",
        states=_READONLY_STATES,
        help="Empleados para los que se genera el archivo txt.",
    )
    employee_domain = fields.Many2many(
        "hr.employee",
        compute="_compute_employee_ids",
        string="Dominio para Empleados",
        help="Dominio para filtrar empleados.",
    )
    description = fields.Char(
        "Descripción",
        help="Texto descriptivo asociado al archivo txt generado.",
        states=_READONLY_STATES,
    )

    structure_id = fields.Many2one(
        "hr.payroll.structure",
        string="Tipo de nómina",
        states=_READONLY_STATES,
        help="Tipo de nómina a tomar en cuenta para la generación del archivo txt.",
    )
    operation_type = fields.Selection(
        [("same", "Mismo banco"), ("other", "Otros bancos")],
        string="Tipo de operación",
        states=_READONLY_STATES,
        default="same",
        help="Indica si el pago de nominas es entre cuentas del mismo banco o no.",
    )
    type_trans = fields.Selection(
        [("payroll", "Empleados")],
        string="Pago a",
        default="payroll",
        states=_READONLY_STATES,
        help="Indica el tipo de txt a generar.",
    )

    txt_type = fields.Selection(
        [("ticket", "Todoticket"), ("guard", "Guarderia")],
        string="Tipo TXT",
        states=_READONLY_STATES,
    )

    valid_date = fields.Date(
        "Fecha efectiva de pago",
        states=_READONLY_STATES,
        help="Fecha en que se ejecutará el pago.",
    )

    @api.onchange("txt_type")
    def _onchange_txt_type(self):
        if self.txt_type:
            if self.txt_type == "ticket":
                self.operation_type = "same"
            elif self.txt_type == "guard":
                self.operation_type = "other"
            if self.by_employee:
                self.employee_ids = False

    @api.constrains("employee_ids")
    def _check_employee_ids(self):
        if self.employee_ids and len(self.employee_ids) > 10:
            raise ValidationError(
                "La cantidad maxima de empleados por TXT no debe ser mayor a 10."
            )

    def _get_employee_domain(self, bank_account_number, operation_type_same=False):
        employees_domain = False

        if operation_type_same:
            employees_bank_info = (
                self.env["hr_employee_bank_information"]
                .search([("is_payroll_account", "=", True)])
                .filtered(lambda x: x.name == self.bank_id)
            )
        else:
            employees_bank_info = (
                self.env["hr_employee_bank_information"]
                .search([("is_payroll_account", "=", True)])
                .filtered(lambda x: x.name != self.bank_id)
            )

        employees_domain = self.env["hr.employee"].search(
            [("id", "in", employees_bank_info.employee_id.ids)]
        )
        if self.structure_id:
            payslip_employees = (
                self.env["hr.payslip"]
                .search(
                    [
                        ("date_from", "=", self.date_start),
                        ("date_to", "=", self.date_end),
                        ("struct_id", "=", self.structure_id.id),
                        ("move_id.state", "=", "posted"),
                        ("employee_id", "in", employees_domain.ids),
                    ]
                )
                .mapped("employee_id")
            )
        else:
            payslip_employees = (
                self.env["hr.payslip"]
                .search(
                    [
                        ("date_from", "=", self.date_start),
                        ("date_to", "=", self.date_end),
                        ("move_id.state", "=", "posted"),
                        ("employee_id", "in", employees_domain.ids),
                    ]
                )
                .mapped("employee_id")
            )
        if payslip_employees:
            employees_domain = employees_domain.filtered(
                lambda e: e.id in payslip_employees.ids
            )
        else:
            employees_domain = False
        return employees_domain

    @api.onchange("by_employee")
    def _onchange_by_employee(self):
        if not self.by_employee:
            self.employee_ids = False

    @api.onchange("bank_id")
    def _onchange_bank_domain(self):
        domain = {}
        if not self.bank_id:
            banks = self.env["res.partner.bank"].search([])
            banks_ids = []
            for bank in banks:
                if bank.is_payroll_account:
                    banks_ids.append(bank.bank_id.id)
            domain = {"domain": {"bank_id": [("id", "in", banks_ids)]}}
        return domain

    @api.onchange("bank_id")
    def _onchange_bank_account_id(self):
        if self.type_trans == "payroll":
            self.bank_account_id = False
            self.employee_ids = False
        banks = self.env["res.partner.bank"].search([])
        banks_ids = []
        for bank in banks:
            if bank.is_payroll_account:
                banks_ids.append(bank.id)
        return {
            "domain": {
                "bank_account_id": [
                    ("id", "in", banks_ids),
                    ("bank_id", "=", self.bank_id.id),
                ]
            }
        }

    @api.depends("bank_account_id", "operation_type", "by_employee", "type_trans")
    def _compute_employee_ids(self):
        for export_bank_payment in self:
            export_bank_payment.employee_domain = self.env["hr.employee"]
            if export_bank_payment.bank_account_id and export_bank_payment.by_employee:
                bank_account_number = (
                    export_bank_payment.bank_account_id.sanitized_acc_number[:4]
                )

                # Obtener los ids de los empleados
                if export_bank_payment.operation_type == "same":
                    employees_domain = self._get_employee_domain(
                        bank_account_number, True
                    )
                    export_bank_payment.employee_domain = employees_domain
                else:
                    employees_domain = self._get_employee_domain(bank_account_number)
                    export_bank_payment.employee_domain = employees_domain

            elif (
                export_bank_payment.type_trans == "fiscal"
                and export_bank_payment.by_employee
            ):
                export_bank_payment.employee_domain = self.env["hr.employee"].search([])

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for new_id in records:
            new_id.name = self.env["ir.sequence"].next_by_code("export.bank.payments")
        return records

    def unlink(self):
        sequences = self.env.ref(
            "omegasoft_export_payroll_payments.sequence_txt_bank_rolda"
        )
        current_sequence = self.env["export.bank.payments"].search(
            [], order="name desc", limit=1
        )

        if all(int(item) < int(current_sequence.name) for item in self.mapped("name")):
            raise ValidationError(
                "No se puede eliminar. Hay secuencias superiores creadas"
            )
        else:
            if len(self) == 1:
                number_next_actual = int(current_sequence.name)
            else:
                number_next_actual = 1
            sequences.write({"number_next_actual": number_next_actual})
        return super(__class__, self).unlink()

    def action_draft(self):
        self.write(
            {
                "state": "draft",
                "txt_file": False,
                "txt_name": False,
            }
        )
        return True

    def action_done(self):
        """Exportar el documento en texto plano."""
        self.ensure_one()
        data = ""

        if (
            self.bank_account_id.sanitized_acc_number
            and len(self.bank_account_id.sanitized_acc_number) != 20
        ):
            raise ValidationError(
                "La longitud del número de cuenta de la compañia debe ser de 20 dígitos."
            )

        elif self.bank_account_id and not self.bank_account_id.is_payroll_account:
            raise ValidationError(
                "La cuenta de la compañia debe estar configurada como 'Cuenta de Nomina'."
            )

        if (
            self.env.company.partner_id.partner_type != "other"
            and not self.env.company.partner_id.vat
        ):
            raise ValidationError("Por favor establezca el RIF de la compañia.")

        bank_account_number = self.bank_account_id.acc_number[:4]

        if bank_account_number == "0191":
            root = self.generate_bnc()
            data, filename = self._write_attachment(root, "BNC")
        elif bank_account_number == "0102":
            root = self.generate_vzla()
            data, filename = self._write_attachment(root, "VZLA")
        elif bank_account_number == "0134":
            root = self.generate_banesco()
            data, filename = self._write_attachment(root, "BANESCO")
        elif bank_account_number == "0105":
            root = self.generate_mercantil()
            data, filename = self._write_attachment(root, "BSF000W", use_date=False)

        if not data:
            raise ValidationError(
                "No se pudo generar el archivo. Intente de nuevo con otro periodo."
            )
        return self.write({"state": "done"})

    def _write_attachment(self, root, prefix, use_date=True):
        """Encrypt txt, save it to the db and view it on the client as an
        attachment
        @param root: location to save document
        """
        date = time.strftime("%d%m%y") if use_date else ""
        txt_name = f"{prefix}{date}.txt"
        txt_file = root.encode("utf-8")
        txt_file = base64.encodebytes(txt_file)
        self.write({"txt_name": txt_name, "txt_file": txt_file})
        return txt_file, txt_name

    def _get_payslips(self):
        """
        Consulta de recibos de pagos. De acuerdo a las siguientes condiciones:
        1. Periodo del recibo
        2. Estado del asiento contable = publicado
        """
        if self.structure_id:
            payslips = self.env["hr.payslip"].search(
                [
                    ("date_from", "=", self.date_start),
                    ("date_to", "=", self.date_end),
                    ("struct_id", "=", self.structure_id.id),
                    ("move_id.state", "=", "posted"),
                ]
            )
        else:
            payslips = self.env["hr.payslip"].search(
                [
                    ("date_from", "=", self.date_start),
                    ("date_to", "=", self.date_end),
                    ("move_id.state", "=", "posted"),
                ]
            )
        # Filtro:
        # 1. Tipo de operacion: Comparar primeros 4 digitos de la cuenta de la compañia con los de la cuenta del empleado
        if self.type_trans != "fiscal":
            bank_account_number = self.bank_account_id.acc_number[:4]
            if self.operation_type == "same":
                employee_domain = self._get_employee_domain(bank_account_number, True)
                if not employee_domain:
                    raise ValidationError(
                        "No se pudo generar el archivo. Intente de nuevo con otro periodo."
                    )
                payslips = payslips.filtered(
                    lambda x: self.bank_account_id.acc_number
                    and x.employee_id.id in employee_domain.ids
                )
            else:
                employee_domain = self._get_employee_domain(bank_account_number)
                if not employee_domain:
                    raise ValidationError(
                        "No se pudo generar el archivo. Intente de nuevo con otro periodo."
                    )
                payslips = payslips.filtered(
                    lambda x: self.bank_account_id.acc_number
                    and x.employee_id.id in employee_domain.ids
                )
        # 2. Por empleado
        if self.by_employee:
            payslips = payslips.filtered(
                lambda x: x.employee_id.id in self.employee_ids.ids
            )

        return payslips

    def employee_payroll_validations(self, payslip):
        if not payslip.net_wage or payslip.net_wage <= 0.0:
            raise ValidationError(
                ("Establezca un monto valido a pagar al empleado: %s.")
                % (payslip.employee_id.name)
            )

        if len(f"{payslip.net_wage:.2f}") > 13:
            raise ValidationError(
                (
                    "El monto a pagar para el empleado: %s, excede la cantidad maxima de digitos."
                )
                % (payslip.employee_id.name)
            )

        if self.operation_type == "same":
            if len(f"{payslip.net_wage:.2f}".replace(".", "")) > 11:
                raise ValidationError(
                    (
                        "El monto a pagar para el empleado: %s, excede la cantidad maxima de digitos."
                    )
                    % (payslip.employee_id.name)
                )

        if self.operation_type == "other":
            if not payslip.employee_id.country_id:
                raise ValidationError(
                    ("Por favor establezca la nacionalidad del empleado: %s.")
                    % (payslip.employee_id.name)
                )

            if len(f"{payslip.net_wage:.2f}") > 18:
                raise ValidationError(
                    (
                        "El monto a pagar para el empleado: %s, excede la cantidad maxima de digitos."
                    )
                    % (payslip.employee_id.name)
                )

        return True

    def _txt_prepare_data_bnc(self, payslip):
        aux_txt_data = ""

        # *** Preparacion de campos ***
        employees_bank_info = self.env["hr_employee_bank_information"].search(
            [
                ("employee_id", "=", payslip.employee_id.id),
                ("is_payroll_account", "=", True),
            ]
        )

        bank_acc = employees_bank_info.bank_account_number
        amount = f"{payslip.net_wage:.2f}".replace(".", "")
        employee = payslip.employee_id
        if not employees_bank_info.letter:
            raise ValidationError(
                f"No se encuentra configurada la Letra Calificadora en los datos bancarios del empleado {employee.name}"
            )
        nationality = employees_bank_info.letter.upper()
        id_digits = employees_bank_info.holder_account_id

        # # *** Construccion de registro ***
        aux_txt_data += f'{"ND":<2}{"0":<1}{bank_acc:<20}{amount:0>13}{nationality:<1}{id_digits:0>9}'

        return aux_txt_data

    def generate_bnc(self):
        # Obtener recibos de salario
        payslips = self._get_payslips()
        txt_data = ""
        if payslips:
            # *** Registro de cabecera ***

            # 1. Preparacion de campos

            bank_acc = self.bank_account_id.sanitized_acc_number
            total_payroll = 0.0
            for payslip in payslips:
                total_payroll += payslip.net_wage
            total_payroll = f"{total_payroll:.2f}".replace(".", "")
            if len(total_payroll) > 13:
                raise ValidationError(
                    "El monto total de la nomina excede la cantidad maxima de digitos."
                )

            if self.env.company.partner_id.vat:
                nationality = self.env.company.partner_id.vat[:1]
                vat_digits = self.env.company.partner_id.vat.replace("J", "").replace(
                    "-", ""
                )
            else:
                nationality = ""
                vat_digits = ""

            # 2. Construccion de linea
            txt_data += f'{"NC":<2}{"0":<1}{bank_acc:<20}{total_payroll:0>13}{nationality:<1}{vat_digits:0>9}'

            for payslip in payslips:
                # *** Registro detalle ***
                self.employee_payroll_validations(payslip)
                txt_data += "\n" + self._txt_prepare_data_bnc(payslip)
        return txt_data

    def _txt_prepare_data_banesco(self, payslip):
        if not payslip.net_wage or payslip.net_wage <= 0.0:
            raise ValidationError(
                ("Establezca un monto valido a pagar al empleado: %s.")
                % (payslip.employee_id.name)
            )

        if len(f"{payslip.net_wage:.2f}") > 15:
            raise ValidationError(
                (
                    "El monto a pagar para el empleado: %s, excede la cantidad maxima de digitos."
                )
                % (payslip.employee_id.name)
            )

        if not payslip.employee_id.country_id:
            raise ValidationError(
                ("Por favor establezca la nacionalidad del empleado: %s.")
                % (payslip.employee_id.name)
            )

        aux_txt_data = ""

        # *** Preparacion de campos ***
        employees_bank_info = self.env["hr_employee_bank_information"].search(
            [
                ("employee_id", "=", payslip.employee_id.id),
                ("is_payroll_account", "=", True),
            ]
        )

        bank_acc = employees_bank_info.bank_account_number
        amount = f"{payslip.net_wage:.2f}".replace(".", "")
        employee = payslip.employee_id
        if not employees_bank_info.letter:
            raise ValidationError(
                f"No se encuentra configurada la Letra Calificadora en los datos bancarios del empleado {employee.name}"
            )
        nationality = employees_bank_info.letter
        id_digits = employees_bank_info.holder_account_id

        a, b = "áéíóúüÁÉÍÓÚñÑ", "aeiouuAEIOUnN"
        trans = str.maketrans(a, b)
        employee_name = employee.name.translate(trans)

        aux_txt_data += "03"
        aux_txt_data += "{:0<8}".format(payslip.number.split("/")[1]) + " " * 22
        aux_txt_data += f"{amount:0>15}"
        aux_txt_data += "VES"
        aux_txt_data += f"{bank_acc:<30}"
        aux_txt_data += f"{bank_acc[:4]:<11}"
        aux_txt_data += "   "
        aux_txt_data += f"{nationality + id_digits:<17}"
        aux_txt_data += f"{employee_name:<70}"
        aux_txt_data += " " * 70
        aux_txt_data += " " * 25
        aux_txt_data += " " * 17
        aux_txt_data += " " * 35
        aux_txt_data += " " * 31
        aux_txt_data += " " * 23
        aux_txt_data += "42 "

        return aux_txt_data

    def generate_banesco(self):
        txt_data = ""
        # Obtener recibos de salario
        payslips = self._get_payslips()
        if self.txt_type == "ticket":
            # Obtener recibos de salario
            if payslips:
                for payslip in payslips:
                    employees_bank_info = self.env[
                        "hr_employee_bank_information"
                    ].search(
                        [
                            ("employee_id", "=", payslip.employee_id.id),
                            ("is_payroll_account", "=", True),
                        ]
                    )
                    amount = f"{payslip.net_wage:.2f}".replace(".", "")
                    employee = payslip.employee_id
                    if not employees_bank_info.letter:
                        raise ValidationError(
                            f"No se encuentra configurada la Letra Calificadora en los datos bancarios del empleado {employee.name}"
                        )
                    nationality = employees_bank_info.letter.upper()
                    id_digits = employees_bank_info.holder_account_id
                    a, b = "áéíóúüÁÉÍÓÚñÑ", "aeiouuAEIOUnN"
                    trans = str.maketrans(a, b)
                    employee_name = employee.name.translate(trans)
                    txt_data += f'{nationality}{id_digits:0>9}{"  "}{amount:0>21}{self.valid_date.strftime("%d%m%Y")}{employee_name:<60}\n'
        elif self.txt_type == "guard":
            if payslips:
                for payslip in payslips:
                    employees_bank_info = self.env[
                        "hr_employee_bank_information"
                    ].search(
                        [
                            ("employee_id", "=", payslip.employee_id.id),
                            ("is_payroll_account", "=", True),
                        ]
                    )
                    amount = f"{payslip.net_wage:.2f}".replace(".", "")
                    employee = payslip.employee_id
                    if not employees_bank_info.letter:
                        raise ValidationError(
                            f"No se encuentra configurada la Letra Calificadora en los datos bancarios del empleado {employee.name}"
                        )
                    nationality = employees_bank_info.letter.upper()
                    id_digits = employees_bank_info.holder_account_id

                    a, b = "áéíóúüÁÉÍÓÚñÑ", "aeiouuAEIOUnN"
                    trans = str.maketrans(a, b)
                    employee_name = employee.name.translate(trans)
                    bank_name = employees_bank_info.name.name.translate(trans)
                    bank_name = re.sub(r"[^a-zA-Z0-9]+", " ", bank_name)
                    first_name = employee_name.split()[0]
                    last_name = employee_name.split()[1]
                    print_name = first_name + " " + last_name

                    description = self.description.translate(trans)
                    description = re.sub(r"[^a-zA-Z0-9]+", " ", description)

                    bank_acc = employees_bank_info.bank_account_number
                    bank_code = bank_acc[:4]

                    txt_data += f'{nationality}{id_digits:0>9}{"  "}{first_name:<20}{last_name:<20}{"NO APLICA":<40}{amount:0>21}{nationality}{id_digits:0>9}{print_name:<40}{bank_code}{bank_name:<40}{bank_acc}{description:<25}{"NO APLICA":<40}\n'
        else:
            if payslips:
                # *** Registro de cabecera ***
                # 1. Preparacion de campos
                bank_acc = self.bank_account_id.sanitized_acc_number
                total_payroll = 0.0
                for payslip in payslips:
                    total_payroll += payslip.net_wage
                total_payroll = f"{total_payroll:.2f}".replace(".", "")
                if len(total_payroll) > 15:
                    raise ValidationError(
                        "El monto total de la nomina excede la cantidad maxima de digitos."
                    )

                if self.env.company.partner_id.vat:
                    nationality = self.env.company.partner_id.vat[:1].upper()
                    vat_digits = self.env.company.partner_id.vat[1::].replace("-", "")
                else:
                    nationality = ""
                    vat_digits = ""

                # 2. Construccion de linea
                # Header
                txt_data += "HDRBANESCO        ED  95BPAYMULP\n"
                txt_data += "01SAL"
                txt_data += " " * 32
                txt_data += "9  "
                txt_data += f"{self.name:<35}"
                timezone = pytz.timezone(self.env.context.get("tz") or self.env.user.tz)
                date = datetime.now(timezone)
                txt_data += date.strftime("%Y%m%d%H%M%S")
                txt_data += "\n"
                # débito
                txt_data += "02"
                txt_data += f"{self.name:0>8}" + " " * 22
                txt_data += nationality.upper() + f"{vat_digits:<16}"
                txt_data += f"{self.env.company.partner_id.name:<35}"
                txt_data += f"{total_payroll:0>15}"
                txt_data += "VES "
                txt_data += f"{bank_acc:<34}"
                txt_data += "BANESCO    "
                txt_data += self.valid_date.strftime("%Y%m%d") + "\n"

                # Créditos
                for payslip in payslips:
                    # *** Registro detalle ***
                    txt_data += self._txt_prepare_data_banesco(payslip) + "\n"

                # Totales
                txt_data += "06"
                txt_data += f"{1:0>15}"
                txt_data += f"{len(payslips):0>15}"
                txt_data += f"{total_payroll:0>15}"

        txt_data = txt_data.rstrip("\n")
        return txt_data

    def _txt_prepare_data_vzla(self, payslip):
        if not payslip.net_wage or payslip.net_wage <= 0.0:
            raise ValidationError(
                ("Establezca un monto valido a pagar al empleado: %s.")
                % (payslip.employee_id.name)
            )

        if len(f"{payslip.net_wage:.2f}") > 15:
            raise ValidationError(
                (
                    "El monto a pagar para el empleado: %s, excede la cantidad maxima de digitos."
                )
                % (payslip.employee_id.name)
            )

        if not payslip.employee_id.country_id:
            raise ValidationError(
                ("Por favor establezca la nacionalidad del empleado: %s.")
                % (payslip.employee_id.name)
            )

        aux_txt_data = ""

        # *** Preparacion de campos ***
        employees_bank_info = self.env["hr_employee_bank_information"].search(
            [
                ("employee_id", "=", payslip.employee_id.id),
                ("is_payroll_account", "=", True),
            ]
        )

        bank_acc = employees_bank_info.bank_account_number
        amount = f"{payslip.net_wage:.2f}".replace(".", ",")
        employee = payslip.employee_id
        if not employees_bank_info.letter:
            raise ValidationError(
                f"No se encuentra configurada la Letra Calificadora en los datos bancarios del empleado {employee.name}"
            )
        nationality = employees_bank_info.letter
        id_digits = employees_bank_info.holder_account_id

        a, b = "áéíóúüÁÉÍÓÚñÑ", "aeiouuAEIOUnN"
        trans = str.maketrans(a, b)
        employee_name = employee.name.translate(trans)

        aux_txt_data += "CREDITO"
        aux_txt_data += "{:0>8}".format(payslip.number.split("/")[1])
        aux_txt_data += nationality.upper() + f"{id_digits:0<9}"
        aux_txt_data += f"{employee_name:<30}"
        aux_txt_data += (
            "00" if employees_bank_info.account_type == "current_account" else "01"
        )
        aux_txt_data += bank_acc
        aux_txt_data += f"{amount:0>18}"
        aux_txt_data += "10" if self.operation_type == "same" else 00  # Tipo de Pago
        aux_txt_data += f"{employees_bank_info.name.bic:<12}"
        aux_txt_data += "{0:<7}".format("")
        aux_txt_data += "{0:<50}".format("")

        return aux_txt_data

    def generate_vzla(self):
        # Obtener recibos de salario
        payslips = self._get_payslips()
        txt_data = ""
        if payslips:
            # *** Registro de cabecera ***

            # 1. Preparacion de campos

            bank_acc = self.bank_account_id.sanitized_acc_number
            total_payroll = 0.0
            for payslip in payslips:
                total_payroll += payslip.net_wage
            total_payroll = f"{total_payroll:.2f}".replace(".", ",")
            if len(total_payroll) > 18:
                raise ValidationError(
                    "El monto total de la nomina excede la cantidad maxima de digitos."
                )

            if self.env.company.partner_id.vat:
                nationality = self.env.company.partner_id.vat[:1].upper()
                vat_digits = self.env.company.partner_id.vat[1::].replace("-", "")
            else:
                nationality = ""
                vat_digits = ""

            # 2. Construccion de linea
            # Header
            txt_data += "HEADER"
            txt_data += f"{self.name:0>8}"
            txt_data += "{0:<8}".format("")  # CAMBIAR POR NúMERO DE NEGOCIACIÓn
            txt_data += nationality.upper() + f"{vat_digits:0<9}"
            txt_data += self.valid_date.strftime("%d/%m/%Y")
            txt_data += self.valid_date.strftime("%d/%m/%Y") + "\n"
            # Débito
            txt_data += "DEBITO"
            txt_data += f"{self.name:0>8}"
            txt_data += nationality.upper() + f"{vat_digits:0<9}"
            txt_data += f"{self.env.company.partner_id.name:<35}"
            txt_data += self.valid_date.strftime("%d/%m/%Y")
            txt_data += "00"  # Tipo de Cuenta, 00 = Corriente. 01 = Ahorro
            txt_data += bank_acc
            txt_data += f"{total_payroll:0>18}"
            txt_data += "VEF"
            txt_data += "40" + "\n"

            # Créditos
            for payslip in payslips:
                # *** Registro detalle ***
                txt_data += self._txt_prepare_data_vzla(payslip) + "\n"

            # Totales
            txt_data += "TOTAL"
            txt_data += f"{1:0>5}"
            txt_data += f"{len(payslips):0>5}"
            txt_data += f"{total_payroll:0>18}"

        return txt_data

    def _txt_prepare_data_mercantil(self, payslip):
        if not payslip.net_wage or payslip.net_wage <= 0.0:
            raise ValidationError(
                ("Establezca un monto valido a pagar al empleado: %s.")
                % (payslip.employee_id.name)
            )

        if len(f"{payslip.net_wage:.2f}") > 17:
            raise ValidationError(
                (
                    "El monto a pagar para el empleado: %s, excede la cantidad maxima de digitos."
                )
                % (payslip.employee_id.name)
            )

        if not payslip.employee_id.country_id:
            raise ValidationError(
                ("Por favor establezca la nacionalidad del empleado: %s.")
                % (payslip.employee_id.name)
            )

        aux_txt_data = ""

        # *** Preparacion de campos ***
        employees_bank_info = self.env["hr_employee_bank_information"].search(
            [
                ("employee_id", "=", payslip.employee_id.id),
                ("is_payroll_account", "=", True),
            ]
        )

        bank_acc = employees_bank_info.bank_account_number
        amount = f"{payslip.net_wage:.2f}".replace(".", "")
        employee = payslip.employee_id
        if not employees_bank_info.letter:
            raise ValidationError(
                f"No se encuentra configurada la Letra Calificadora en los datos bancarios del empleado {employee.name}"
            )
        nationality = employees_bank_info.letter.upper()
        id_digits = employees_bank_info.holder_account_id

        a, b = "áéíóúüÁÉÍÓÚñÑ", "aeiouuAEIOUnN"
        trans = str.maketrans(a, b)
        employee_name = employee.name.translate(trans)

        aux_txt_data += "2"
        aux_txt_data += nationality
        aux_txt_data += f"{id_digits:0>15}"
        aux_txt_data += "1" if self.operation_type == "same" else "3"
        aux_txt_data += "{:0>12}".format("")
        aux_txt_data += "{0:<30}".format("")
        aux_txt_data += bank_acc
        aux_txt_data += f"{amount:0>17}"
        aux_txt_data += f"{nationality + id_digits:<16}"
        aux_txt_data += "0000000222"
        aux_txt_data += "{:0>3}".format("")
        aux_txt_data += "{0:<60}".format(re.sub(r"[^A-Za-z]+", " ", employee_name))
        aux_txt_data += "{:0>15}".format("")
        aux_txt_data += "{0:<50}".format("")
        aux_txt_data += "{:0>4}".format("")
        aux_txt_data += "{0:<30}".format("")
        aux_txt_data += "{0:<80}".format("")
        aux_txt_data += "{:0>35}".format("")

        return aux_txt_data

    def generate_mercantil(self):
        # Obtener recibos de salario
        payslips = self._get_payslips()
        txt_data = ""
        if payslips:
            # *** Registro de cabecera ***

            # 1. Preparacion de campos

            bank_acc = self.bank_account_id.sanitized_acc_number
            total_payroll = 0.0
            for payslip in payslips:
                total_payroll += payslip.net_wage
            total_payroll = f"{total_payroll:.2f}".replace(".", "")
            if len(total_payroll) > 17:
                raise ValidationError(
                    "El monto total de la nomina excede la cantidad maxima de digitos."
                )

            if self.env.company.partner_id.vat:
                nationality = self.env.company.partner_id.vat[:1].upper()
                vat_digits = self.env.company.partner_id.vat[1::].replace("-", "")
            else:
                nationality = ""
                vat_digits = ""

            # 2. Construccion de linea
            # Cabecera
            txt_data += "1"
            txt_data += "{0:<12}".format("BAMRVECA")
            txt_data += f"{self.name:0>15}"
            txt_data += "NOMIN"
            txt_data += "0000000222"
            txt_data += nationality
            txt_data += f"{vat_digits:0>15}"
            txt_data += f"{len(payslips):0>8}"
            txt_data += f"{total_payroll:0>17}"
            txt_data += self.valid_date.strftime("%Y%m%d")
            txt_data += bank_acc
            txt_data += "{:0>7}".format("")
            txt_data += "{:0>8}".format("")
            txt_data += "{:0>4}".format("")
            txt_data += "{:0>8}".format("")
            txt_data += "{:0>261}".format("") + "\n"

            # Detalles
            for payslip in payslips:
                # *** Registro detalle ***
                txt_data += self._txt_prepare_data_mercantil(payslip) + "\n"

        return txt_data
