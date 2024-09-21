from odoo import api, fields, models
from odoo.tools import date_utils

PERIOD_DATES = [
    (31, 3),  # march
    (30, 6),  # june
    (30, 9),  # september
    (31, 12),  # december
]


class HrEmployeePrivate(models.Model):
    _inherit = "hr.employee"

    employee_ari_ids = fields.One2many(
        "hr.employee.ari", "employee_id", string="ARI", readonly=True
    )
    employee_ari_setting_ids = fields.One2many(
        "ari.employee.setting.lines", "employee_id", string="Lineas"
    )

    def _calculate_ari(self, force=False):
        def _get_trimester_field(month):
            return {
                1: "trimester_1",
                2: "trimester_2",
                3: "trimester_3",
                4: "trimester_4",
            }[(month - 1) // 3 + 1]

        def _compute_factor(amount):
            if amount <= 1000:
                return amount * 6 / 100
            elif amount <= 1500:
                return amount * 9 / 100 - 30
            elif amount <= 2000:
                return amount * 12 / 100 - 75
            elif amount <= 2500:
                return amount * 16 / 100 - 155
            elif amount <= 3000:
                return amount * 20 / 100 - 255
            elif amount <= 4000:
                return amount * 24 / 100 - 375
            elif amount <= 6000:
                return amount * 29 / 100 - 575
            else:
                return amount * 34 / 100 - 875

        today = (
            force and fields.Date.from_string(force) or fields.Date.context_today(self)
        )
        if not any(
            today.day == day and today.month == month for day, month in PERIOD_DATES
        ):
            return

        date_from, date_to = date_utils.get_quarter(today)
        employee_ids = self.search(
            [
                ("contract_id.state", "=", "open"),
                ("company_id", "=", self.env.company.id),
            ]
        )
        full_wage = employee_ids._get_full_wage(date_from, date_to)
        received_wage = employee_ids._get_received_wage(date_from, date_to)
        withholding_amount = employee_ids._get_withholding_amount(date_from, date_to)
        trimester = _get_trimester_field(today.month)
        ut = self.env["account.ut"].search([], limit=1)
        data = []

        for employee_id in employee_ids:
            wage = full_wage[employee_id.id]
            family_burden = len(
                employee_id.family_information_ids.filtered(
                    lambda l: l.is_family_burden
                )
            )
            line = {
                "employee_id": employee_id.id,
                "fiscal_year": today.year,
                "trimester": trimester,
                "wage": wage,
                "ut": ut.amount,
                "family": family_burden,
            }
            line.update(
                employee_id.employee_ari_setting_ids._get_ari_setting_by_trimester(
                    trimester
                )
            )

            wage_ut = wage / ut.amount
            to_hold_ut = (
                _compute_factor(
                    wage_ut
                    - (
                        (
                            sum(
                                line.get(key, 0.0)
                                for key in ("education", "HCM", "odontology", "house")
                            )
                            / ut.amount
                        )
                        or 774.0
                    )
                )
                - ((family_burden + 1) * 10)
                - (line.get("extra", 0.0) / ut.amount)
            )
            percentage = to_hold_ut / wage_ut * 100

            last_trimester = employee_id.employee_ari_ids[-1:]
            if (
                last_trimester
                and last_trimester.fiscal_year == today.year
                and last_trimester.percentage != percentage
            ):
                percentage = (
                    (
                        to_hold_ut * ut.amount
                        - withholding_amount.get(employee_id.id, 0.0)
                    )
                    / (wage - received_wage.get(employee_id.id, 0.0))
                ) * 100

            line["percentage"] = percentage > 0.0 and percentage or 0.0
            data.append(line)

        if data:
            self.env["hr.employee.ari"].create(data)

    def _get_full_wage(self, date_from, date_to):
        company = self.env.company
        overtime = self._get_employee_overtime(date_from, date_to)
        total_days = 360 + company.days_of_profit + company.vacations
        full_wage = {}
        for employee_id in self:
            contract = employee_id.contract_id
            if contract.wage_type == "hourly":
                daily_wage = (
                    contract.custom_hourly_wage_currency._convert(
                        contract.hourly_wage, company.currency_id, company, date_to
                    )
                    * 8
                )
            else:
                daily_wage = (
                    contract.custom_wage_currency._convert(
                        contract.wage, company.currency_id, company, date_to
                    )
                    / 30
                )
            full_wage[employee_id.id] = (
                daily_wage + overtime.get(employee_id.id, 0.0)
            ) * total_days
        return full_wage

    def _get_employee_overtime(self, date_from, date_to):
        overtime = {}
        if self.env.company.overtime_category_ids:
            self._cr.execute(
                """
                SELECT hr_payslip.employee_id, SUM(hr_payslip_line.total) / 90
                FROM hr_payslip, hr_payslip_line
                WHERE hr_payslip.id = hr_payslip_line.slip_id
                    AND hr_payslip.employee_id IN %s
                    AND hr_payslip.state IN ('done', 'paid')
                    AND hr_payslip.date_from >= %s
                    AND hr_payslip.date_to <= %s
                    AND hr_payslip_line.category_id IN %s
                    AND hr_payslip.company_id = %s
                GROUP BY hr_payslip.employee_id
            """,
                (
                    tuple(self.ids),
                    date_from,
                    date_to,
                    tuple(self.env.company.overtime_category_ids.ids),
                    self.env.company.id,
                ),
            )
            overtime = dict(self._cr.fetchall())
        return overtime

    def _get_received_wage(self, date_from, date_to):
        received_wage = {}
        if self.env.company.wage_received_rule_ids:
            self._cr.execute(
                """
                SELECT hr_payslip.employee_id, SUM(hr_payslip_line.total)
                FROM hr_payslip, hr_payslip_line
                WHERE hr_payslip.id = hr_payslip_line.slip_id
                    AND hr_payslip.employee_id IN %s
                    AND hr_payslip.state IN ('done', 'paid')
                    AND hr_payslip.date_from >= %s
                    AND hr_payslip.date_to <= %s
                    AND hr_payslip_line.code IN %s
                    AND hr_payslip.company_id = %s
                GROUP BY hr_payslip.employee_id
            """,
                (
                    tuple(self.ids),
                    date_from,
                    date_to,
                    tuple(self.env.company.wage_received_rule_ids.mapped("code")),
                    self.env.company.id,
                ),
            )
            received_wage = dict(self._cr.fetchall())
        return received_wage

    def _get_withholding_amount(self, date_from, date_to):
        withheld = {}
        if self.env.company.withholdig_rule_ids:
            self._cr.execute(
                """
                SELECT hr_payslip.employee_id, SUM(hr_payslip_line.total)
                FROM hr_payslip, hr_payslip_line
                WHERE hr_payslip.id = hr_payslip_line.slip_id
                    AND hr_payslip.employee_id IN %s
                    AND hr_payslip.state IN ('done', 'paid')
                    AND hr_payslip.date_from >= %s
                    AND hr_payslip.date_to <= %s
                    AND hr_payslip_line.code IN %s
                    AND hr_payslip.company_id = %s
                GROUP BY hr_payslip.employee_id
            """,
                (
                    tuple(self.ids),
                    date_from,
                    date_to,
                    tuple(self.env.company.withholdig_rule_ids.mapped("code")),
                    self.env.company.id,
                ),
            )
            withheld = dict(self._cr.fetchall())
        return withheld


class Contract(models.Model):
    _inherit = "hr.contract"

    percentage_income_tax_islr = fields.Float(
        compute="_compute_percentage_income_tax_islr", store=True
    )

    @api.depends("employee_id.employee_ari_ids")
    def _compute_percentage_income_tax_islr(self):
        for rec in self:
            rec.percentage_income_tax_islr = rec.employee_id.employee_ari_ids[
                -1:
            ].percentage
