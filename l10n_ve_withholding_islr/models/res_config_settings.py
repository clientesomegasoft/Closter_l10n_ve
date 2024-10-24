from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    is_islr_exempt = fields.Boolean(
        related="company_id.partner_id.is_islr_exempt", readonly=False
    )
    is_islr_agent = fields.Boolean(
        related="company_id.partner_id.is_islr_agent", readonly=False
    )
    in_islr_journal_id = fields.Many2one(
        related="company_id.in_islr_journal_id",
        readonly=False,
        domain="[('company_id', '=', company_id), ('withholding_journal_type', '=', 'islr')]",
    )
    out_islr_journal_id = fields.Many2one(
        related="company_id.out_islr_journal_id",
        readonly=False,
        domain="[('company_id', '=', company_id), ('withholding_journal_type', '=', 'islr')]",
    )
    in_islr_account_id = fields.Many2one(
        related="company_id.in_islr_account_id", readonly=False
    )
    out_islr_account_id = fields.Many2one(
        related="company_id.out_islr_account_id", readonly=False
    )

    @api.onchange("is_islr_agent")
    def _onchange_is_islr_agent(self):
        if not self.is_islr_agent:
            self.in_islr_journal_id = False
            self.in_islr_account_id = False
