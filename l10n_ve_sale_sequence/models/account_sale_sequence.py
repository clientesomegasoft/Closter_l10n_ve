from odoo import Command, api, fields, models


class AccountSaleSequence(models.Model):
    _name = "account.sale.sequence"
    _description = "Secuencia de venta"

    name = fields.Char(string="Nombre de secuencia", required=True)
    sequence_type = fields.Selection(
        [("form", "Forma libre"), ("serie", "Serie"), ("manual", "Contingencia")],
        string="Tipo de secuencia",
        required=True,
    )
    serie = fields.Char(related="invoice_control_sequence_id.serie", readonly=False)
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
        readonly=True,
    )

    # FACTURAS
    invoice_control_sequence_id = fields.Many2one(
        "ir.sequence", required=True, ondelete="restrict"
    )
    invoice_control_number_next_actual = fields.Integer(
        related="invoice_control_sequence_id.number_next_actual", readonly=False
    )
    invoice_control_padding = fields.Integer(
        related="invoice_control_sequence_id.padding", readonly=False
    )

    invoice_sequence_id = fields.Many2one(
        "ir.sequence", required=True, ondelete="restrict"
    )
    invoice_journal_ids = fields.One2many(
        "account.journal",
        related="invoice_sequence_id.invoice_name_journal_ids",
        readonly=False,
        domain="[('type', '=', 'sale'), ('sequence_type', '=', sequence_type), ('invoice_name_sequence_id', '=', False)]",
    )
    invoice_prefix = fields.Char(related="invoice_sequence_id.prefix", readonly=False)
    invoice_padding = fields.Integer(
        related="invoice_sequence_id.padding", readonly=False
    )
    invoice_number_next_actual = fields.Integer(
        related="invoice_sequence_id.number_next_actual", readonly=False
    )

    # NOTAS DE CRÉDITO
    refund_control_sequence_id = fields.Many2one(
        "ir.sequence", required=True, ondelete="restrict"
    )
    refund_control_number_next_actual = fields.Integer(
        related="refund_control_sequence_id.number_next_actual", readonly=False
    )
    refund_control_padding = fields.Integer(
        related="refund_control_sequence_id.padding", readonly=False
    )

    refund_sequence_id = fields.Many2one(
        "ir.sequence", required=True, ondelete="restrict"
    )
    refund_journal_ids = fields.One2many(
        "account.journal",
        related="refund_sequence_id.invoice_name_journal_ids",
        readonly=False,
        domain="[('type', '=', 'sale'), ('sequence_type', '=', sequence_type), ('invoice_name_sequence_id', '=', False)]",
    )
    refund_prefix = fields.Char(related="refund_sequence_id.prefix", readonly=False)
    refund_padding = fields.Integer(
        related="refund_sequence_id.padding", readonly=False
    )
    refund_number_next_actual = fields.Integer(
        related="refund_sequence_id.number_next_actual", readonly=False
    )

    # NOTAS DE DÉBITO
    debit_control_sequence_id = fields.Many2one(
        "ir.sequence", required=True, ondelete="restrict"
    )
    debit_control_number_next_actual = fields.Integer(
        related="debit_control_sequence_id.number_next_actual", readonly=False
    )
    debit_control_padding = fields.Integer(
        related="debit_control_sequence_id.padding", readonly=False
    )

    debit_sequence_id = fields.Many2one(
        "ir.sequence", required=True, ondelete="restrict"
    )
    debit_journal_ids = fields.One2many(
        "account.journal",
        related="debit_sequence_id.invoice_name_journal_ids",
        readonly=False,
        domain="[('type', '=', 'sale'), ('sequence_type', '=', sequence_type), ('invoice_name_sequence_id', '=', False)]",
    )
    debit_prefix = fields.Char(related="debit_sequence_id.prefix", readonly=False)
    debit_padding = fields.Integer(related="debit_sequence_id.padding", readonly=False)
    debit_number_next_actual = fields.Integer(
        related="debit_sequence_id.number_next_actual", readonly=False
    )

    @api.onchange("sequence_type")
    def _onchange_sequence_type(self):
        self.serie = False

    @api.model_create_multi
    def create(self, vals_list):
        create_sequence = self.env["ir.sequence"].create
        field_group = ("invoice", "refund", "debit")
        for vals in vals_list:
            control_sequence = False
            is_manual = vals["sequence_type"] == "manual"
            for field in field_group:
                if is_manual or not control_sequence:
                    control_sequence = self._create_control_sequence(field, vals)
                name_sequence = create_sequence(
                    {
                        "name": "{} name - {}".format(field, vals["sequence_type"]),
                        "company_id": vals.get("company_id", self.env.company.id),
                    }
                )
                vals[field + "_control_sequence_id"] = control_sequence.id
                vals[field + "_sequence_id"] = name_sequence.id

        res = super(__class__, self).create(vals_list)
        res._check_control_sequence()
        return res

    def write(self, vals):
        if "sequence_type" in vals:
            if vals["sequence_type"] == "manual":
                for field in ("refund", "debit"):
                    control_sequence = self._create_control_sequence(field, vals)
                    vals[field + "_control_sequence_id"] = control_sequence.id
            elif self.sequence_type == "manual":
                to_unlink = (
                    self.refund_control_sequence_id + self.debit_control_sequence_id
                )
                self.refund_control_sequence_id = (
                    self.debit_control_sequence_id
                ) = self.invoice_control_sequence_id
                to_unlink.unlink()

        res = super(__class__, self).write(vals)

        if any(
            field in vals
            for field in (
                "sequence_type",
                "invoice_journal_ids",
                "refund_journal_ids",
                "debit_journal_ids",
            )
        ):
            self._check_control_sequence()
        return res

    def unlink(self):
        sequence_ids = self.env["ir.sequence"]
        for field in ("invoice", "refund", "debit"):
            for record in self:
                sequence_ids |= getattr(record, field + "_control_sequence_id")
                sequence_ids |= getattr(record, field + "_sequence_id")
        res = super(__class__, self).unlink()
        sequence_ids.unlink()
        return res

    def _check_control_sequence(self):
        for rec in self:
            if rec.sequence_type == "manual":
                rec.invoice_control_sequence_id.nro_ctrl_journal_ids = [
                    Command.set(rec.invoice_journal_ids.ids)
                ]
                rec.refund_control_sequence_id.nro_ctrl_journal_ids = [
                    Command.set(rec.refund_journal_ids.ids)
                ]
                rec.debit_control_sequence_id.nro_ctrl_journal_ids = [
                    Command.set(rec.debit_journal_ids.ids)
                ]
            else:
                rec.invoice_control_sequence_id.nro_ctrl_journal_ids = [
                    Command.set(
                        rec.invoice_journal_ids.ids
                        + rec.refund_journal_ids.ids
                        + rec.debit_journal_ids.ids
                    )
                ]

    def _create_control_sequence(self, field, vals):
        return self.env["ir.sequence"].create(
            {
                "name": "control number {} - {}".format(field, vals["sequence_type"]),
                "prefix": "00-",
                "padding": 8,
                "company_id": vals.get("company_id")
                or self.company_id.id
                or self.env.company.id,
            }
        )
