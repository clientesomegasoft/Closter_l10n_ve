from odoo import models, fields, api, _
from odoo.tools import float_round, date_utils
from odoo.tools.misc import format_date

class ReportNames(models.Model):
    _name = "hr_receipt_payment_names"
    _description = "Report names"
    
    name = fields.Char(string='Report Name')

    active = fields.Boolean(
        default=True, help="Set active to false to hide the report name tag without removing it.")
