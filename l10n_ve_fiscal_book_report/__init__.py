from . import models
from odoo import SUPERUSER_ID, api


def _set_invoices(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["account.move"].search([]).write({"not_in_fiscal_book": False})
