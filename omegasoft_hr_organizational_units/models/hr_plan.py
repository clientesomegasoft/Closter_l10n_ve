# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HrPlan(models.Model):
    _inherit = "hr.plan"

    organizational_units_id = fields.Many2one(
        "hr.organizational.units",
        string="organizational units",
        domain="[('company_id', '=', company_id)]",
        check_company=True,
    )
