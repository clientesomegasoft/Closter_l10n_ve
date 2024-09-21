from odoo import Command, api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    liquor_tax_ids = fields.Many2many(
        "account.liquor.tax", string="Impuestos por venta de licor", ondelete="restrict"
    )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    liquor_tax_ids = fields.Many2many(
        "account.liquor.tax", string="Impuestos por venta de licor", readonly=True
    )

    @api.onchange("product_id")
    def _onchange_liquor_tax_ids(self):
        self.liquor_tax_ids = [Command.set(self.product_id.liquor_tax_ids.ids)]

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res["liquor_tax_ids"] = [Command.set(self.liquor_tax_ids.ids)]
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    liquor_tax_ids = fields.Many2many(
        "account.liquor.tax",
        "liquor_tax_move_line_rel",
        "line_id",
        "tax_id",
        string="Impuestos por venta de licor",
        readonly=True,
    )

    @api.onchange("product_id")
    def _onchange_liquor_tax_ids(self):
        if self.move_type in ("out_invoice", "out_refund"):
            self.liquor_tax_ids = [Command.set(self.product_id.liquor_tax_ids.ids)]
