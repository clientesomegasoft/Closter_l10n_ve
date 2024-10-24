from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    estimated_profit = fields.Monetary(string="Estimated profit", tracking=True)
    estimated_profit_date_start = fields.Date(
        string="Date start", help="Starting date from estimated profit"
    )
    estimated_profit_date_end = fields.Date(
        string="Date end", help="End date up to estimated profit"
    )

    @api.onchange("estimated_profit_date_start", "estimated_profit_date_end")
    def _onchange_calculation_estimated_profits(self):
        if self.estimated_profit_date_start and self.estimated_profit_date_end:
            weeks_between_start_end = (
                self.estimated_profit_date_end - self.estimated_profit_date_start
            ).days
            weeks_between_start_end = int(weeks_between_start_end / 7)
            self.estimated_profit = 0

            payslip_obj = self.env["hr.payslip"].search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("state", "in", ["done", "paid"]),
                    ("date_from", ">=", self.estimated_profit_date_start),
                    ("date_to", "<=", self.estimated_profit_date_end),
                ],
                order="create_date desc",
            )

            category_obj = self.env["hr.estimated.profit"].search(
                [("payroll_structure_type", "=", self.structure_type_id.id)], limit=1
            )

            if payslip_obj and category_obj:
                for payslip in payslip_obj:
                    for line in payslip.line_ids.filtered(
                        lambda x: x.category_id.id
                        in category_obj.salary_rule_category.ids
                    ):
                        self.estimated_profit += line.total

                if self.estimated_profit:
                    self.estimated_profit = (
                        self.estimated_profit / weeks_between_start_end
                    ) / category_obj.average_days
