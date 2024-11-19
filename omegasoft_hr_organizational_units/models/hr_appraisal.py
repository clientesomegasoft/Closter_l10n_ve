# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrAppraisal(models.Model):
    _inherit = "hr.appraisal"

    organizational_units_id = fields.Many2one(
        "hr.organizational.units",
        string="organizational units",
        related="employee_id.organizational_units_id",
    )
