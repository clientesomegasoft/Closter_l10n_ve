from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    serie = fields.Char(string="Serie", readonly=True)
    invoice_name_sequence_id = fields.Many2one(
        related="journal_id.invoice_name_sequence_id"
    )

    @api.depends("posted_before", "state", "journal_id", "date")
    def _compute_name(self):
        processed_moves = self.env["account.move"]
        for move in self:
            if (
                move.is_sale_document()
                and move.name in (False, "/")
                and move.state == "posted"
                and move.journal_id.invoice_name_sequence_id
            ):
                move.name = move.journal_id.invoice_name_sequence_id.next_by_id()
                processed_moves |= move
        return super(AccountMove, self - processed_moves)._compute_name()

    def action_post(self):
        var = super(AccountMove, self).action_post()
        if (
            self.is_sale_document()
            and not self.nro_ctrl
            and self.journal_id.nro_ctrl_sequence_id
        ):
            self.nro_ctrl = self.journal_id.nro_ctrl_sequence_id.next_by_id()
            self.serie = self.journal_id.nro_ctrl_sequence_id.serie
        return var
