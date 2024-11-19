from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    withholding_officer_id = fields.Many2one(
        related="company_id.withholding_officer_id", readonly=False
    )
    arc_template_id = fields.Many2one(
        related="company_id.arc_template_id",
        readonly=False,
        domain="[('model', '=', 'employee.arc.report.wizard')]",
        store=True,
    )
