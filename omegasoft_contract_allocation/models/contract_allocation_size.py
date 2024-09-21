from odoo import fields, models


class HrContractAllocationSize(models.Model):
    _name = "contract_allocation_size"
    _description = "Allocation Size"

    name = fields.Char(string="Name")
