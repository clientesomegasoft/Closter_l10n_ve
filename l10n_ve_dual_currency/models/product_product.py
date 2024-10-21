from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero, float_repr, float_round


class ProductProduct(models.Model):
    _inherit = "product.product"

    standard_price_ref = fields.Float(
        string="Coste op.", company_dependent=True, digits="Product Price"
    )
    value_svl_ref = fields.Float(compute="_compute_value_svl", compute_sudo=True)
    avg_cost_ref = fields.Monetary(
        string="Costo unitario op.",
        compute="_compute_value_svl",
        compute_sudo=True,
        currency_field="cost_currency_ref_id",
    )
    total_value_ref = fields.Monetary(
        string="Valor total op.",
        compute="_compute_value_svl",
        compute_sudo=True,
        currency_field="cost_currency_ref_id",
    )

    def write(self, vals):
        if "standard_price" in vals and "standard_price_ref" not in vals:
            vals["standard_price_ref"] = (
                vals["standard_price"] * self.cost_currency_ref_id.rate
            )
        elif "standard_price_ref" in vals and "standard_price" not in vals:
            vals["standard_price"] = (
                vals["standard_price_ref"] / self.cost_currency_ref_id.rate
            )
        return super().write(vals)

    @api.depends("stock_valuation_layer_ids")
    @api.depends_context("to_date", "company")
    def _compute_value_svl(self):
        """Compute totals of multiple svl related values"""
        company_id = self.env.company
        self.company_currency_id = company_id.currency_id
        domain = [
            ("product_id", "in", self.ids),
            ("company_id", "=", company_id.id),
        ]
        if self.env.context.get("to_date"):
            to_date = fields.Datetime.to_datetime(self.env.context["to_date"])
            domain.append(("create_date", "<=", to_date))
        groups = self.env["stock.valuation.layer"]._read_group(
            domain, ["value:sum", "value_ref:sum", "quantity:sum"], ["product_id"]
        )
        products = self.browse()
        # Browse all products and compute products' quantities_dict in batch.
        self.env["product.product"].browse(
            [group["product_id"][0] for group in groups]
        ).sudo(False).mapped("qty_available")
        for group in groups:
            product = self.browse(group["product_id"][0])
            value_svl = company_id.currency_id.round(group["value"])
            value_svl_ref = company_id.currency_ref_id.round(group["value_ref"])
            avg_cost = value_svl / group["quantity"] if group["quantity"] else 0
            avg_cost_ref = value_svl_ref / group["quantity"] if group["quantity"] else 0
            product.value_svl = value_svl
            product.value_svl_ref = value_svl_ref
            product.quantity_svl = group["quantity"]
            if not avg_cost and product.sudo(False).qty_available > 0:
                avg_cost = (
                    product.standard_price_ref / self.env.company.currency_ref_id.rate
                )
            if not avg_cost_ref and product.sudo(False).qty_available > 0:
                avg_cost_ref = (
                    product.standard_price * self.env.company.currency_ref_id.rate
                )
            product.avg_cost = avg_cost
            product.avg_cost_ref = avg_cost_ref
            product.total_value = avg_cost * product.sudo(False).qty_available
            product.total_value_ref = avg_cost_ref * product.sudo(False).qty_available
            products |= product
        remaining = self - products
        remaining.value_svl = 0
        remaining.value_svl_ref = 0
        remaining.quantity_svl = 0
        remaining.avg_cost = 0
        remaining.avg_cost_ref = 0
        remaining.total_value = 0
        remaining.total_value_ref = 0

    def _prepare_in_svl_vals(self, quantity, unit_cost):
        company = self.env["res.company"].browse(
            self.env.context.get("force_company", self.env.company.id)
        )
        vals = super()._prepare_in_svl_vals(quantity, unit_cost)
        value_ref = company.currency_ref_id.round(
            unit_cost * quantity * company.currency_ref_id.rate
        )
        vals.update(
            {
                "value_ref": value_ref,
                "unit_cost_ref": company.currency_ref_id.round(
                    unit_cost * company.currency_ref_id.rate
                ),
                "remaining_value_ref": value_ref,
            }
        )
        return vals

    def _prepare_out_svl_vals(self, quantity, company):
        """Prepare the values for a stock valuation layer created by a delivery.

        :param quantity: the quantity to value, expressed in `self.uom_id`
        :return: values to use in a call to create
        :rtype: dict
        """
        self.ensure_one()
        company_id = self.env.context.get("force_company", self.env.company.id)
        company = self.env["res.company"].browse(company_id)
        currency = company.currency_id
        # Quantity is negative for out valuation layers.
        quantity = -1 * quantity
        vals = {
            "product_id": self.id,
            "value": currency.round(quantity * self.standard_price),
            "value_ref": company.currency_ref_id.round(
                quantity * self.standard_price_ref
            ),
            "unit_cost": self.standard_price,
            "unit_cost_ref": self.standard_price_ref,
            "quantity": quantity,
        }
        fifo_vals = self._run_fifo(abs(quantity), company)
        vals["remaining_qty"] = fifo_vals.get("remaining_qty")
        # In case of AVCO, fix rounding issue of standard price when needed.
        if self.product_tmpl_id.cost_method == "average" and not float_is_zero(
            self.quantity_svl, precision_rounding=self.uom_id.rounding
        ):
            rounding_error = currency.round(
                (self.standard_price * self.quantity_svl - self.value_svl)
                * abs(quantity / self.quantity_svl)
            )
            if rounding_error:
                # If it is bigger than the (smallest number
                # of the currency * quantity) / 2, then it isn't
                # a rounding error but a stock valuation error,
                # we shouldn't fix it under the hood ...
                if abs(rounding_error) <= max(
                    (abs(quantity) * currency.rounding) / 2, currency.rounding
                ):
                    vals["value"] += rounding_error
                    vals[
                        "rounding_adjustment"
                    ] = "\nRounding Adjustment: {}{} {}".format(
                        "+" if rounding_error > 0 else "",
                        float_repr(
                            rounding_error, precision_digits=currency.decimal_places
                        ),
                        currency.symbol,
                    )
        if self.product_tmpl_id.cost_method == "fifo":
            vals.update(fifo_vals)
        return vals

    def _change_standard_price(self, new_price):
        """Helper to create the stock valuation layers and the account moves
        after an update of standard price.

        :param new_price: new standard price
        """
        # Handle stock valuation layers.

        if self.filtered(lambda p: p.valuation == "real_time") and not self.env[
            "stock.valuation.layer"
        ].check_access_rights("read", raise_exception=False):
            raise UserError(
                _(
                    "You cannot update the cost of a product in automated "
                    "valuation as it leads to the creation of a journal entry, "
                    "for which you don't have the access rights."
                )
            )

        svl_vals_list = []
        company_id = self.env.company
        price_unit_prec = self.env["decimal.precision"].precision_get("Product Price")
        rounded_new_price = float_round(new_price, precision_digits=price_unit_prec)
        rounded_new_price_ref = float_round(
            new_price * company_id.currency_ref_id.rate,
            precision_digits=price_unit_prec,
        )

        for product in self:
            if product.cost_method not in ("standard", "average"):
                continue
            quantity_svl = product.sudo().quantity_svl
            if (
                float_compare(
                    quantity_svl, 0.0, precision_rounding=product.uom_id.rounding
                )
                <= 0
            ):
                continue

            value = company_id.currency_id.round(
                (rounded_new_price * quantity_svl) - product.sudo().value_svl
            )
            value_ref = company_id.currency_ref_id.round(
                (rounded_new_price_ref * quantity_svl) - product.sudo().value_svl_ref
            )

            if company_id.currency_id.is_zero(
                value
            ) and company_id.currency_ref_id.is_zero(value_ref):
                continue
            elif company_id.currency_id.is_zero(value):
                description = _(
                    "Product value manually modified (from %(standard_price_ref)s to %(rounded_new_price_ref)s)",
                    standard_price_ref=product.standard_price_ref,
                    rounded_new_price_ref=rounded_new_price_ref,
                )
            else:
                description = _(
                    "Product value manually modified (from %(standard_price)s to %(rounded_new_price)s)",
                    standard_price=product.standard_price,
                    rounded_new_price=rounded_new_price,
                )

            svl_vals = {
                "company_id": company_id.id,
                "product_id": product.id,
                "description": description,
                "value": value,
                "value_ref": value_ref,
                "quantity": 0,
            }
            svl_vals_list.append(svl_vals)
        stock_valuation_layers = (
            self.env["stock.valuation.layer"].sudo().create(svl_vals_list)
        )

        # Handle account moves.
        product_accounts = {
            product.id: product.product_tmpl_id.get_product_accounts()
            for product in self
        }
        am_vals_list = []
        for stock_valuation_layer in stock_valuation_layers:
            product = stock_valuation_layer.product_id
            value = stock_valuation_layer.value
            value_ref = stock_valuation_layer.value_ref

            if product.type != "product" or product.valuation != "real_time":
                continue

            # Sanity check.
            if not product_accounts[product.id].get("expense"):
                raise UserError(
                    _("You must set a counterpart account on your product category.")
                )
            if not product_accounts[product.id].get("stock_valuation"):
                raise UserError(
                    _(
                        "You don't have any stock valuation account defined "
                        "on your product category. You must define one before "
                        "processing this operation."
                    )
                )

            if value < 0 or value_ref < 0:
                debit_account_id = product_accounts[product.id]["expense"].id
                credit_account_id = product_accounts[product.id]["stock_valuation"].id
            else:
                debit_account_id = product_accounts[product.id]["stock_valuation"].id
                credit_account_id = product_accounts[product.id]["expense"].id

            move_vals = {
                "journal_id": product_accounts[product.id]["stock_journal"].id,
                "company_id": company_id.id,
                "ref": product.default_code,
                "stock_valuation_layer_ids": [(6, None, [stock_valuation_layer.id])],
                "move_type": "entry",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": _(
                                "%(user)s changed cost from %(previous)s to %(new_price)s - %(product)s",
                                user=self.env.user.name,
                                previous=product.standard_price,
                                new_price=new_price,
                                product=product.display_name,
                            ),
                            "account_id": debit_account_id,
                            "debit": abs(value),
                            "credit": 0,
                            "balance_ref": abs(value_ref),
                            "product_id": product.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": _(
                                "%(user)s changed cost from %(previous)s to %(new_price)s - %(product)s",
                                user=self.env.user.name,
                                previous=product.standard_price,
                                new_price=new_price,
                                product=product.display_name,
                            ),
                            "account_id": credit_account_id,
                            "debit": 0,
                            "credit": abs(value),
                            "balance_ref": -abs(value_ref),
                            "product_id": product.id,
                        },
                    ),
                ],
            }
            am_vals_list.append(move_vals)

        account_moves = (
            self.env["account.move"]
            .sudo()
            .with_context(skip_compute_balance_ref=True)
            .create(am_vals_list)
        )
        if account_moves:
            account_moves._post()

    def _run_fifo(self, quantity, company):
        self.ensure_one()

        # Find back incoming stock valuation layers
        # (called candidates here) to value `quantity`.
        qty_to_take_on_candidates = quantity
        candidates = (
            self.env["stock.valuation.layer"]
            .sudo()
            .search(
                [
                    ("product_id", "=", self.id),
                    ("remaining_qty", ">", 0),
                    ("company_id", "=", company.id),
                ]
            )
        )
        new_standard_price = 0
        new_standard_price_ref = 0
        tmp_value = 0  # to accumulate the value taken on the candidates
        tmp_value_ref = 0

        for candidate in candidates:
            qty_taken_on_candidate = min(
                qty_to_take_on_candidates, candidate.remaining_qty
            )

            candidate_unit_cost = candidate.remaining_value / candidate.remaining_qty
            candidate_unit_cost_ref = (
                candidate.remaining_value_ref / candidate.remaining_qty
            )
            new_standard_price = candidate_unit_cost
            new_standard_price_ref = candidate_unit_cost_ref
            value_taken_on_candidate = qty_taken_on_candidate * candidate_unit_cost
            value_taken_on_candidate = candidate.currency_id.round(
                value_taken_on_candidate
            )
            value_taken_on_candidate_ref = candidate.currency_ref_id.round(
                qty_taken_on_candidate * candidate_unit_cost_ref
            )
            new_remaining_value = candidate.remaining_value - value_taken_on_candidate
            new_remaining_value_ref = (
                candidate.remaining_value_ref - value_taken_on_candidate_ref
            )

            candidate_vals = {
                "remaining_qty": candidate.remaining_qty - qty_taken_on_candidate,
                "remaining_value": new_remaining_value,
                "remaining_value_ref": new_remaining_value_ref,
            }

            candidate.write(candidate_vals)

            qty_to_take_on_candidates -= qty_taken_on_candidate
            tmp_value += value_taken_on_candidate
            tmp_value_ref += value_taken_on_candidate_ref

            if float_is_zero(
                qty_to_take_on_candidates, precision_rounding=self.uom_id.rounding
            ):
                if float_is_zero(
                    candidate.remaining_qty, precision_rounding=self.uom_id.rounding
                ):
                    next_candidates = candidates.filtered(
                        lambda svl: svl.remaining_qty > 0
                    )
                    new_standard_price = (
                        next_candidates
                        and next_candidates[0].unit_cost
                        or new_standard_price
                    )
                    new_standard_price_ref = (
                        next_candidates
                        and next_candidates[0].unit_cost_ref
                        or new_standard_price_ref
                    )
                break

        # Update the standard price with the price of the last used candidate, if any.
        values = {}
        if self.cost_method == "fifo":
            if new_standard_price:
                values["standard_price"] = new_standard_price
            if new_standard_price_ref:
                values["standard_price_ref"] = new_standard_price_ref
        if values:
            self.sudo().with_company(company.id).with_context(
                disable_auto_svl=True
            ).write(values)

        # If there's still quantity to value but we're out of candidates, we fall in the
        # negative stock use case. We chose to value the out move at the price of the
        # last out and a correction entry will be made once `_fifo_vacuum` is called.
        vals = {}
        if float_is_zero(
            qty_to_take_on_candidates, precision_rounding=self.uom_id.rounding
        ):
            vals = {
                "value": -tmp_value,
                "value_ref": -tmp_value_ref,
                "unit_cost": tmp_value / quantity,
                "unit_cost_ref": tmp_value_ref / quantity,
            }
        else:
            assert qty_to_take_on_candidates > 0
            last_fifo_price = new_standard_price or self.standard_price
            last_fifo_price_ref = new_standard_price_ref or self.standard_price_ref
            negative_stock_value = last_fifo_price * -qty_to_take_on_candidates
            negative_stock_value_ref = last_fifo_price_ref * -qty_to_take_on_candidates
            tmp_value += abs(negative_stock_value)
            tmp_value_ref += abs(negative_stock_value_ref)
            vals = {
                "remaining_qty": -qty_to_take_on_candidates,
                "value": -tmp_value,
                "value_ref": -tmp_value_ref,
                "unit_cost": last_fifo_price,
                "unit_cost_ref": last_fifo_price_ref,
            }
        return vals
