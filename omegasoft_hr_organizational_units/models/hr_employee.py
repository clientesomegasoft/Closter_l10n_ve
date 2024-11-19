from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    organizational_units_id = fields.Many2one(
        "hr.organizational.units",
        string="organizational units",
        domain="[('company_id', '=', company_id)]",
    )
    active_organizational_units = fields.Boolean(
        string="active organizational units",
        related="company_id.active_organizational_units",
    )
