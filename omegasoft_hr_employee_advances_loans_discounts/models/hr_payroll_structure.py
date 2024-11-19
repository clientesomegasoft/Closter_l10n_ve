from odoo import fields, models


class HrPayslip(models.Model):
    _name = "hr.payroll.structure"
    _inherit = ["hr.payroll.structure", "mail.thread", "mail.activity.mixin"]

    is_loan_discount = fields.Boolean(
        "Is loan and Discount", default=False, tracking=True
    )
