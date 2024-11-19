from odoo import _, fields, models
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = "res.company"

    currency_ref_id = fields.Many2one(
        comodel_name="res.currency",
        string="Operating currency",
        required=True,
        default=lambda self: self._default_currency_id(),
    )
    fiscal_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Fiscal currency",
        required=True,
        domain="[('id', 'in', (currency_id, currency_ref_id))]",
        default=lambda self: self._default_currency_id(),
    )

    def write(self, values):
        for company in self:
            if (
                "currency_ref_id" in values
                and values["currency_ref_id"] != company.currency_ref_id.id
            ) or (
                "fiscal_currency_id" in values
                and values["fiscal_currency_id"] != company.fiscal_currency_id.id
            ):
                if self.env["account.move.line"].search(
                    [("company_id", "=", company.id)], limit=1
                ):
                    raise UserError(
                        _(
                            "¡No puedes cambiar la moneda operativa / fiscal "
                            "de la compañía ya que existen asientos contables!"
                        )
                    )
        return super(__class__, self).write(values)
