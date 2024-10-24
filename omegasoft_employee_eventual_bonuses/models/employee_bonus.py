from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrEmployeeBonus(models.Model):
    _name = "hr_employee_bonus"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin"]
    _description = "Employee bonus"
    _order = "date desc, amount desc"

    name = fields.Selection(
        string="Type",
        selection=[
            ("toy_voucher", "Toy voucher"),
            ("christmas_bonus", "Christmas Bonus"),
            ("school_voucher", "School voucher"),
            ("birth_bonus", "Birth Bonus"),
        ],
        tracking=True,
    )

    active = fields.Boolean(
        default=True,
        help="Set active to false to hide the children tag without removing it.",
    )

    description = fields.Char(
        string="Description",
        help="specific reference to the bonus payment.",
        tracking=True,
    )

    state = fields.Selection(
        string="State",
        selection=[
            ("new", "New"),
            ("draft", "Draft"),
            ("assigned", "Assigned"),
            ("cancel", "Rejected"),
        ],
        default="new",
        tracking=True,
    )

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        default=lambda self: self.env.company,
        ondelete="restrict",
        tracking=True,
    )

    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        default=lambda self: self.env.company.currency_id,
        ondelete="restrict",
        tracking=True,
    )

    amount = fields.Monetary(string="Amount", tracking=True)

    date = fields.Date(string="Date", default=fields.Date.context_today, tracking=True)

    minimum_age = fields.Integer(string="Minimum age", tracking=True)

    type_minimum_age = fields.Selection(
        string="Type minimum age",
        selection=[("days", "Days"), ("months", "Months"), ("years", "Years")],
        tracking=True,
    )

    maximum_age = fields.Integer(string="Maximum age", tracking=True)

    type_maximum_age = fields.Selection(
        string="Type maximum age",
        selection=[("days", "Days"), ("months", "Months"), ("years", "Years")],
        tracking=True,
    )

    study_level = fields.Selection(
        string="Study level",
        selection=[
            ("maternal", "Maternal"),
            ("elementary_school", "Elementary school"),
            ("high_school", "High School"),
            ("university", "University"),
        ],
        tracking=True,
    )

    bonus_line_ids = fields.One2many(
        string="Bonus line",
        comodel_name="hr_employee_bonus_line",
        inverse_name="bonus_id",
    )

    company_currency = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.company.currency_id
    )
    currency_ref_id = fields.Many2one(related="company_id.currency_ref_id")
    rate_id = fields.Many2one(
        "res.currency.rate",
        string="Rate",
        tracking=True,
        default=lambda self: self.env.company.currency_ref_id.rate_ids.filtered(
            lambda aml: aml.is_payroll_rate
        ).sorted("name")[-1],
        domain="[('is_payroll_rate', '=', True)]",
    )

    @api.constrains("amount")
    def _constrain_amount(self):
        if self.amount <= 0:
            raise ValidationError(_("El monto debe ser mayor a cero."))

    @api.constrains("maximum_age")
    def _constrain_maximum_age(self):
        if self.maximum_age <= 0 and self.name in ["toy_voucher", "birth_bonus"]:
            raise ValidationError(_("La Edad máxima debe ser mayor a cero."))

    def name_get(self):
        msj = []
        for record in self:
            if record:
                if record.name == "toy_voucher":
                    name = "Bono de Juguete" + " - " + str(record.date)
                elif record.name == "christmas_bonus":
                    name = "Bono Navideño" + " - " + str(record.date)
                elif record.name == "school_voucher":
                    name = "Bono Escolar" + " - " + str(record.date)
                elif record.name == "birth_bonus":
                    name = "Bono Nacimiento" + " - " + str(record.date)
                msj.append((record.id, name))
                name = " "
        return msj

    @api.onchange("name")
    def _onchange_name(self):
        for record in self:
            record.study_level = False
            record.minimum_age = False
            record.type_minimum_age = False
            record.maximum_age = False
            record.type_maximum_age = False

    @api.onchange("type_maximum_age")
    def _onchange_maximum_age(self):
        for record in self:
            # Express ages in months
            aux_minimum_age = record.minimum_age
            aux_maximum_age = record.maximum_age

            if record.type_minimum_age == "days":
                aux_minimum_age = int(record.minimum_age * 0.0329)
            elif record.type_minimum_age == "years":
                aux_minimum_age = record.minimum_age * 1

            if record.type_maximum_age == "days":
                aux_maximum_age = record.maximum_age * 0.0329
            elif record.type_maximum_age == "years":
                aux_maximum_age = record.maximum_age * 12
            if aux_maximum_age < aux_minimum_age:
                raise ValidationError(
                    _("La edad máxima no debe ser inferior a la edad mínima.")
                )

    def _clean_lines(self):
        for record in self.bonus_line_ids:
            record.unlink()

    def _search_employees(self, is_schooll_voucher=False):
        self._clean_lines()
        employee_obj = (
            self.env["hr.employee"]
            .search([])
            .filtered(lambda x: x.contract_id.state in ["open"])
        )
        employee_list = []
        bonus_lines = []
        if self.name in ["toy_voucher", "school_voucher", "birth_bonus"]:
            # look for employees whose children's age (if any)
            # is within the range of the minimum and maximum
            # bonus age.
            children_list = []
            aux_minimum_age = self.minimum_age
            aux_maximum_age = self.maximum_age
            for employee in employee_obj.filtered(lambda x: x.family_information_ids):
                for child in employee.family_information_ids.filtered(
                    lambda x: x.relationship in ["son", "daughter"]
                ):
                    aux_child_age = child.age

                    # Express ages in months
                    # (0.329) represents the factor to take from days to months
                    if child.type_age == "days":
                        aux_child_age = int(child.age * 0.0329)
                    elif child.type_age == "years":
                        aux_child_age = child.age * 12

                    if self.type_minimum_age == "days":
                        aux_minimum_age = int(self.minimum_age * 0.0329)
                    elif self.type_minimum_age == "years":
                        aux_minimum_age = self.minimum_age * 12

                    if self.type_maximum_age == "days":
                        aux_maximum_age = self.maximum_age * 0.0329
                    elif self.type_maximum_age == "years":
                        aux_maximum_age = self.maximum_age * 12

                    if not is_schooll_voucher:
                        # Toy voucher
                        children_list.append(
                            aux_child_age >= aux_minimum_age
                            and aux_child_age <= aux_maximum_age
                        )
                    else:
                        # School voucher
                        children_list.append(child.study_level == self.study_level)
                if any(children_list):
                    bonus_lines.append(
                        {
                            "bonus_id": self.id,
                            "employee_id": employee.id,
                            "employee_bonus_amount": children_list.count(True)
                            * self.currency_id._convert(
                                self.amount,
                                self.env.company.currency_id,
                                self.env.company,
                                self.rate_id.name or fields.Date.today(),
                            )
                            if self.rate_id.name
                            else self.amount,
                        }
                    )
                    employee_list.append(employee.id)
                children_list.clear()
        elif self.name in ["christmas_bonus"]:
            # Sundry bonds
            for employee in employee_obj:
                bonus_lines.append(
                    {
                        "bonus_id": self.id,
                        "employee_id": employee.id,
                        "employee_bonus_amount": self.currency_id._convert(
                            self.amount,
                            self.env.company.currency_id,
                            self.env.company,
                            self.rate_id.name or fields.Date.today(),
                        )
                        if self.rate_id.name
                        else self.amount,
                    }
                )
            employee_list = employee_obj.mapped("id")

        # Employees whose children's age (if any)
        # is within the minimum and maximum bonus age range.
        if employee_list:
            self.env["hr_employee_bonus_line"].create(bonus_lines)
            self.write({"state": "draft"})
        else:
            pass

    def search_employees(self):
        # TODO: Clear the entered information if you have changed
        # the type of voucher, which was entered the first time.
        if self.name == "school_voucher":
            # School voucher
            self._search_employees(True)
        elif self.name == "birth_bonus":
            self._search_employees(True)
        else:
            self._search_employees()

    def action_confirm(self):
        self.write({"state": "assigned"})

    def action_cancel(self):
        self._clean_lines()
        self.write({"state": "cancel"})

    def action_draft(self):
        self._clean_lines()
        self.write({"state": "draft"})
