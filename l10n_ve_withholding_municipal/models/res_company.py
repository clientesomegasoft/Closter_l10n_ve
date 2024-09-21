from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    in_municipal_journal_id = fields.Many2one(
        "account.journal", string="Diario de compra para retención municipal"
    )
    out_municipal_journal_id = fields.Many2one(
        "account.journal", string="Diario de venta para retención municipal"
    )
    in_municipal_account_id = fields.Many2one(
        "account.account", string="Cuenta de retención municipal en compras"
    )
    out_municipal_account_id = fields.Many2one(
        "account.account", string="Cuenta de retención municipal en ventas"
    )
    activity_number = fields.Char(string="Licencia de actividades económicas")
    nifg = fields.Char(string="NIFG")

    def _create_per_company_withholding_sequence(self):
        super(ResCompany, self)._create_per_company_withholding_sequence()
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
