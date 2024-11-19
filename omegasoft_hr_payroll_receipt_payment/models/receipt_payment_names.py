from odoo import fields, models


class ReportNames(models.Model):
    _name = "hr_receipt_payment_names"
    _description = "Report names"

    name = fields.Char(string="Report Name")

    active = fields.Boolean(
        default=True,
        help="Set active to false to hide the report name tag without removing it.",
    )
