import logging

import pytz

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


def to_utc(value, origin_tz="UTC"):
    return (
        origin_tz
        and pytz.timezone(origin_tz).localize(value).astimezone(pytz.UTC)
        or value
    ).replace(tzinfo=None)


class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    inverse_company_rate = fields.Float(search="_search_inverse_company_rate")

    def _search_inverse_company_rate(self, operator, value):
        if operator not in (">", "<", "=", "!="):
            raise UserError(_("Operation not supported"))

        value = 1.0 / value
        epsilon = 0.0001

        # NOTE: (3) Also note that even if we use a comparison based on epsilon values
        #           we cannot ensure that we will have a single record for the required
        #           field during the import process
        if operator in ("=", "!="):
            domain = [
                "&",
                ("rate", ">", value - epsilon),
                ("rate", "<", value + epsilon),
            ]
            if operator == "!=":
                domain.insert(0, "!")
        else:
            domain = [("rate", operator, value)]

        return domain

    def name_get(self):
        # NOTE: In this way, we ensure that exports will always return a valid rate
        if not self.env.context.get("import_compat"):
            return super(__class__, self).name_get()

        return [(currency.id, tools.ustr(currency.name)) for currency in self]

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        def infer_datetime(name):
            name = self._fields["name"].convert_to_write(name, self)
            tz = self._context.get("tz", self.env.user.tz) or "UTC"
            if self.env.context.get("convert_date_to_utc"):
                name = to_utc(name, tz)
            return [("name", "=", name)]

        def infer_rate(name):
            name = self._fields["rate"].convert_to_write(name, self)
            field = "rate"

            # NOTE: (1) This exchange rule may change in the future
            # NOTE: (2) It's not recommended to use this inference because it
            #           may lead to inconsistences or unexpected behavior during
            #           the import process
            comparison = float_compare(abs(name), 1.0, precision_digits=2)
            if comparison > 0:
                # We assume that the value is actually an inversed ratio
                # because the company_id worth less than the company_ref_id
                # usually.
                field = "inverse_company_rate"

            return [
                ("currency_id", "=", self.env.company.currency_ref_id.id),
                (field, "=", name),
            ]

        # TODO: Move to an overridable function maybe?
        inference_criteria = {
            "name": infer_datetime,
            "rate": infer_rate,
        }

        args = list(args or [])
        search_fnames = self._rec_names_search or (
            [self._rec_name] if self._rec_name else []
        )

        # NOTE: We cannot let odoo decide how to treat the
        #       fields manually because any search made in
        #       multiple non compatible fields will trigger
        #       a ValueError Exception
        #       For example: `rate` and `name` for this model
        #       which have the types Float and Datetime
        #       respectively.
        if not search_fnames:
            _logger.warning(
                "Cannot execute name_search, no _rec_name "
                "or _rec_names_search defined on %s",
                self._name,
            )

        elif not (name == "" and operator in ("like", "ilike")):
            aggregator = (
                expression.AND
                if operator in expression.NEGATIVE_TERM_OPERATORS
                else expression.OR
            )
            domains = []
            for field in search_fnames:
                try:
                    domain = inference_criteria[field](name)
                    domains.append(domain)
                except ValueError:
                    pass
            args += aggregator(domains)
        return self._search(args, limit=limit, access_rights_uid=name_get_uid)
