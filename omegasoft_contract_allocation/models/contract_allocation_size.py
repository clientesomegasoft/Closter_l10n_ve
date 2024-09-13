# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta

class HrContractAllocationSize(models.Model):
    _name = 'contract_allocation_size'
    _description = "Allocation Size"

    name = fields.Char(string='Name')