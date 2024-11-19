from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    active_organizational_units = fields.Boolean(string="active organizational units")


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    active_organizational_units = fields.Boolean(
        string="active organizational units",
        related="company_id.active_organizational_units",
        readonly=False,
    )
