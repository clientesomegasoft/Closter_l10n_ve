from odoo import fields, models


class HrPayrollStructureType(models.Model):
    _inherit = "hr.payroll.structure.type"

    is_worker_payroll = fields.Boolean(
        string="Worker payroll",
        help="Indicates whether the structure type is for a worker payroll.",
    )
