from odoo import _, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    in_iva_journal_id = fields.Many2one(
        "account.journal", string="VAT journal on purchases"
    )
    out_iva_journal_id = fields.Many2one(
        "account.journal", string="VAT journal on sales"
    )
    in_iva_account_id = fields.Many2one(
        "account.account", string="VAT account on purchases"
    )
    out_iva_account_id = fields.Many2one(
        "account.account", string="VAT account on sales"
    )

    def _create_per_company_withholding_sequence(self):
        res = super(__class__, self)._create_per_company_withholding_sequence()
        values = [
            {
                "name": _("VAT Withholding: %s") % (company.name),
                "code": "account_withholding_iva",
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
