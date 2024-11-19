from odoo import fields, models


class Department(models.Model):
    _inherit = "hr.department"

    generate_commissions = fields.Boolean(string="Generate commissions")
