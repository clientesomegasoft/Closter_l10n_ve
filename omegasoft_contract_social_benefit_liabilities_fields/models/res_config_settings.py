from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    selection_type_date_benefit = fields.Selection(
        selection=[
            ("calendar_date", "Calendat date"),
            ("contract_start_date", "Contract start date"),
        ],
        required=True,
        string="Type date benefit calculation",
    )


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    selection_type_date_benefit = fields.Selection(
        related="company_id.selection_type_date_benefit",
        readonly=False,
        required=True,
        string="Type date benefit calculation",
    )
