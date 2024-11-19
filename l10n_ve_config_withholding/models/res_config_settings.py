from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sign_512 = fields.Image(
        related="company_id.sign_512", readonly=False, max_width=512, max_height=512
    )
