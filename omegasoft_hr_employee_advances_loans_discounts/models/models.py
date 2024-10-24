from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"  # pylint: disable=consider-merging-classes-inherited

    advances_loans_discounts_line_ids = fields.Many2many(
        comodel_name="hr_employee_advances_loans_discounts_lines",
        string="Advances loans discounts lines",
    )

    # Employee social benefits
    def _compute_advance_social_benefits(self, contract_obj):
        # Calculation of advance payment of social benefits

        advancement_bs = sum(
            line.currency_id._convert(
                line.amount,
                self.env.company.currency_id,
                self.env.company,
                line.rate_id.name or fields.Date.today(),
            )
            for line in self.advances_loans_discounts_line_ids.filtered(
                lambda x: x.type_advance_loan == "social_benefits"
                and x.advances_loans_discounts_id.state in ["open"]
            )
        )
        if advancement_bs:
            contract_obj.advances_of_social_benefits = (
                advancement_bs + contract_obj.accumulated_advances_social_benefits
            )
            contract_obj.total_available_social_benefits_generated = (
                contract_obj.social_benefits_generated
                + contract_obj.accrued_social_benefits
            ) - contract_obj.advances_of_social_benefits

    def _compute_advance_vacations(self, contract_obj):
        # Calculation of advance vacations

        advancement_bs = sum(
            line.currency_id._convert(
                line.amount,
                self.env.company.currency_id,
                self.env.company,
                line.rate_id.name or fields.Date.today(),
            )
            for line in self.advances_loans_discounts_line_ids.filtered(
                lambda x: x.type_advance_loan == "vacations"
                and x.advances_loans_discounts_id.state in ["open"]
            )
        )
        if advancement_bs:
            contract_obj.vacations_advances_granted = advancement_bs

    def _compute_advance_benefit_interest(
        self, contract_obj, advance_loans_discounts_line
    ):
        # Calculation of advance vacations

        advancement_bs = sum(
            line.currency_id._convert(
                line.amount,
                self.env.company.currency_id,
                self.env.company,
                line.rate_id.name or fields.Date.today(),
            )
            for line in advance_loans_discounts_line.filtered(
                lambda x: x.type_advance_loan == "benefit_interest"
                and x.product_employee_ids.id == self.id
            )
        )

        if advancement_bs:
            contract_obj.benefit_interest -= advancement_bs

    def _compute_advance_days_per_year(
        self, contract_obj, advance_loans_discounts_line
    ):
        # Calculation of advance vacations

        advancement_bs = sum(
            line.currency_id._convert(
                line.amount,
                self.env.company.currency_id,
                self.env.company,
                line.rate_id.name or fields.Date.today(),
            )
            for line in advance_loans_discounts_line.filtered(
                lambda x: x.type_advance_loan == "days_per_year"
                and x.product_employee_ids.id == self.id
            )
        )
        if advancement_bs:
            contract_obj.days_per_year_accumulated -= advancement_bs

    # Utilities and Advances of utilities
    def _compute_advance_granted(self, contract_obj, payslip_obj=False):
        # Calculation of Advance of utilities

        advancement_bs = sum(
            line.currency_id._convert(
                line.amount,
                self.env.company.currency_id,
                self.env.company,
                line.rate_id.name or fields.Date.today(),
            )
            for line in self.advances_loans_discounts_line_ids.filtered(
                lambda x: x.type_advance_loan == "profits"
                and x.advances_loans_discounts_id.state in ["open"]
            )
        )
        if advancement_bs:
            contract_obj.advances_granted = (
                advancement_bs + contract_obj.accumulated_advances_earnings_benefits
            )
            contract_obj.earnings_generated_total_available = (
                contract_obj.earnings_generated - contract_obj.advances_granted
            )

    def _unlink_advance_loans_discounts(
        self, contract_obj, advance_loans_discounts_line
    ):
        # Calculation of advance payment of social benefits

        type_advance_loan = advance_loans_discounts_line.mapped("type_advance_loan")
        if advance_loans_discounts_line.advances_loans_discounts_id.state in [
            "rejected"
        ]:
            if "social_benefits" in type_advance_loan:
                advancement_bs = sum(
                    line.currency_id._convert(
                        line.amount,
                        self.env.company.currency_id,
                        self.env.company,
                        line.rate_id.name or fields.Date.today(),
                    )
                    for line in advance_loans_discounts_line.filtered(
                        lambda x: x.type_advance_loan == "social_benefits"
                        and x.advances_loans_discounts_id.state in ["rejected"]
                        and x.product_employee_ids.id == self.id
                    )
                )

                contract_obj.advances_of_social_benefits -= advancement_bs
                contract_obj.total_available_social_benefits_generated = (
                    contract_obj.social_benefits_generated
                    + contract_obj.accrued_social_benefits
                ) - contract_obj.advances_of_social_benefits

            elif "profits" in type_advance_loan:
                advancement_bs = sum(
                    line.currency_id._convert(
                        line.amount,
                        self.env.company.currency_id,
                        self.env.company,
                        line.rate_id.name or fields.Date.today(),
                    )
                    for line in advance_loans_discounts_line.filtered(
                        lambda x: x.type_advance_loan == "profits"
                        and x.advances_loans_discounts_id.state in ["rejected"]
                        and x.product_employee_ids.id == self.id
                    )
                )

                contract_obj.advances_granted -= advancement_bs
                contract_obj.earnings_generated_total_available = (
                    contract_obj.earnings_generated - contract_obj.advances_granted
                )

            elif "vacations" in type_advance_loan:
                advancement_bs = sum(
                    line.currency_id._convert(
                        line.amount,
                        self.env.company.currency_id,
                        self.env.company,
                        line.rate_id.name or fields.Date.today(),
                    )
                    for line in advance_loans_discounts_line.filtered(
                        lambda x: x.type_advance_loan == "vacations"
                        and x.advances_loans_discounts_id.state in ["rejected"]
                        and x.product_employee_ids.id == self.id
                    )
                )

                contract_obj.vacations_advances_granted -= advancement_bs

            elif "benefit_interest" in type_advance_loan:
                advancement_bs = sum(
                    line.currency_id._convert(
                        line.amount,
                        self.env.company.currency_id,
                        self.env.company,
                        line.rate_id.name or fields.Date.today(),
                    )
                    for line in advance_loans_discounts_line.filtered(
                        lambda x: x.type_advance_loan == "benefit_interest"
                        and x.advances_loans_discounts_id.state in ["rejected"]
                        and x.product_employee_ids.id == self.id
                    )
                )

                contract_obj.benefit_interest += advancement_bs

            elif "days_per_year" in type_advance_loan:
                advancement_bs = sum(
                    line.currency_id._convert(
                        line.amount,
                        self.env.company.currency_id,
                        self.env.company,
                        line.rate_id.name or fields.Date.today(),
                    )
                    for line in advance_loans_discounts_line.filtered(
                        lambda x: x.type_advance_loan == "days_per_year"
                        and x.advances_loans_discounts_id.state in ["rejected"]
                        and x.product_employee_ids.id == self.id
                    )
                )

                contract_obj.days_per_year_accumulated += advancement_bs
            else:
                pass
