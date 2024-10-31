from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    in_municipal_journal_id = fields.Many2one(
        "account.journal", string="Purchase journal for municipal retention"
    )
    out_municipal_journal_id = fields.Many2one(
        "account.journal", string="Sales journal for municipal retention"
    )
    in_municipal_account_id = fields.Many2one(
        "account.account", string="Municipal withholding account on purchases"
    )
    out_municipal_account_id = fields.Many2one(
        "account.account", string="Municipal withholding account on sales"
    )
    activity_number = fields.Char(string="License for economic activities")
    nifg = fields.Char(string="NIFG")

    def _create_per_company_withholding_sequence(self):
        res = super(__class__, self)._create_per_company_withholding_sequence()
        values = [
            {
                "name": "Withholding municipal: %s" % company.name,
                "code": "account_withholding_municipal",
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
