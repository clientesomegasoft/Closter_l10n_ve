from odoo import api, fields, models, tools


class SaleOrder(models.Model):
    _inherit = "sale.order"

    currency_ref_id = fields.Many2one(related="company_id.currency_ref_id")
    currency_rate_ref = fields.Many2one(
        comodel_name="res.currency.rate",
        string="Tasa de cambio",
        readonly=True,
        tracking=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: self.env.company.currency_ref_id.get_currency_rate(),
        domain="[('currency_id', '=', currency_ref_id)]",
    )

    @api.onchange("currency_rate_ref")
    def _recompute_prices_by_currency_rate_ref(self):
        if self.currency_id.id == self.currency_ref_id.id:
            self._recompute_prices()

    def _prepare_invoice(self):
        vals = super(SaleOrder, self)._prepare_invoice()
        vals["currency_rate_ref"] = self.currency_rate_ref.id
        return vals


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_pricelist_price(self):
        """Compute the price given by the pricelist for the given line information.

        :return: the product sales price in the order currency (without taxes)
        :rtype: float
        """
        self.ensure_one()
        self.product_id.ensure_one()

        pricelist_rule = self.pricelist_item_id
        order_date = self.order_id.date_order or fields.Date.today()
        product = self.product_id.with_context(**self._get_product_price_context())
        qty = self.product_uom_qty or 1.0
        uom = self.product_uom or self.product_id.uom_id

        price = pricelist_rule._compute_price(
            product,
            qty,
            uom,
            order_date,
            currency=self.currency_id,
            currency_rate_ref=self.order_id.currency_rate_ref,
        )

        return price


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def _compute_price(
        self, product, quantity, uom, date, currency=None, currency_rate_ref=None
    ):
        """Compute the unit price of a product in the context of a pricelist application.

        :param product: recordset of product (product.product/product.template)
        :param float qty: quantity of products requested (in given uom)
        :param uom: unit of measure (uom.uom record)
        :param datetime date: date to use for price computation and currency conversions
        :param currency: pricelist currency (for the specific case where self is empty)

        :returns: price according to pricelist rule, expressed in pricelist currency
        :rtype: float
        """
        product.ensure_one()
        uom.ensure_one()

        currency = currency or self.currency_id
        currency.ensure_one()

        # Pricelist specific values are specified according to product UoM
        # and must be multiplied according to the factor between uoms
        product_uom = product.uom_id
        if product_uom != uom:
            convert = lambda p: product_uom._compute_price(p, uom)
        else:
            convert = lambda p: p

        if self.compute_price == "fixed":
            price = convert(self.fixed_price)
        elif self.compute_price == "percentage":
            base_price = self._compute_base_price(
                product, quantity, uom, date, currency, currency_rate_ref
            )
            price = (base_price - (base_price * (self.percent_price / 100))) or 0.0
        elif self.compute_price == "formula":
            base_price = self._compute_base_price(
                product, quantity, uom, date, currency, currency_rate_ref
            )
            # complete formula
            price_limit = base_price
            price = (base_price - (base_price * (self.price_discount / 100))) or 0.0
            if self.price_round:
                price = tools.float_round(price, precision_rounding=self.price_round)

            if self.price_surcharge:
                price += convert(self.price_surcharge)

            if self.price_min_margin:
                price = max(price, price_limit + convert(self.price_min_margin))

            if self.price_max_margin:
                price = min(price, price_limit + convert(self.price_max_margin))
        else:  # empty self, or extended pricelist price computation logic
            price = self._compute_base_price(
                product, quantity, uom, date, currency, currency_rate_ref
            )

        return price

    def _compute_base_price(
        self, product, quantity, uom, date, target_currency, currency_rate_ref=None
    ):
        """Compute the base price for a given rule

        :param product: recordset of product (product.product/product.template)
        :param float qty: quantity of products requested (in given uom)
        :param uom: unit of measure (uom.uom record)
        :param datetime date: date to use for price computation and currency conversions
        :param target_currency: pricelist currency

        :returns: base price, expressed in provided pricelist currency
        :rtype: float
        """
        target_currency.ensure_one()

        rule_base = self.base or "list_price"
        if rule_base == "pricelist" and self.base_pricelist_id:
            price = self.base_pricelist_id._get_product_price(
                product, quantity, uom, date
            )
            src_currency = self.base_pricelist_id.currency_id
        elif rule_base == "standard_price":
            src_currency = product.cost_currency_id
            price = product.price_compute(rule_base, uom=uom, date=date)[product.id]
        elif target_currency == self.env.company.currency_ref_id:  # list_price_ref
            src_currency = product.currency_ref_id
            price = product.price_compute("list_price_ref", uom=uom, date=date)[
                product.id
            ]
        else:  # list_price
            src_currency = product.currency_id
            price = product.price_compute(rule_base, uom=uom, date=date)[product.id]

        if src_currency != target_currency:
            if (
                target_currency == self.env.company.currency_ref_id
                and currency_rate_ref
            ):
                price = price * currency_rate_ref.rate
            else:
                price = src_currency._convert(
                    price, target_currency, self.env.company, date, round=False
                )

        return price
