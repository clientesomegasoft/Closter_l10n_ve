from odoo import fields, models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    is_payroll_account = fields.Boolean(
        string="Payroll account",
        help="Indicates whether the bank account is intended for payroll purposes.",
    )
