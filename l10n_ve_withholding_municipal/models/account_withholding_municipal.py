from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class AccountWithholdingMunicipal(models.Model):
    _name = "account.withholding.municipal"
    _description = "Retenciones Municipales"
    _order = "date desc, name desc, id desc"

    name = fields.Char(string="Numero de comprobante", default="NUMERO DE COMPROBANTE")
    type = fields.Selection(
        [
            ("customer", "Retención municipal clientes"),
            ("supplier", "Retención municipal proveedores"),
        ],
        required=True,
        readonly=True,
    )
    state = fields.Selection(
        [("draft", "Borrador"), ("posted", "Publicado"), ("cancel", "Cancelado")],
        string="Estado",
        default="draft",
    )
    invoice_id = fields.Many2one(
        "account.move", string="Factura", required=True, readonly=True
    )
    agent_id = fields.Many2one(
        "res.partner", string="Agente de retención", required=True, readonly=True
    )
    subject_id = fields.Many2one(
        "res.partner", string="Sujeto retenido", required=True, readonly=True
    )
    date = fields.Date(
        string="Fecha de comprobante",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    invoice_date = fields.Date(
        related="invoice_id.invoice_date", string="Fecha factura"
    )
    line_ids = fields.One2many(
        "account.withholding.municipal.line",
        "withholding_municipal_id",
        string="Lineas",
        readonly=True,
    )
    base_amount = fields.Monetary(
        string="Base imponible", compute="_compute_amount", store=True
    )
    amount = fields.Monetary(
        string="Monto retenido", compute="_compute_amount", store=True
    )
    move_id = fields.Many2one("account.move", string="Asiento contable")
    journal_id = fields.Many2one("account.journal", string="Diario")
    withholding_account_id = fields.Many2one(
        "account.account", string="Cuenta de retención", required=True
    )
    destination_account_id = fields.Many2one(
        "account.account", string="Cuenta destino", required=True
    )
    currency_id = fields.Many2one(
        "res.currency", related="company_id.fiscal_currency_id", store=True
    )
    company_id = fields.Many2one(
        "res.company", related="invoice_id.company_id", string="Compañía", store=True
    )

    @api.depends("line_ids.base_amount", "line_ids.amount")
    def _compute_amount(self):
        for rec in self:
            base_amount = amount = 0.0
            for line in rec.line_ids:
                base_amount += line.base_amount
                amount += line.amount
            rec.base_amount = base_amount
            rec.amount = amount

    def button_post(self):
        if not self.date:
            self.date = fields.Date.today()
        if self.type == "supplier" and (
            not self.name or self.name == "NUMERO DE COMPROBANTE"
        ):
            self.name = self.date.strftime("%Y%m") + self.env[
                "ir.sequence"
            ].with_company(self.company_id).next_by_code(
                "account_withholding_municipal"
            )
        elif self.type == "customer" and (
            not self.name or self.name == "NUMERO DE COMPROBANTE"
        ):
            raise UserError(
                _(
                    "El numero de comprobante es requerido."
                )
            )

        values = self._prepare_move_values()
        if self.move_id:
            self.move_id.with_context(
                skip_invoice_sync=True, skip_account_move_synchronization=True
            ).write(values)
        else:
            self.move_id = (
                self.env["account.move"]
                .with_context(
                    skip_invoice_sync=True, skip_account_move_synchronization=True
                )
                .create(values)
            )

        self.move_id.action_post()

        # Reconcile.
        (self.move_id.line_ids + self.invoice_id.line_ids).filtered(
            lambda l: l.account_id.id == self.destination_account_id.id
            and not l.reconciled
        ).reconcile()

        self.write({"state": "posted"})

    def button_send_mail(self):
        self.ensure_one()
        template_id = self.env.ref(
            "l10n_ve_withholding_municipal.mail_template_withholding_municipal_receipt"
        ).id
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "target": "new",
            "context": {
                "default_model": "account.withholding.municipal",
                "default_res_id": self.id,
                "default_use_template": bool(template_id),
                "default_template_id": template_id,
                "default_composition_mode": "comment",
                "default_email_layout_xmlid": "mail.mail_notification_light",
            },
        }

    def button_draft(self):
        for rec in self:
            if rec.move_id:
                rec.move_id.button_draft()
        self.write({"state": "draft"})

    def button_cancel(self):
        for rec in self:
            if rec.move_id:
                if rec.move_id.state == "posted":
                    rec.move_id._reverse_moves(
                        [
                            {
                                "date": fields.Date.context_today(rec),
                                "ref": "Reverso de: " + rec.move_id.name,
                            }
                        ],
                        cancel=True,
                    )
                elif rec.move_id.state == "draft":
                    rec.move_id.button_cancel()
        self.write({"state": "cancel"})

    def button_open_journal_entry(self):
        self.ensure_one()
        return {
            "name": "Asiento",
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "context": {"create": False},
            "view_mode": "form",
            "res_id": self.move_id.id,
        }

    def unlink(self):
        for rec in self:
            if rec.state != "cancel":
                raise UserError(
                    _(
                        "Solo retenciones en estado Cancelado pueden ser suprimidas."
                    )
                )
        return super().unlink()

    def _prepare_move_values(self):
        partner_id = self.agent_id if self.type == "customer" else self.subject_id
        amount_currency = self.amount if self.invoice_id.is_inbound() else -self.amount
        balance = self.company_id.currency_id.round(
            amount_currency
            / (
                self.company_id.currency_id == self.currency_id
                and 1.0
                or self.invoice_id.currency_rate_ref.rate
            )
        )

        move_line_values = [
            {
                "name": "COMP. RET. MUNICIPAL %s" % self.name,
                "partner_id": partner_id.id,
                "account_id": self.withholding_account_id.id,
                "amount_currency": amount_currency,
                "balance": balance,
                "currency_id": self.currency_id.id,
            },
            {
                "name": "COMP. RET. MUNICIPAL %s" % self.name,
                "partner_id": partner_id.id,
                "account_id": self.destination_account_id.id,
                "amount_currency": -amount_currency,
                "balance": -balance,
                "currency_id": self.currency_id.id,
            },
        ]

        withholding_line, counterpart_line, writeoff_lines = self._seek_for_lines()
        line_ids_commands = [
            Command.update(withholding_line.id, move_line_values[0])
            if withholding_line
            else Command.create(move_line_values[0]),
            Command.update(counterpart_line.id, move_line_values[1])
            if counterpart_line
            else Command.create(move_line_values[1]),
        ]
        for line in writeoff_lines:
            line_ids_commands.append(Command.delete(line.id))

        return {
            "move_type": "entry",
            "ref": self.invoice_id.name,
            "date": self.date,
            "journal_id": self.journal_id.id,
            "partner_id": partner_id.id,
            "currency_rate_ref": self.invoice_id.currency_rate_ref.id,
            "currency_id": self.currency_id.id,
            "company_id": self.company_id.id,
            "line_ids": line_ids_commands,
        }

    def _seek_for_lines(self):
        withholding_line = self.env["account.move.line"]
        counterpart_line = self.env["account.move.line"]
        writeoff_lines = self.env["account.move.line"]
        for line in self.move_id.line_ids:
            if line.account_id == self.withholding_account_id:
                withholding_line |= line
            elif line.account_id == self.destination_account_id:
                counterpart_line |= line
            else:
                writeoff_lines |= line
        return withholding_line, counterpart_line, writeoff_lines


class AccountWithholdingMunicipalLine(models.Model):
    _name = "account.withholding.municipal.line"
    _description = "Lineas de retencion de municipal"

    withholding_municipal_id = fields.Many2one(
        "account.withholding.municipal", ondelete="cascade", required=True
    )
    municipal_concept_id = fields.Many2one(
        "account.municipal.concept",
        string="Concepto de retención municipal",
        required=True,
    )
    municipal_concept_rate = fields.Float(related="municipal_concept_id.rate")
    base_amount = fields.Monetary(string="Base imponible")
    amount = fields.Monetary(string="Monto retenido")
    currency_id = fields.Many2one(
        "res.currency", related="company_id.fiscal_currency_id", store=True
    )
    company_id = fields.Many2one(
        "res.company", related="withholding_municipal_id.company_id", store=True
    )
