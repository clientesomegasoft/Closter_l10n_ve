# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class HrPayslipWorkedDays(models.Model):
    _inherit = "hr.payslip.worked_days"

    @api.depends(
        "is_paid",
        "number_of_hours",
        "payslip_id",
        "contract_id.wage",
        "payslip_id.sum_worked_hours",
    )
    def _compute_amount(self):
        for worked_days in self:
            if worked_days.payslip_id.edited or worked_days.payslip_id.state not in [
                "draft",
                "verify",
            ]:
                continue
            if not worked_days.contract_id or worked_days.code == "OUT":
                worked_days.amount = 0
                continue
            if worked_days.payslip_id.wage_type == "hourly":
                worked_days.amount = (
                    worked_days.payslip_id.contract_id.hourly_wage
                    * worked_days.number_of_hours
                    if worked_days.is_paid
                    else 0
                )

                if (
                    worked_days.currency_id
                    != worked_days.payslip_id.contract_id.custom_hourly_wage_currency
                ):
                    worked_days.amount = worked_days.payslip_id.contract_id.custom_hourly_wage_currency._convert(  # noqa: B950
                        worked_days.amount,
                        worked_days.currency_id,
                        self.env.company,
                        worked_days.payslip_id.rate_id.name,
                    )
            else:
                worked_days.amount = (
                    (
                        (worked_days.payslip_id.contract_id.contract_wage / 30)
                        * worked_days.number_of_days
                        if worked_days.number_of_days
                        else (
                            (
                                worked_days.payslip_id.contract_id.contract_wage
                                / (
                                    30
                                    * worked_days.contract_id.resource_calendar_id.hours_per_day
                                )
                            )
                            * worked_days.number_of_hours
                        )
                    )
                    if worked_days.is_paid
                    else 0
                )

                if (
                    worked_days.currency_id
                    != worked_days.payslip_id.contract_id.custom_wage_currency
                ):
                    worked_days.amount = worked_days.payslip_id.contract_id.custom_wage_currency._convert(  # noqa: B950
                        worked_days.amount,
                        worked_days.currency_id,
                        self.env.company,
                        worked_days.payslip_id.rate_id.name,
                    )
