from dateutil.relativedelta import relativedelta

from odoo import fields, models

PERIOD_DATES = [
    (5, 4),  # April
    (5, 7),  # July
    (5, 10),  # October
    (5, 1),  # January
]


class SocialBenefit(models.Model):
    _inherit = "hr.contract"  # pylint: disable=consider-merging-classes-inherited

    most_recent_spd = fields.Date(help="Most recent SPD payment")
    employee_accrued_benefits_date = fields.Date(
        string="Date of accrued benefits", help="Date of accrued benefits"
    )
    employee_additional_days = fields.Integer(help="Additional days", default=0)

    # Social benefits
    def _social_benefits(self):  # noqa: C901
        employee_obj = (
            self.env["hr.employee"]
            .search([("active", "=", True)])
            .filtered(
                lambda self: self.contract_id.state == "open"
                and self.contracts_count >= 1
            )
        )
        for employee in employee_obj:
            # Searching for the employee's payroll that is in paid status.
            payslip_obj = self.env["hr.payslip"].search(
                [("employee_id", "=", employee.id), ("state", "in", ["done", "paid"])],
                order="create_date desc",
            )

            current_contract = self._get_current_contract(employee)

            if (
                current_contract
                and payslip_obj
                and current_contract.date_start
                and not current_contract.date_end
            ):
                today = fields.Date.from_string(fields.Date.today())

                if payslip_obj:
                    payslip = payslip_obj[0]
                    # Step 1: Calculation of the monthly salary benefits
                    if payslip.payslip_run_id:
                        rate_date = (
                            payslip.payslip_run_id.rate_id.name
                            if payslip.payslip_run_id.rate_id
                            else fields.Date.today()
                        )
                    else:
                        rate_date = (
                            payslip.rate_id.name
                            if payslip.rate_id
                            else fields.Date.today()
                        )

                    salaray_bs = 0
                    if current_contract.wage_type == "monthly":
                        salaray_bs = current_contract.custom_wage_currency._convert(
                            current_contract.wage,
                            self.env.company.currency_id,
                            self.env.company,
                            rate_date or fields.Date.today(),
                        )
                    else:
                        salaray_bs = (
                            current_contract.custom_hourly_wage_currency._convert(
                                current_contract.hourly_wage,
                                self.env.company.currency_id,
                                self.env.company,
                                rate_date or fields.Date.today(),
                            )
                        )

                    # Step 2: Calculation of the daily salary benefits
                    # 2.1: Bring the employee's payroll that is in a paid status:

                    # 2.1.1: Seniority equal to 3 months. If the age is the same
                    # to 3 months, the query must bring the payrolls that are in
                    # paid status of the last 3 months, filtered by the rule
                    # salary SDP (Daily salary benefits).

                    # 2.1.2: Seniority greater than 3 months. If the seniority is
                    # greater to 3 months and also 3 months have passed since the
                    # last calculation of SDP. The query must bring all the payrolls
                    # paid for the last 3 months, filtered by the salary rule SDP
                    # (Daily salary benefits).

                    # 2.2: Of all the paid payrolls that result from the query,
                    # add the total amounts of all the lines.

                    # 2.1.2: Seniority greater than or equal to 3 months.
                    sdp_list = []
                    if (
                        (
                            int(current_contract.months_of_seniority) >= 1
                            and self.env.company.selection_type_date_benefit
                            == "calendar_date"
                        )
                        or (
                            int(current_contract.months_of_seniority) >= 3
                            and self.env.company.selection_type_date_benefit
                            == "contract_start_date"
                        )
                        or (int(current_contract.years_of_seniority) >= 1)
                    ):
                        # Is there a previous sdp calculation?
                        if current_contract.most_recent_spd:
                            # Number of months since the last sdp calculation
                            last_sdp_calculation = relativedelta(
                                today, current_contract.most_recent_spd
                            )

                            # Has it been 3 months since the last calculation of sdp?
                            if (
                                last_sdp_calculation.years == 0
                                and last_sdp_calculation.months == 3
                            ):
                                # Start and end of the last 3 months
                                start_last_3_months = current_contract.most_recent_spd
                                end_last_3_months = today

                                # Most recent calculation of SDP
                                current_contract.most_recent_spd = today

                                # Salaries paid in the last three months
                                sdp_list = payslip_obj.filtered(
                                    lambda x: (
                                        (
                                            x.date_from >= start_last_3_months
                                            and x.date_from < end_last_3_months
                                        )
                                        and (
                                            x.date_to > start_last_3_months
                                            and x.date_to <= end_last_3_months
                                        )
                                    )
                                )
                            else:
                                pass
                        else:  # This is your first calculation of spd
                            if (
                                self.env.company.selection_type_date_benefit
                                == "contract_start_date"
                            ):
                                # Most recent calculation of SDP
                                current_contract.most_recent_spd = (
                                    current_contract.accumulated_social_benefits_date
                                    or current_contract.date_start
                                )
                                next_three_months = (
                                    current_contract.most_recent_spd
                                    + relativedelta(months=3)
                                )

                                # Salaries paid for the last three months
                                sdp_list = payslip_obj.filtered(
                                    lambda x: (
                                        (
                                            x.date_from
                                            >= current_contract.most_recent_spd
                                            and x.date_from < next_three_months
                                        )
                                        and (
                                            x.date_to > current_contract.most_recent_spd
                                            and x.date_to <= next_three_months
                                        )
                                    )
                                )
                                current_contract.most_recent_spd = next_three_months

                            elif (
                                self.env.company.selection_type_date_benefit
                                == "calendar_date"
                            ):
                                if any(
                                    today.day == day and today.month == month
                                    for day, month in PERIOD_DATES
                                ):
                                    # Most recent calculation of SDP
                                    current_contract.most_recent_spd = (
                                        current_contract.accumulated_social_benefits_date
                                        or (
                                            today
                                            + relativedelta(
                                                months=-current_contract.months_of_seniority
                                                if current_contract.months_of_seniority
                                                < 3
                                                and current_contract.years_of_seniority
                                                < 1
                                                else -3
                                            )
                                        )
                                    )

                                    # Salaries paid for the last three months
                                    sdp_list = payslip_obj.filtered(
                                        lambda x: (
                                            (
                                                x.date_from
                                                >= current_contract.most_recent_spd
                                                and x.date_from < today
                                            )
                                            and (
                                                x.date_to
                                                > current_contract.most_recent_spd
                                                and x.date_to.month <= today.month
                                            )
                                        )
                                    )
                                    current_contract.most_recent_spd = today

                    else:
                        pass

                    comprehensive_salary = 0
                    rule_sdp_acum = 0
                    daily_wage = 0
                    aliquot_profits = 0
                    aliquot_holidays = 0
                    comprehensive_salary = 0
                    # current_contract.is_benefit_calculation_valid = False
                    if sdp_list:
                        # Sum of total amounts
                        category_for_social_benefit = (
                            self.env.company.salary_rules_category.ids
                            if self.env.company.salary_rules_category
                            else []
                        )
                        for payslip in sdp_list:
                            for line in payslip.line_ids.filtered(
                                lambda x: x.category_id.id
                                in category_for_social_benefit
                            ):
                                rule_sdp_acum += line.currency_id._convert(
                                    line.total,
                                    self.env.company.currency_id,
                                    self.env.company,
                                    payslip.rate_id.name or fields.Date.today(),
                                )

                        if current_contract.structure_type_id.wage_type in ["hourly"]:
                            daily_wage = (
                                (((salaray_bs * 8) * 7) * 4) + rule_sdp_acum
                            ) / 30
                        elif current_contract.structure_type_id.wage_type in [
                            "monthly"
                        ]:
                            daily_wage = (salaray_bs + rule_sdp_acum) / 30

                        # Step 3: Calculation of profit rate
                        aliquot_profits = daily_wage * (
                            (self.env.company.days_of_profit or 0) / 360
                        )

                        # Step 4: Calculation of vacation rate
                        aliquot_holidays = daily_wage * (
                            (self.env.company.vacations or 0) / 360
                        )

                        # Step 5: Calculation of the Comprehensive Salary
                        comprehensive_salary = (
                            daily_wage + aliquot_holidays + aliquot_profits
                        )

                        # Step 7: Assignment of benefits
                        if (
                            self.env.company.selection_type_date_benefit
                            == "calendar_date"
                        ):
                            current_contract.social_benefits_generated += (
                                comprehensive_salary
                                * (
                                    5
                                    * (
                                        current_contract.months_of_seniority
                                        if current_contract.months_of_seniority < 3
                                        and current_contract.years_of_seniority < 1
                                        else 3
                                    )
                                )
                            )
                            current_contract.provisions_social_benefits_generated = (
                                comprehensive_salary
                                * (
                                    5
                                    * (
                                        current_contract.months_of_seniority
                                        if current_contract.months_of_seniority < 3
                                        and current_contract.years_of_seniority < 1
                                        else 3
                                    )
                                )
                            )
                        else:
                            current_contract.social_benefits_generated += (
                                comprehensive_salary * 15
                            )
                            current_contract.provisions_social_benefits_generated = (
                                comprehensive_salary * 15
                            )
                        current_contract.provisions_social_benefits_generated_date = (
                            today
                        )
                        # date of last benefit calculation
                        current_contract.last_social_benefits_calculation = today

                        # Step 6: Calculation of Additional Days (Days per year)
                        if (
                            current_contract.years_of_seniority > 0
                            and current_contract.years_of_seniority % 2 == 0
                            and current_contract.employee_additional_days <= 30
                            and (
                                not current_contract.last_calculation_days_per_year
                                or not (
                                    current_contract.last_calculation_days_per_year.year
                                    == today.year
                                )
                            )
                        ):
                            additional_days = 0
                            for item in range(
                                int(current_contract.years_of_seniority / 2)
                            ):
                                additional_days += 2
                            current_contract.employee_additional_days = (
                                additional_days if additional_days <= 30 else 30
                            )
                            current_contract.last_calculation_days_per_year = today

                            current_contract.days_per_year_accumulated += (
                                current_contract.employee_additional_days
                                * comprehensive_salary
                            )
                            current_contract.provisions_days_per_year_accumulated = (
                                current_contract.employee_additional_days
                                * comprehensive_salary
                            )
                            current_contract.provisions_days_per_year_accumulated_date = today
                    else:
                        pass

                    # Total Benefits Available

                    current_contract.total_available_social_benefits_generated = (
                        current_contract.social_benefits_generated
                        + current_contract.accrued_social_benefits
                    ) - current_contract.advances_of_social_benefits
                    current_contract.provisions_benefit_interest = (
                        current_contract.total_available_social_benefits_generated
                        * self.env.company.central_bank_social_benefits_rate
                    )

                    if not current_contract.provisions_benefit_interest_date or not (
                        current_contract.provisions_benefit_interest_date.month
                        == today.month
                    ):
                        current_contract.provisions_benefit_interest_date = today
                        current_contract.benefit_interest += (
                            current_contract.total_available_social_benefits_generated
                            * self.env.company.central_bank_social_benefits_rate
                        )
                else:
                    pass
            else:
                pass
