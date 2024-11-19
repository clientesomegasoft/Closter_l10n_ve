from odoo import api, models


class ResCurrency(models.Model):
    _inherit = "res.currency"

    @api.model
    def _get_query_currency_ref_table(self, options):
        """
        Buils a currency table that models a relationships with the form:
            company -> rate
        In order to convert any amount of the user's company to any required
        target currency.

        :param options: The report options.
        :return:        The query representing the currency table. This temporal table
                        will be called as operative_currency_table.

        SEE ALSO: _get_query_currency_table
        """

        # Basically we renamed the references to the field
        # currency_id by currency_ref_id
        user_company = self.env.company
        user_currency = user_company.currency_ref_id
        if options.get("multi_company", False):
            companies = self.env.companies
            conversion_date = options["date"]["date_to"]
            currency_rates = companies.mapped("currency_ref_id")._get_rates(
                user_company, conversion_date
            )
        else:
            companies = user_company
            currency_rates = {user_currency.id: 1.0}

        conversion_rates = []
        for company in companies:
            conversion_rates.extend(
                (
                    company.id,
                    # This is the rate to perform the following conversion:
                    #   company.currency_id -> company_.currency_ref_id
                    currency_rates[user_company.currency_ref_id.id],
                    user_currency.decimal_places,
                )
            )
        query = (
            "(VALUES %s) AS operative_currency_table(company_id, rate, precision)"
            % ",".join("(%s, %s, %s)" for i in companies)
        )
        return self.env.cr.mogrify(query, conversion_rates).decode(
            self.env.cr.connection.encoding
        )
