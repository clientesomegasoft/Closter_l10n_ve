from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    signature_512 = fields.Image(readonly=False)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    signature_512 = fields.Image(related="company_id.signature_512", readonly=False)
