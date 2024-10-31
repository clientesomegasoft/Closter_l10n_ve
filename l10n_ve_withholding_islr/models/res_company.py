from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    in_islr_journal_id = fields.Many2one(
        "account.journal", string="ISLR Journal on Purchases"
    )
    out_islr_journal_id = fields.Many2one(
        "account.journal", string="ISLR Journal on Sales"
    )
    in_islr_account_id = fields.Many2one(
        "account.account", string="ISLR account on purchases"
    )
    out_islr_account_id = fields.Many2one(
        "account.account", string="ISLR account on sales"
    )

    def _create_per_company_withholding_sequence(self):
        res = super(__class__, self)._create_per_company_withholding_sequence()
        values = [
            {
                "name": "Withholding ISLR: %s" % company.name,
                "code": "account_withholding_islr",
                "company_id": company.id,
                "padding": 8,
                "number_next": 1,
                "number_increment": 1,
            }
            for company in self
        ]
        if values:
            self.env["ir.sequence"].create(values)
        return res
