from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    apply_itf = fields.Boolean(related="company_id.apply_itf", readonly=False)
    itf_percentage = fields.Float(related="company_id.itf_percentage", readonly=False)
    itf_account_id = fields.Many2one(
        related="company_id.itf_account_id", readonly=False
    )

    @api.onchange("apply_itf")
    def _onchange_apply_itf(self):
        if not self.apply_itf:
            self.itf_percentage = 0
            self.itf_account_id = False
