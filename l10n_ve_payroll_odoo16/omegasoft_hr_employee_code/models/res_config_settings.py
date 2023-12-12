# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    employee_file = fields.Boolean('Employee File', related="company_id.employee_file", readonly=False)
    sequence_next_number = fields.Integer('Sequence Next Number', related="company_id.sequence_next_number", readonly=False)


class ResCompany(models.Model):
    _inherit = 'res.company'

    employee_file = fields.Boolean('Employee File', default=False)
    sequence_next_number = fields.Integer('Sequence Next Number')

    def write(self, vals):
        res = super().write(vals)
        sequence = self.env['ir.sequence'].search([('code', '=', 'hr.employee.code'), ('company_id', '=', self.id)], limit=1)
        file_code_access = self.env['ir.model.access'].search([('name', '=', 'omegasoft_hr_employee_code.employee_file_code')])
        if 'employee_file' in vals and self.employee_file:
            if not sequence:
                self.env['ir.sequence'].create({
                    'name': 'Employee file code',
                    'code': 'hr.employee.code',
                    'prefix': '',
                    'number_next': 1,
                    'number_increment': 1,
                    'padding': 6,
                    'company_id': self.id,
                })
            file_code_access.write({
                'perm_write': True,
                'perm_create': True,
                'perm_unlink': True,
            })

        elif 'employee_file' in vals:
            file_code_access.write({
                'perm_write': False,
                'perm_create': False,
                'perm_unlink': False,
            })

        if 'sequence_next_number' in vals and self.sequence_next_number:
            sequence.number_next = self.sequence_next_number
        
        return res
