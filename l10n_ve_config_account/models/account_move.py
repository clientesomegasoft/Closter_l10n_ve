from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    person_type_code = fields.Char(related="partner_id.person_type_id.code")
    supplier_invoice_number = fields.Char(
        string="Número de factura de proveedor", copy=False
    )
    nro_ctrl = fields.Char(string="Número de control", copy=False)

    _sql_constraints = [
        (
            "unique_nro_ctrl_out_invoice",
            "EXCLUDE (nro_ctrl WITH =, company_id WITH =) WHERE (move_type IN ('out_invoice', 'out_refund'))",
            "\nYa existe un documento con el mismo número de control !",
        ),
        (
            "unique_nro_ctrl_in_invoice",
            "UNIQUE(move_type, partner_id, nro_ctrl, company_id)",
            "\nYa existe un documento con el mismo número de control !",
        ),
    ]
