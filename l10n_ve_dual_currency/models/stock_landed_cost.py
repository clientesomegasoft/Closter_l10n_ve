from odoo import fields, models


class StockLandedCost(models.Model):
    _inherit = "stock.landed.cost"

    def button_validate(self):
        res = super(StockLandedCost, self).button_validate()
        for cost in self:
            if cost.account_move_id:
                cost.account_move_id.global_rate_ref = False
        return res


class StockLandedCostLine(models.Model):
    _inherit = "stock.landed.cost.lines"

    currency_ref_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_ref_id.id,
        required=True,
    )
    currency_rate_ref = fields.Many2one(
        comodel_name="res.currency.rate",
        string="Tasa de cambio",
        ondelete="restrict",
        required=True,
        default=lambda self: self.env.company.currency_ref_id.get_currency_rate(),
        domain="[('currency_id', '=', currency_ref_id)]",
    )


class AdjustmentLines(models.Model):
    _inherit = "stock.valuation.adjustment.lines"

    def _create_accounting_entries(self, move, qty_out):
        res = super(AdjustmentLines, self)._create_accounting_entries(move, qty_out)
        for line in res:
            line[2]["currency_rate_ref"] = self.cost_line_id.currency_rate_ref.id
        return res
