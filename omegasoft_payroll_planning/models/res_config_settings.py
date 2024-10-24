# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    planning_workstation = fields.Boolean(
        "Workstation", readonly=False, help="Do you want to associate jobs with roles?"
    )


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    planning_workstation = fields.Boolean(
        "Workstation",
        related="company_id.planning_workstation",
        readonly=False,
        help="Do you want to associate jobs with roles?",
    )
