import base64

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class WithholdingIVATXT(models.Model):
    _name = "account.withholding.iva.txt"
    _description = "Withholding IVA TXT"

    name = fields.Char(
        "Descripción",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    start_date = fields.Date(
        string="Desde",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    end_date = fields.Date(
        string="Hasta",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("posted", "Publicado"),
            ("cancel", "Cancelado"),
        ],
        default="draft",
    )
    filename = fields.Char()
    file = fields.Binary(readonly=True, string="Archivo TXT")
    line_ids = fields.One2many(
        "account.withholding.iva",
        "txt_id",
        string="Líneas",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    tax_amount = fields.Monetary(
        string="Impuesto", compute="_compute_amount", store=True
    )
    amount = fields.Monetary(
        string="Monto retenido", compute="_compute_amount", store=True
    )
    total_amount = fields.Monetary(
        string="Monto a declarar", compute="_compute_amount", store=True
    )
    currency_id = fields.Many2one(related="company_id.fiscal_currency_id")
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company.id,
        readonly=True,
    )

    @api.depends("line_ids.tax_amount", "line_ids.amount")
    def _compute_amount(self):
        for rec in self:
            tax_amount = amount = total_amount = 0.0
            for line in rec.line_ids:
                tax_amount += line.tax_amount
                amount += line.amount
                total_amount += (
                    line.amount
                    if line.invoice_id.move_type == "in_invoice"
                    else -line.amount
                )
            rec.tax_amount = tax_amount
            rec.amount = amount
            rec.total_amount = total_amount

    def seek_for_lines(self):
        self.ensure_one()
        lines = self.env["account.withholding.iva"].search(
            [
                ("state", "=", "posted"),
                ("txt_state", "!=", "posted"),
                ("type", "=", "supplier"),
                ("date", ">=", self.start_date),
                ("date", "<=", self.end_date),
                ("company_id", "=", self.company_id.id),
            ]
        )
        self.line_ids = [Command.set(lines.ids)]

    def button_post(self):
        self.file = base64.encodebytes("\n".join(self._generate_txt_data()).encode())
        self.filename = f"IVA_{fields.Datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.txt"
        self.write({"state": "posted"})

    def button_draft(self):
        self.write({"state": "draft"})

    def button_cancel(self):
        self.write({"state": "cancel"})

    def unlink(self):
        for rec in self:
            if rec.state != "cancel":
                raise UserError(
                    _("Solo TXT en estado Cancelado pueden ser suprimidos.")
                )
        return super().unlink()

    def _generate_txt_data(self):
        def format(amount):  # pylint: disable=redefined-builtin
            return f"{amount:.2f}"

        def get_origin_document(invoice):
            if invoice.debit_origin_id:
                return invoice.debit_origin_id.supplier_invoice_number
            if invoice.move_type == "in_refund":
                return invoice.reversed_entry_id.supplier_invoice_number
            return "0"

        data = []
        period = self.start_date.strftime("%Y%m")
        for withholding_id in self.line_ids:
            invoice = withholding_id.invoice_id
            agent_rif = withholding_id.agent_id.vat.replace("-", "")
            invoice_date = withholding_id.invoice_date.strftime("%Y-%m-%d")
            subject_rif = withholding_id.subject_id.vat.replace("-", "")
            origin_document = get_origin_document(invoice)
            exempt_amount = withholding_id.exempt_amount
            for line in withholding_id.line_ids:
                data.append(
                    "\t".join(
                        (
                            agent_rif,
                            period,
                            invoice_date,
                            "C",
                            invoice.fiscal_transaction_type[-2:],
                            subject_rif,
                            invoice.supplier_invoice_number,
                            invoice.nro_ctrl,
                            format(
                                line.tax_base_amount + line.tax_amount + exempt_amount
                            ),
                            format(line.tax_base_amount),
                            format(line.amount),
                            origin_document,
                            withholding_id.name,
                            format(exempt_amount),
                            format(line.tax_line_id.amount),
                            "0",
                        )
                    )
                )
                exempt_amount = 0.0
        return data
