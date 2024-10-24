from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    sequence_type = fields.Selection(
        [("form", "Forma libre"), ("serie", "Serie"), ("manual", "Contingencia")],
        string="Tipo de secuencia",
    )
    nro_ctrl_sequence_id = fields.Many2one(
        "ir.sequence", string="Secuencia de número de control"
    )
    invoice_name_sequence_id = fields.Many2one(
        "ir.sequence", string="Secuencia de factura"
    )
