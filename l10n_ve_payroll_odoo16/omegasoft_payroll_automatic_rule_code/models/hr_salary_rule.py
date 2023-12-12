# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    code = fields.Char(compute='_compute_code', store=True, required=False)

    @api.depends('category_id.code', 'sequence')
    def _compute_code(self):
        for record in self:
            if record.category_id:
                record.code = record.category_id.code + str(record.sequence) 
            else:
                record.code = False
