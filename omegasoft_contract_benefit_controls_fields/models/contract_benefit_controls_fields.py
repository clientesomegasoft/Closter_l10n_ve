from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ContractBenefitControlField(models.Model):
    _inherit = "hr.contract"

    # Social benefits
    accumulated_social_benefits = fields.Monetary(
        string="Accumulated Social Benefits",
        help="""Indicates the amount of the opening
        balance for the Benefit Accrual to Date.""",
        tracking=True,
        currency_field="accumulated_social_benefits_currency",
    )
    accumulated_social_benefits_date = fields.Date(
        string="Date Accumulated Social Benefits"
    )
    accumulated_social_benefits_currency = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.company.currency_id
    )
    is_accumulated_social_benefits = fields.Boolean(
        string="Is accumulated social benefits"
    )
    # Advances
    accumulated_advances_social_benefits = fields.Monetary(
        string="Advances Social Benefits",
        help="Indicates the amount of the opening balance for the Benefit advances",
        tracking=True,
        currency_field="accumulated_social_benefits_currency",
    )
    is_accumulated_advances_social_benefits = fields.Boolean(
        string="Is advances social benefits"
    )

    # Interest benefits
    interest_accrued_employee_benefits = fields.Monetary(
        string="Interest on accrued employee benefits",
        help="""Indicates the amount of the initial
        balance for accrued interest benefits.""",
        tracking=True,
        currency_field="interest_accrued_employee_benefits_currency",
    )
    interest_accrued_employee_benefits_currency = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.company.currency_id
    )
    is_interest_accrued_employee_benefits = fields.Boolean(
        string="Is interest accrued employee benefits"
    )

    # Utility benefits
    accumulated_earnings_benefits = fields.Monetary(
        string="Accumulated earnings Benefits",
        help="""Indicates the amount of the opening
        balance for the Benefit Accrual to Date.""",
        tracking=True,
        currency_field="accumulated_earnings_benefits_currency",
    )
    accumulated_earnings_benefits_currency = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.company.currency_id
    )
    is_accumulated_earnings_benefits = fields.Boolean(
        string="Is accumulated social benefits"
    )
    # Advances
    accumulated_advances_earnings_benefits = fields.Monetary(
        string="Advances earnings Benefits",
        help="Indicates the amount of the opening balance for the Benefit Advances",
        tracking=True,
        currency_field="accumulated_earnings_benefits_currency",
    )
    is_accumulated_advances_earnings_benefits = fields.Boolean(
        string="Is accumulated social benefits"
    )

    # Day per year benefits
    accumulated_day_per_year_benefits = fields.Monetary(
        string="Accumulated day per year Benefits",
        help="""Indicates the amount of the opening
        balance for the Benefit Accrual to Date.""",
        tracking=True,
        currency_field="accumulated_day_per_year_benefits_currency",
    )
    accumulated_day_per_year_benefits_currency = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.company.currency_id
    )
    is_accumulated_day_per_year_benefits = fields.Boolean(
        string="Is accumulated day per year benefits"
    )

    last_social_benefits_calculation = fields.Date(
        string="Last Social Benefits Calculation",
        help="Indicates the date of the last Social Benefit payment calculation.",
    )
    last_calculation_days_per_year = fields.Date(
        string="Last calculation Days per year",
        help="Indicates the date of the last payment of days per year.",
    )

    @api.constrains("accumulated_social_benefits")
    def _check_accumulated_social_benefits(self):
        module = self.env["ir.module.module"].search(
            [("name", "=", "omegasoft_contract_social_benefit_liabilities_fields")]
        )
        for record in self:
            if record.accumulated_social_benefits < 0:
                raise ValidationError(
                    _("El monto para las Prestaciones Sociales "
                    "Acumuladas debe ser superior a cero.")
                )
            elif (
                module
                and module.state == "installed"
                and record.accumulated_social_benefits
                and record.accumulated_social_benefits_date
            ):
                record.is_accumulated_social_benefits = True
                record.accrued_social_benefits += record.accumulated_social_benefits
                record.total_available_social_benefits_generated = (
                    record.social_benefits_generated + record.accrued_social_benefits
                ) - record.advances_of_social_benefits
            else:
                pass

    @api.constrains("interest_accrued_employee_benefits")
    def _check_interest_accrued_employee_benefits(self):
        module = self.env["ir.module.module"].search(
            [("name", "=", "omegasoft_contract_social_benefit_liabilities_fields")]
        )
        for record in self:
            if record.interest_accrued_employee_benefits < 0:
                raise ValidationError(
                    _("El monto para las Prestaciones Sociales "
                    "Acumuladas debe ser superior a cero.")
                )
            elif (
                module
                and module.state == "installed"
                and record.interest_accrued_employee_benefits
            ):
                record.is_interest_accrued_employee_benefits = True
                record.benefit_interest += record.interest_accrued_employee_benefits
            else:
                pass

    @api.constrains("accumulated_advances_social_benefits")
    def _check_accumulated_advances_social_benefits(self):
        module = self.env["ir.module.module"].search(
            [("name", "=", "omegasoft_contract_social_benefit_liabilities_fields")]
        )
        for record in self:
            if record.accumulated_advances_social_benefits < 0:
                raise ValidationError(
                    _("El monto para los Anticipos Sociales "
                    "Acumuladas debe ser superior a cero.")
                )
            elif (
                module
                and module.state == "installed"
                and record.accumulated_advances_social_benefits
            ):
                record.is_accumulated_advances_social_benefits = True
                record.advances_of_social_benefits += (
                    record.accumulated_advances_social_benefits
                )
                record.total_available_social_benefits_generated = (
                    record.social_benefits_generated + record.accrued_social_benefits
                ) - record.advances_of_social_benefits
            else:
                pass

    @api.constrains("accumulated_earnings_benefits")
    def _check_accumulated_earnings_benefits(self):
        module = self.env["ir.module.module"].search(
            [("name", "=", "omegasoft_contract_social_benefit_liabilities_fields")]
        )
        for record in self:
            if record.accumulated_earnings_benefits < 0:
                raise ValidationError(
                    _("El monto para los Anticipos Sociales "
                    "Acumuladas debe ser superior a cero.")
                )
            elif (
                module
                and module.state == "installed"
                and record.accumulated_earnings_benefits
            ):
                record.is_accumulated_earnings_benefits = True
                record.earnings_generated += record.accumulated_earnings_benefits
                record.earnings_generated_total_available = (
                    record.earnings_generated - record.advances_granted
                )
            else:
                pass

    @api.constrains("accumulated_advances_earnings_benefits")
    def _check_accumulated_advances_earnings_benefits(self):
        module = self.env["ir.module.module"].search(
            [("name", "=", "omegasoft_contract_social_benefit_liabilities_fields")]
        )
        for record in self:
            if record.accumulated_advances_earnings_benefits < 0:
                raise ValidationError(
                    _("El monto para los Anticipos Sociales "
                    "Acumuladas debe ser superior a cero.")
                )
            elif (
                module
                and module.state == "installed"
                and record.accumulated_advances_earnings_benefits
            ):
                record.is_accumulated_advances_earnings_benefits = True
                record.advances_granted += record.accumulated_advances_earnings_benefits
                record.earnings_generated_total_available = (
                    record.earnings_generated - record.advances_granted
                )
            else:
                pass

    @api.constrains("accumulated_day_per_year_benefits")
    def _check_accumulated_day_per_year_benefits(self):
        module = self.env["ir.module.module"].search(
            [("name", "=", "omegasoft_contract_social_benefit_liabilities_fields")]
        )
        for record in self:
            if record.accumulated_day_per_year_benefits < 0:
                raise ValidationError(
                    _("El monto para los Anticipos Sociales "
                    "Acumuladas debe ser superior a cero.")
                )
            elif (
                module
                and module.state == "installed"
                and record.accumulated_day_per_year_benefits
            ):
                record.is_accumulated_day_per_year_benefits = True
                record.days_per_year_accumulated += (
                    record.accumulated_day_per_year_benefits
                )
            else:
                pass
