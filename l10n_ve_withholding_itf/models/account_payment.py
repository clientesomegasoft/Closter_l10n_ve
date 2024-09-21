from odoo import Command, api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    apply_itf = fields.Boolean(compute="_compute_apply_itf")
    calculate_itf = fields.Boolean(
        string="Permitir ITF",
        default=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    itf_move_id = fields.Many2one("account.move", string="Asiento ITF")

    @api.depends("currency_id", "payment_type", "company_id.apply_itf")
    def _compute_apply_itf(self):
        for pay in self:
            pay.apply_itf = (
                pay.company_id.apply_itf
                and pay.payment_type == "outbound"
                and pay.currency_id.id == pay.company_id.fiscal_currency_id.id
            )

    def action_post(self):
        super(__class__, self).action_post()

        percentage = self.company_id.itf_percentage
        amount_currency = self.currency_id.round(self.amount * percentage / 100)

        if not (self.apply_itf and self.calculate_itf) or self.currency_id.is_zero(
            amount_currency
        ):
            if self.itf_move_id:
                if self.itf_move_id.state == "posted":
                    self.itf_move_id._reverse_moves(
                        [
                            {
                                "date": fields.Date.context_today(self),
                                "ref": "Reverso de: " + self.itf_move_id.name,
                            }
                        ],
                        cancel=True,
                    )
                elif self.itf_move_id.state == "draft":
                    self.itf_move_id.button_cancel()
                self.itf_move_id = False
            return

        balance = (
            amount_currency
            if self.currency_id == self.company_currency_id
            else self.company_currency_id.round(
                amount_currency / self.currency_rate_ref.rate
            )
        )
        move_line_values = [
            {
                "name": f"Comisión ITF del {percentage}% de {self.name}",
                "date_maturity": self.date,
                "amount_currency": amount_currency,
                "currency_id": self.currency_id.id,
                "balance": balance,
                "partner_id": self.partner_id.id,
                "account_id": self.company_id.itf_account_id.id,
            },
            {
                "name": f"Comisión ITF del {percentage}% de {self.name}",
                "date_maturity": self.date,
                "amount_currency": -amount_currency,
                "currency_id": self.currency_id.id,
                "balance": -balance,
                "partner_id": self.partner_id.id,
                "account_id": self.outstanding_account_id.id,
            },
        ]

        liquidity_lines, counterpart_lines, writeoff_lines = self._seek_for_itf_lines()

        line_ids_commands = [
            Command.update(liquidity_lines.id, move_line_values[0])
            if liquidity_lines
            else Command.create(move_line_values[0]),
            Command.update(counterpart_lines.id, move_line_values[1])
            if counterpart_lines
            else Command.create(move_line_values[1]),
        ]

        for line in writeoff_lines:
            line_ids_commands.append(Command.delete(line.id))

        move_values = {
            "move_type": "entry",
            "date": self.date,
            "journal_id": self.journal_id.id,
            "partner_id": self.partner_id.id,
            "currency_rate_ref": self.currency_rate_ref.id,
            "currency_id": self.currency_id.id,
            "company_id": self.company_id.id,
            "line_ids": line_ids_commands,
        }

        if self.itf_move_id:
            self.itf_move_id.write(move_values)
        else:
            self.itf_move_id = self.env["account.move"].create(move_values)
        self.itf_move_id.action_post()

    def _seek_for_itf_lines(self):
        liquidity_lines = self.env["account.move.line"]
        counterpart_lines = self.env["account.move.line"]
        writeoff_lines = self.env["account.move.line"]
        for line in self.itf_move_id.line_ids:
            if line.account_id.id == self.company_id.itf_account_id.id:
                liquidity_lines |= line
            elif line.account_id.id == self.outstanding_account_id.id:
                counterpart_lines |= line
            else:
                writeoff_lines |= line
        return liquidity_lines, counterpart_lines, writeoff_lines

    def button_open_itf_entry(self):
        self.ensure_one()
        return {
            "name": "Asiento ITF",
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "context": {"create": False},
            "view_mode": "form",
            "res_id": self.itf_move_id.id,
        }

    def action_draft(self):
        super(__class__, self).action_draft()
        self.itf_move_id.button_draft()

    def action_cancel(self):
        super(__class__, self).action_cancel()
        self.itf_move_id.button_cancel()
