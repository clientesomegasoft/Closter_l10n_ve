from dateutil.relativedelta import MO, relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class HrEmployeeAdvancesLoansDiscountsLines(models.Model):
    _name = "hr_employee_advances_loans_discounts_lines"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin"]
    _description = "Employee Advances, loans and discounts lines"

    advances_loans_discounts_id = fields.Many2one(
        comodel_name="hr_employee_advances_loans_discounts",
        string="Employee Advances, loans and discounts",
        tracking=True,
        ondelete="restrict",
    )
    date_issue = fields.Date(related="advances_loans_discounts_id.date_issue")

    employee_ids = fields.Many2many(related="advances_loans_discounts_id.employee_ids")

    product_employee_ids = fields.Many2many(
        string="Employees product",
        comodel_name="hr.employee",
        help="Employees",
        tracking=True,
    )

    type_advance_loan = fields.Selection(
        string="Products",
        help="Types of advances, loans that exist in the company",
        selection=[
            ("loan", "Loan"),
            ("discount", "Discount"),
            ("social_benefits", "Social benefits"),
            ("per_diem", "Per diem"),
            ("vacations", "Vacations"),
            ("profits", "Profits"),
            ("benefit_interest", "Benefit interest"),
            ("days_per_year", "Days per year"),
            ("others", "Others"),
        ],
        tracking=True,
    )

    description = fields.Char(
        string="description", help="Brief description of the product", tracking=True
    )

    amount = fields.Float(
        string="Amount",
        help="Amount to allocate (pay) the selected product.",
        tracking=True,
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        help="Currencies active in the company",
        tracking=True,
        ondelete="restrict",
        default=lambda self: self.env.company.currency_id,
    )

    exceeds_maximum = fields.Boolean(
        string="Exceeds the maximum?",
        help="""When active, the system will not consider the
        limits of the amount of the advance payment.""",
        tracking=True,
    )

    rate_id = fields.Many2one(related="advances_loans_discounts_id.rate_id")
    rate_amount = fields.Float(related="rate_id.inverse_company_rate")

    fees = fields.Float(
        string="Fees", tracking=True, help="number of installments to be discounted."
    )
    fee_amount = fields.Float(
        string="Fees Amount",
        tracking=True,
        help="Amount of installments to be discounted.",
    )
    discount_start_date = fields.Date(
        string="Discount start date", tracking=True, help="Discount start date"
    )
    discount_end_date = fields.Date(
        string="Discount end date", tracking=True, help="Discount end date"
    )
    discount_state = fields.Selection(
        string="Discount state",
        selection=[
            ("draft", "Draft"),
            ("open", "Open"),
            ("paid", "Paid"),
            ("rejected", "Rejected"),
        ],
        tracking=True,
        help="Discount state",
        default="draft",
    )

    @api.model_create_multi
    def create(self, values):
        res = super(__class__, self).create(values)
        res.discount_state = "draft"
        return res

    def unlink(self):
        for record in self:
            if record.discount_state != "draft":
                raise ValidationError(
                    _("Las lineas solo pueden ser eliminadas en estado borrador")
                )
        res = super(__class__, self).unlink()
        return res

    @api.onchange("product_employee_ids")
    def _check_product_employee_ids(self):
        if len(self.product_employee_ids) > 1:
            raise ValidationError(
                _("Los anticipos por empleado sólo aceptan un máximo de 1 empleado")
            )

    def _should_check_amount(self):
        return (
            self.product_employee_ids
            and self.amount
            and self.product_employee_ids.contract_id
            and self.type_advance_loan
            in [
                "profits",
                "social_benefits",
                "benefit_interest",
                "days_per_year",
            ]
        )

    @api.constrains("currency_id", "amount")
    @api.onchange("currency_id", "amount")
    def _check_amount(self):
        for record in self:
            if not record._should_check_amount():
                continue

            current_contract = record.product_employee_ids.contract_id
            employee = record.product_employee_ids
            rate_id = record.rate_id or fields.Date.today()
            currency_id = current_contract.company_id.currency_id

            advancement = record.currency_id._convert(
                record.amount, currency_id, current_contract.company_id, rate_id
            )
            # Normalize webclient precision errors:
            advancement = round(advancement, currency_id.decimal_places)

            available = employee._get_employee_available_benefits(
                record.type_advance_loan, currency_id, rate_id
            )
            available_limit = available.available_benefits_amount_limit

            # These amounts were rounded before, so it's safe to perform this comparison
            if (
                not record.exceeds_maximum
                and currency_id.compare_amounts(advancement, available_limit) == 1
            ):
                ERROR_DETAILS = {
                    "profits": _("sus utilidades"),
                    "social_benefits": _(
                        "75{} del monto total de las prestaciones disponibles"
                    ).format("%"),
                    "benefit_interest": _("sus intereses prestacionales"),
                    "days_per_year": _("sus días por año"),
                }

                raise ValidationError(
                    _(
                        "El monto {advancement} del anticipo para ({employee}) no debe "
                        "ser superior a {details}: {available:,.2f}".format(
                            advancement=advancement,
                            employee=", ".join(
                                record.product_employee_ids.mapped("name")
                            ),
                            details=ERROR_DETAILS.get(record.type_advance_loan, ""),
                            available=available_limit,
                        )
                    )
                )

    @api.onchange("fees")
    def _compute_fees_amount(self):
        for record in self:
            if record.fees and record.fees <= 0:
                raise ValidationError(_("La cantidad de cuotas debe ser mayor a Cero"))
            elif record.fees:
                record.fee_amount = record.amount / record.fees

    @api.onchange("discount_start_date", "fees")
    def _compute_discount_end_date(self):
        for record in self:
            pay_structure = " "
            if (
                record.product_employee_ids
                and record.fees
                and record.discount_start_date
            ):
                start_date = record.discount_start_date
                # Obtaining the employee's pay structure

                if record.type_advance_loan in ["discount", "loan"]:
                    pay_structure = (
                        record.product_employee_ids.contract_id.structure_loan_discount.schedule_pay
                        if record.product_employee_ids.contract_id.structure_loan_discount
                        else False
                    )
                    if not pay_structure:
                        raise UserError(
                            _(
                                "Indicate the structure for loans and "
                                "discounts from the employee contract"
                            )
                        )

                else:
                    pay_structure = record.product_employee_ids.contract_id.structure_type_id.default_schedule_pay

                # Quincenal
                if pay_structure == "bi-weekly":
                    if record.discount_start_date.day <= 15:
                        start_date = start_date + relativedelta(
                            days=-record.discount_start_date.day + 1
                        )
                    else:
                        start_date = start_date + relativedelta(
                            days=15 - record.discount_start_date.day
                        )
                    record.discount_end_date = start_date + relativedelta(
                        weeks=record.fees * 2
                    )
                # Semanal
                elif pay_structure == "weekly":
                    start_date = start_date + relativedelta(weekday=MO(-1))
                    record.discount_end_date = start_date + relativedelta(
                        weeks=record.fees
                    )
                # Mensual
                elif pay_structure == "monthly":
                    record.discount_end_date = start_date + relativedelta(
                        months=record.fees
                    )

                record.discount_end_date = (
                    record.discount_end_date + relativedelta(days=-1)
                    if pay_structure in ["weekly"]
                    else record.discount_end_date
                )

    # employee file code

    employee_file = fields.Boolean(
        "Employee file", related="advances_loans_discounts_id.employee_file"
    )
    employee_file_code_ids = fields.Many2many(
        "employee.file.code",
        relation="employee_code_loans_line_rel",
        string="Employee File",
    )

    @api.onchange("employee_file_code_ids")
    def _onchange_employee_file_code_ids(self):
        if self.employee_file:
            if (
                self.employee_file_code_ids
                and self.employee_file_code_ids.employee_id.ids
                != self.product_employee_ids.ids
            ):
                self.product_employee_ids = [
                    (6, 0, self.employee_file_code_ids.employee_id.ids)
                ]
            elif not self.employee_file_code_ids and self.product_employee_ids:
                self.product_employee_ids = [(6, 0, [])]

    @api.onchange("product_employee_ids")
    def _onchange_employee(self):
        if self.employee_file:
            if (
                self.product_employee_ids
                and self.product_employee_ids.ids
                != self.employee_file_code_ids.employee_id.ids
            ):
                self.employee_file_code_ids = [
                    (6, 0, self.product_employee_ids.employee_file_code_id.ids)
                ]
            elif not self.product_employee_ids and self.employee_file_code_ids:
                self.employee_file_code_ids = [(6, 0, [])]

    @api.constrains("employee_file_code_ids")
    def _constrains_employee_file_code_ids(self):
        for record in self:
            if record.employee_file:
                if not record._context.get("bypass", False):
                    if (
                        record.employee_file_code_ids
                        and record.employee_file_code_ids.employee_id.ids
                        != record.product_employee_ids.ids
                    ):
                        record.product_employee_ids = [
                            (6, 0, record.employee_file_code_ids.employee_id.ids)
                        ]
                    elif (
                        not record.employee_file_code_ids
                        and record.product_employee_ids
                    ):
                        record.product_employee_ids = [(6, 0, [])]

    @api.constrains("product_employee_ids")
    def _constrains_employee(self):
        for record in self:
            if record.employee_file:
                if (
                    record.product_employee_ids
                    and record.product_employee_ids.ids
                    != record.employee_file_code_ids.employee_id.ids
                ):
                    record.employee_file_code_ids = [
                        (6, 0, record.product_employee_ids.employee_file_code_id.ids)
                    ]
                elif not record.product_employee_ids and record.employee_file_code_ids:
                    record.employee_file_code_ids = [(6, 0, [])]

    # employee file code
