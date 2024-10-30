from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    withholding_journal_type = fields.Selection(
        selection=[], string="Type of withholding journal"
    )

    @api.onchange("type")
    def _onchange_journal_type(self):
        self.withholding_journal_type = False
