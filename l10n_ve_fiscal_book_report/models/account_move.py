from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    not_in_fiscal_book = fields.Boolean(
        string="Excluir este documento del libro fiscal", default=False
    )
