from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    person_type_code = fields.Char(related="partner_id.person_type_id.code")
    supplier_invoice_number = fields.Char(string="Provider invoice number", copy=False)
    nro_ctrl = fields.Char(string="Control number", copy=False)

    _sql_constraints = [
        (
            "unique_nro_ctrl_out_invoice",
            "EXCLUDE (nro_ctrl WITH =, company_id WITH =) WHERE (move_type IN ('out_invoice', 'out_refund'))",  # noqa: B950
            "\nA document with the same control number already exists!",
        ),
        (
            "unique_nro_ctrl_in_invoice",
            "UNIQUE(move_type, partner_id, nro_ctrl, company_id)",
            "\nA document with the same control number already exists!",
        ),
    ]
