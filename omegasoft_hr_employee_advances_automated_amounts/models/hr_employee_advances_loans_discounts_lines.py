from odoo import fields, models


class HrEmployeeAdvancesLoansDiscountsLines(models.Model):
    _inherit = "hr_employee_advances_loans_discounts_lines"

    use_available_amount_per_employee = fields.Boolean(
        related="advances_loans_discounts_id.use_available_amount_per_employee"
    )

    parent_state = fields.Selection(
        related="advances_loans_discounts_id.state", string="Parent State"
    )
