
from odoo import models, fields, api

class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'

    is_worker_payroll = fields.Boolean(string="Worker payroll", help="Indicates whether the structure type is for a worker payroll.")