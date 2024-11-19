from odoo import fields, models


class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    currency_ref_id = fields.Many2one(related="company_id.currency_ref_id")
    amount_ref = fields.Monetary(default=0.0, currency_field="currency_ref_id")
