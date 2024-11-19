from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    igtf_percentage = fields.Float(string="IGTF percentage", digits=(5, 2))
    igtf_inbound_account_id = fields.Many2one(
        "account.account", string="IGTF Receipt Account"
    )
    igtf_outbound_account_id = fields.Many2one(
        "account.account", string="IGTF payment account"
    )
