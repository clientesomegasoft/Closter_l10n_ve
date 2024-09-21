from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    igtf_percentage = fields.Float(string="Porcentaje IGTF", digits=(5, 2))
    igtf_inbound_account_id = fields.Many2one(
        "account.account", string="Cuenta Recibos IGTF"
    )
    igtf_outbound_account_id = fields.Many2one(
        "account.account", string="Cuenta pagos IGTF"
    )
