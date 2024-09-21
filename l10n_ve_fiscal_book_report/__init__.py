from . import models
from odoo import api, SUPERUSER_ID


def _set_invoices(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["account.move"].search([]).write({"not_in_fiscal_book": False})
