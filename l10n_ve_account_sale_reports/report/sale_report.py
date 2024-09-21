from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    price_subtotal_ref = fields.Float(string="Untaxed Total Ref", readonly=True)

    untaxed_amount_to_invoice_ref = fields.Float(
        string="Untaxed Amount To Invoice Ref", readonly=True
    )

    untaxed_amount_invoiced_ref = fields.Float(
        string="Untaxed Amount Invoiced Ref", readonly=True
    )

    discount_amount_ref = fields.Float(string="Discount Amount Ref", readonly=True)

    margin_ref = fields.Float(string="Margin Ref", readonly=True)

    price_total_ref = fields.Float(string="Total Ref", readonly=True)

    def _select_additional_fields(self):
        res = super()._select_additional_fields()

        res.update(
            {
                "price_subtotal_ref": f"""
                (CASE WHEN l.product_id IS NOT NULL
                    THEN SUM(l.price_subtotal
                        / {self._case_value_or_one('s.currency_rate')}
                        * {self._case_value_or_one('currency_table.rate')})
                    ELSE 0
                END) * {self._case_value_or_one('operative_currency_table.rate')}
            """,
                "untaxed_amount_to_invoice_ref": f"""
                (CASE WHEN l.product_id IS NOT NULL
                    THEN SUM(l.untaxed_amount_to_invoice
                        / {self._case_value_or_one('s.currency_rate')}
                        * {self._case_value_or_one('currency_table.rate')})
                    ELSE 0
                END) * {self._case_value_or_one('operative_currency_table.rate')}
                """,
                "untaxed_amount_invoiced_ref": f"""
                (CASE WHEN l.product_id IS NOT NULL
                    THEN SUM(l.untaxed_amount_invoiced
                        / {self._case_value_or_one('s.currency_rate')}
                        * {self._case_value_or_one('currency_table.rate')})
                    ELSE 0
                END) * {self._case_value_or_one('operative_currency_table.rate')}
                """,
                "discount_amount_ref": f"""
                (CASE WHEN l.product_id IS NOT NULL
                    THEN SUM(l.price_unit * l.product_uom_qty * l.discount / 100.0
                        / {self._case_value_or_one('s.currency_rate')}
                        * {self._case_value_or_one('currency_table.rate')})
                    ELSE 0
                END) * {self._case_value_or_one('operative_currency_table.rate')}
                """,
                "margin_ref": f"""
                SUM(l.margin
                    / {self._case_value_or_one('s.currency_rate')}
                    * {self._case_value_or_one('currency_table.rate')})
                * {self._case_value_or_one('operative_currency_table.rate')}
                """,
                "price_total_ref": f"""
                (CASE WHEN l.product_id IS NOT NULL
                    THEN SUM(l.price_total
                        / {self._case_value_or_one('s.currency_rate')}
                    * {self._case_value_or_one('currency_table.rate')})
                ELSE 0
                END) * {self._case_value_or_one('operative_currency_table.rate')}
                """,
            }
        )
        return res

    def _from_sale(self):
        statement = super(__class__, self)._from_sale()
        operative_currency_table = self.env[
            "res.currency"
        ]._get_query_currency_ref_table(
            {"multi_company": True, "date": {"date_to": fields.Date.today()}}
        )

        statement = f"""
            {statement}
            JOIN {operative_currency_table} ON operative_currency_table.company_id = s.company_id
        """
        return statement

    def _group_by_sale(self):
        statement = super(__class__, self)._group_by_sale()
        statement = f"""
            {statement},
            operative_currency_table.rate
        """
        return statement
