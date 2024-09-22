from odoo import api, fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    price_subtotal_ref = fields.Float(string="Untaxed Total Ref", readonly=True)

    price_total_ref = fields.Float(string="Total Ref", readonly=True)

    price_average_ref = fields.Float(
        string="Average Price Ref", group_operator="avg", readonly=True
    )

    @api.model
    def _select(self):
        statement = super(__class__, self)._select()

        # Firstly, we convert the values to the ones
        # represented in the company's currency,
        # then whe convert them to the operative
        # currency as expects the temporary table
        # `operative_currency_table`.
        statement = f"""
            {statement},
            (-line.balance * currency_table.rate) * operative_currency_table.rate AS price_subtotal_ref,
            (line.price_total * (CASE
                    WHEN move.move_type IN ('in_invoice','out_refund','in_receipt')
                        THEN -1
                        ELSE 1 END))
                * operative_currency_table.rate AS price_total_ref,

            -- TODO: FIX THE FOLLOWING FIELD: `price_average_ref`. It's mid
            (-COALESCE(
                    -- Average line price
                    (line.balance / NULLIF(line.quantity, 0.0))
                        * (CASE
                            WHEN move.move_type IN ('in_invoice','out_refund','in_receipt')
                                THEN -1
                                ELSE 1 END)
                    -- convert to template uom
                    * (NULLIF(COALESCE(uom_line.factor, 1), 0.0)
                        / NULLIF(COALESCE(uom_template.factor, 1), 0.0)),
                    0.0) * currency_table.rate)
                * operative_currency_table.rate AS price_average_ref
        """
        return statement

    @api.model
    def _from(self):
        statement = super(__class__, self)._from()
        operative_currency_table = self.env[
            "res.currency"
        ]._get_query_currency_ref_table(
            {"multi_company": True, "date": {"date_to": fields.Date.today()}}
        )

        statement = f"""
            {statement}
            JOIN {operative_currency_table} ON operative_currency_table.company_id = line.company_id
        """
        return statement
