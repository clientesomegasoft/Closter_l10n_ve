from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    apply_igtf = fields.Boolean(
        related="company_id.partner_id.apply_igtf", readonly=False
    )
    igtf_percentage = fields.Float(related="company_id.igtf_percentage", readonly=False)
    igtf_inbound_account_id = fields.Many2one(
        related="company_id.igtf_inbound_account_id", readonly=False
    )
    igtf_outbound_account_id = fields.Many2one(
        related="company_id.igtf_outbound_account_id", readonly=False
    )

    @api.onchange("apply_igtf")
    def _onchange_apply_igtf(self):
        if not self.apply_igtf:
            self.igtf_percentage = 0
            self.igtf_inbound_account_id = False
            self.igtf_outbound_account_id = False
