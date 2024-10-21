import re

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    banavih_code = fields.Char(string="Código Banavih")


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    banavih_code = fields.Char(related="company_id.banavih_code", readonly=False)


class ExportBankPaymentsBanavih(models.Model):
    _inherit = "export.bank.payments"
    _description = "Exportar pagos de nomina banavih"

    type_trans = fields.Selection(selection_add=[("fiscal", " Banavih")])

    def action_done(self):
        """Exportar el documento en texto plano."""
        self.ensure_one()
        data = ""

        if (
            self.bank_account_id.sanitized_acc_number
            and len(self.bank_account_id.sanitized_acc_number) != 20
        ):
            raise ValidationError(
                _(
                    "La longitud del número de cuenta de "
                    "la compañia debe ser de 20 dígitos."
                )
            )

        elif self.bank_account_id and not self.bank_account_id.is_payroll_account:
            raise ValidationError(
                _(
                    "La cuenta de la compañia debe estar "
                    "configurada como 'Cuenta de Nomina'."
                )
            )

        if (
            self.env.company.partner_id.partner_type != "other"
            and not self.env.company.partner_id.vat
        ):
            raise ValidationError(_("Por favor establezca el RIF de la compañia."))

        if self.type_trans == "fiscal":
            root = self.generate_fiscal_payroll()
            fiscal_code = (
                fields.Date.today().strftime("%-d")
                + f"{self.date_end.month:0>2}"
                + str(self.date_end.year)
            )
            banavih_code = self.env.company.banavih_code
            if not banavih_code:
                raise ValidationError(
                    _(
                        "No se encuentra configurado un Código de Identificación Banavih!"
                    )
                )
            data, filename = self._write_attachment(
                root, banavih_code + fiscal_code, False
            )
        else:
            return super(__class__, self).action_done()

        if not data:
            raise ValidationError(
                _("No se pudo generar el archivo. Intente de nuevo con otro periodo.")
            )
        return self.write({"state": "done"})

    def _get_import_total_by_employee(self):
        domain = [
            ("slip_id.contract_id.housing_policy_law", "=", True),
            ("slip_id.date_from", ">=", self.date_start),
            ("slip_id.date_to", "<=", self.date_end),
            ("slip_id.move_id.state", "=", "posted"),
            ("category_id.code", "in", ["BASIC", "BASIC3"]),
        ]

        fields = ["employee_id", "total :sum"]
        groupby = ["employee_id"]
        group_data = self.env["hr.payslip.line"].read_group(domain, fields, groupby)

        employees_data = {p["employee_id"][0]: p["total"] for p in group_data}

        return employees_data

    def _fiscal_payroll_validations(self, employee, totals):
        if not employee.country_id:
            raise ValidationError(
                (_("Por favor establezca la nacionalidad del empleado: %s."))
                % (employee.name)
            )
        if not employee.identification_id:
            raise ValidationError(
                (_("Por favor establezca la C.I. para el empleado: %s."))
                % (employee.name)
            )
        elif not employee.identification_id[2:].isnumeric():
            raise ValidationError(
                (_("La C.I. del empleado: %s, debe contener solo números."))
                % (employee.name)
            )
        elif 5 < len(employee.identification_id[2:]) > 8:
            raise ValidationError(
                (
                    _(
                        "La C.I. del empleado: %s, debe tener "
                        "una longitud entre 5 y 8 dígitos."
                    )
                )
                % (employee.name)
            )
        words = employee.name.split(" ")
        names = tuple(filter(lambda x: x != "", words))
        if len(names) < 2:
            raise ValidationError(
                (_("El empleado: %s, debe tener almenos un nombre y un apellido."))
                % (employee.name)
            )
        elif len(names) == 2:
            # Se asume que se trata del primer nombre y aprimer pellido
            if not (1 < len(names[0]) < 26):
                raise ValidationError(
                    (
                        _(
                            "El primer nombre del empleado: %s, debe tener "
                            "una longitud entre 2 y 25 caracteres."
                        )
                    )
                    % (employee.name)
                )
            if not (1 < len(names[1]) < 26):
                raise ValidationError(
                    (
                        _(
                            "El primer apellido del empleado: %s, debe tener "
                            "una longitud entre 2 y 25 caracteres."
                        )
                    )
                    % (employee.name)
                )
        elif len(names) == 3:
            # Se asume que se trata de primer nombre,
            # primer apellido y un segundo apellido
            if not (1 < len(names[0]) < 26):
                raise ValidationError(
                    (
                        _(
                            "El primer nombre del empleado: %s, debe tener "
                            "una longitud entre 2 y 25 caracteres."
                        )
                    )
                    % (employee.name)
                )
            if not (1 < len(names[1]) < 26):
                raise ValidationError(
                    (
                        _(
                            "El primer apellido del empleado: %s, debe tener "
                            "una longitud entre 2 y 25 caracteres."
                        )
                    )
                    % (employee.name)
                )
        else:
            # Se asume que las primeras 4 palabras son el primer nombre,
            # segundo nombre, primer apellido, segundo apellido
            if not (1 < len(names[0]) < 26):
                raise ValidationError(
                    (
                        _(
                            "El primer nombre del empleado: %s, debe tener "
                            "una longitud entre 2 y 25 caracteres."
                        )
                    )
                    % (employee.name)
                )
            if not (1 < len(names[2]) < 26):
                raise ValidationError(
                    (
                        _(
                            "El primer apellido del empleado: %s, debe tener "
                            "una longitud entre 2 y 25 caracteres."
                        )
                    )
                    % (employee.name)
                )
        if totals[employee.id] <= 0:
            raise ValidationError(
                (
                    _(
                        "La sumatoria de los montos totales de las lineas con "
                        "categoria 'Básico' y 'Basico3' en los Recibos de Salario "
                        "del empleado: %s, debe ser un monto mayor que cero."
                    )
                )
                % (employee.name)
            )
        elif len(f"{totals[employee.id]:.2f}".replace(".", "")) > 18:
            raise ValidationError(
                (
                    _(
                        "La sumatoria de los montos totales de las lineas con "
                        "categoria 'Básico' y 'Basico3' en los Recibos de Salario "
                        "del empleado: %s, no debe tener mas de 18 digitos."
                    )
                )
                % (employee.name)
            )
        if not employee.contract_id.date_start:
            raise ValidationError(
                (_("Por establecer la fecha de inicio de contrato del empleado:"))
                % (employee.name)
            )

    def _remove_accents(self, s):
        s = re.sub(r"[àáâãäå]", "a", s)
        s = re.sub(r"[èéêë]", "e", s)
        s = re.sub(r"[ìíîï]", "i", s)
        s = re.sub(r"[òóôõö]", "o", s)
        s = re.sub(r"[ùúûü]", "u", s)
        return s

    def generate_fiscal_payroll(self):
        txt_data = ""
        totals = self._get_import_total_by_employee()
        ids = [k for k in totals]
        employees = self.env["hr.employee"].search([("id", "in", ids)])
        i = 0
        identification_ids = []
        for employee in employees:
            # Validaciones
            if employee.identification_id in identification_ids:
                raise ValidationError(
                    (
                        _(
                            "La cedula de identidad del empleado %s, se "
                            "encuentra duplicada en el archivo a generar."
                        )
                    )
                    % (employee.name)
                )
            else:
                identification_ids.append(employee.identification_id)
            self._fiscal_payroll_validations(employee, totals)
            # Preparacion de campos
            nationality = "V" if employee.country_id.name == "Venezuela" else "E"
            employee_id = (
                re.search("(\d+)", employee.identification_id).group()
                if re.search("(\d+)", employee.identification_id)
                else ""
            )
            words = self._remove_accents(employee.name).upper().split(" ")
            names = tuple(filter(lambda x: x != "", words))
            second_name = ""
            second_surname = ""
            if len(names) == 2:
                first_name = names[0][:25].replace(".", "")
                first_surname = names[1][:25].replace(".", "")
            elif len(names) == 3:
                first_name = names[0][:25].replace(".", "")
                first_surname = names[1][:25].replace(".", "")
                second_surname = names[2][:25].replace(".", "")
            else:
                first_name = names[0][:25].replace(".", "")
                second_name = names[1][:25].replace(".", "")
                first_surname = names[2][:25].replace(".", "")
                second_surname = names[3][:25].replace(".", "")
            debt_amount = f"{totals[employee.id]:.2f}".replace(".", "")
            entry_date = employee.contract_id.date_start.strftime("%d%m%Y")
            exit_date = (
                employee.contract_id.date_end.strftime("%d%m%Y")
                if employee.contract_id.date_end
                else ""
            )

            # Contruccion de lineas
            txt_data += f'{nationality}{","}{employee_id}{","}{first_name}{","}{second_name}{","}'
            txt_data += f'{first_surname}{","}{second_surname}{","}{debt_amount}{","}{entry_date}{","}'
            if exit_date:
                txt_data += f"{exit_date}"
            i += 1
            if i < len(employees):
                txt_data += "\n"
        return txt_data
