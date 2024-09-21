from odoo import api, models


class FiscalBooksReportHandler(models.AbstractModel):
    _inherit = "account.fiscal.books.report.handler"

    @api.model
    def get_headers(self, options):
        headers = super(__class__, self).get_headers(options)
        if options["file_type"] == "sale":
            headers[-1].insert(5, {"name": "Serie", "key": "serie"})
        return headers

    @api.model
    def _select(self, options):
        query = super(__class__, self)._select(options)
        if options["file_type"] == "sale":
            query += """, account_move.serie AS serie"""
        return query
