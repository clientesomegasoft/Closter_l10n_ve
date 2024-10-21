import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import format_amount

from .tools import to_datetime


class Currency(models.Model):
    _inherit = "res.currency"

    def _get_rates(self, company, date):
        return super(__class__, self)._get_rates(
            company, to_datetime(date, tz=self._context.get("tz", self.env.user.tz))
        )

    def get_currency_rate(self, date=None):
        self.ensure_one()
        tz = self._context.get("tz", self.env.user.tz) or "UTC"
        self._cr.execute(
            """
            SELECT id
            FROM res_currency_rate
            WHERE name <= %s AND currency_id = %s AND company_id = %s
            ORDER BY DATE(TIMEZONE('UTC', name) AT TIME ZONE %s) DESC, is_bcv_rate DESC NULLS LAST, name DESC
            LIMIT 1
        """,
            [
                to_datetime(date, tz=tz) or fields.Datetime.now(),
                self.id,
                self._context.get("company_id", self.env.company.id),
                tz,
            ],
        )
        rstl = self._cr.fetchone()
        return self.env["res.currency.rate"].browse(rstl and rstl[0])

    def _convert_with_rate(
        self, from_amount, to_currency, company, date, rate=None, round=True
    ):  # pylint: disable=redefined-builtin
        self, to_currency = self or to_currency, to_currency or self
        assert self, "convert amount from unknown currency"
        assert to_currency, "convert amount to unknown currency"
        assert company, "convert amount from unknown company"
        assert date, "convert amount from unknown date"

        if self == to_currency:
            to_amount = from_amount
        elif from_amount:
            if self == company.currency_ref_id and to_currency == company.currency_id:
                to_amount = (
                    from_amount / (rate or to_currency.get_currency_rate(date)).rate
                )
            elif to_currency == company.currency_ref_id:
                to_amount = (
                    self._convert(
                        from_amount, company.currency_id, company, date, round=False
                    )
                    * (rate or to_currency.get_currency_rate(date)).rate
                )
            else:
                to_amount = self._convert(
                    from_amount, company.currency_id, company, date, round=False
                )
        else:
            return 0.0

        return to_currency.round(to_amount) if round else to_amount


class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    name = fields.Datetime(default=fields.Datetime.now)
    is_bcv_rate = fields.Boolean(string="Tasa BCV", default=False)

    @api.constrains("name", "is_bcv_rate")
    def _unique_bcv_rate_per_day(self):
        for rate in self:
            if rate.is_bcv_rate:
                tz = self._context.get("tz", self.env.user.tz)
                self._cr.execute(
                    """
                    SELECT COUNT(*)
                    FROM res_currency_rate
                    WHERE DATE(TIMEZONE('UTC', name) AT TIME ZONE %s) = %s
                        AND is_bcv_rate = TRUE
                        AND currency_id = %s
                        AND company_id = %s
                        AND id != %s
                """,
                    [
                        tz,
                        rate.name.astimezone(pytz.timezone(tz)).date(),
                        rate.currency_id.id,
                        rate.company_id.id,
                        rate.id,
                    ],
                )
                if self._cr.fetchone()[0]:
                    raise UserError(_("Solo se puede almacenar una tasa BCV por dia."))

    def write(self, vals):
        if self.env["account.move.line"].search(
            [("currency_rate_ref", "=", self.id)], limit=1
        ) or self.env["stock.landed.cost.lines"].search(
            [("currency_rate_ref", "=", self.id)], limit=1
        ):
            raise UserError(
                _(
                    "No es posible ejecutar esta acción ya que la "
                    "tasa está siendo utilizada por otro modelo."
                )
            )
        return super(__class__, self).write(vals)

    def name_get(self):
        field = (
            self.env.company.currency_id == self.env.company.fiscal_currency_id
            and "inverse_company_rate"
            or "rate"
        )
        return [
            (
                rate.id,
                format_amount(
                    self.env, getattr(rate, field), self.env.company.fiscal_currency_id
                ),
            )
            for rate in self
        ]
