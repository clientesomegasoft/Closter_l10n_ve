import base64
import re

from lxml import etree

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class WithholdingISLRXML(models.Model):
    _name = "account.withholding.islr.xml"
    _description = "Withholding ISLR XML"

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
    file = fields.Binary(readonly=True, string="Archivo XML")
    line_ids = fields.One2many(
        "account.withholding.islr",
        "xml_id",
        string="Líneas",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    amount = fields.Monetary(
        string="Monto retenido", compute="_compute_amount", store=True
    )
    currency_id = fields.Many2one(
        "res.currency", related="company_id.fiscal_currency_id", store=True
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
        readonly=True,
    )

    @api.depends("line_ids.amount")
    def _compute_amount(self):
        for rec in self:
            amount = 0.0
            for line in rec.line_ids:
                amount += line.amount
            rec.amount = amount

    def seek_for_lines(self):
        for rec in self:
            lines = self.env["account.withholding.islr"].search(
                [
                    ("type", "=", "supplier"),
                    ("state", "=", "posted"),
                    ("xml_state", "!=", "posted"),
                    ("date", ">=", rec.start_date),
                    ("date", "<=", rec.end_date),
                    ("company_id", "=", rec.company_id.id),
                ]
            )
            rec.line_ids = [Command.set(lines.ids)]

    def button_post(self):
        self.file = base64.encodebytes(self._generate_xml_data())
        self.filename = (
            f"ISLR_{fields.Datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.xml"
        )
        self.write({"state": "posted"})

    def button_draft(self):
        self.write({"state": "draft"})

    def button_cancel(self):
        self.write({"state": "cancel"})

    def unlink(self):
        for rec in self:
            if rec.state != "cancel":
                raise UserError(
                    _("Solo XML en estado Cancelado pueden ser suprimidos."))
        return super().unlink()

    def _generate_xml_data(self):
        root = etree.Element(
            "RelacionRetencionesISLR",
            Periodo=self.start_date.strftime("%Y%m"),
            RifAgente=self.company_id.vat.replace("-", ""),
        )

        for withholding_id in self.line_ids:
            invoice = withholding_id.invoice_id
            subject_rif = withholding_id.subject_id.vat.replace("-", "")
            date = withholding_id.date.strftime("%d/%m/%Y")

            for line in withholding_id.line_ids:
                header = etree.SubElement(root, "DetalleRetencion")
                child = etree.SubElement(header, "RifRetenido")
                child.text = subject_rif
                header.append(child)
                child = etree.SubElement(header, "NumeroFactura")
                child.text = re.sub(r"[^0-9]", "", invoice.supplier_invoice_number)
                header.append(child)
                child = etree.SubElement(header, "NumeroControl")
                child.text = re.sub(r"[^0-9]", "", invoice.nro_ctrl)
                header.append(child)
                child = etree.SubElement(header, "FechaOperacion")
                child.text = date
                header.append(child)
                child = etree.SubElement(header, "CodigoConcepto")
                child.text = line.rate_id.name
                header.append(child)
                child = etree.SubElement(header, "MontoOperacion")
                child.text = "%.2f" % line.base_amount
                header.append(child)
                child = etree.SubElement(header, "PorcentajeRetencion")
                child.text = "%.2f" % line.percent
                header.append(child)

        return etree.tostring(
            root, pretty_print=True, xml_declaration=True, encoding="utf-8"
        )
