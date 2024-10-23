from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    is_municipal_agent = fields.Boolean(
        related="company_id.partner_id.is_municipal_agent", readonly=False
    )
    in_municipal_journal_id = fields.Many2one(
        related="company_id.in_municipal_journal_id",
        readonly=False,
        domain="[('company_id', '=', company_id), ('withholding_journal_type', '=', 'municipal')]",  # noqa: B950
    )
    out_municipal_journal_id = fields.Many2one(
        related="company_id.out_municipal_journal_id",
        readonly=False,
        domain="[('company_id', '=', company_id), ('withholding_journal_type', '=', 'municipal')]",  # noqa: B950
    )
    in_municipal_account_id = fields.Many2one(
        related="company_id.in_municipal_account_id", readonly=False
    )
    out_municipal_account_id = fields.Many2one(
        related="company_id.out_municipal_account_id", readonly=False
    )
    activity_number = fields.Char(related="company_id.activity_number", readonly=False)
    nifg = fields.Char(related="company_id.nifg", readonly=False)

    @api.onchange("is_municipal_agent")
    def _onchange_is_municipal_agent(self):
        if not self.is_municipal_agent:
            self.in_municipal_journal_id = False
            self.in_municipal_account_id = False
