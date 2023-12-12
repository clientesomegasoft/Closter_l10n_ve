# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EmployeeCrew(models.Model):
    _name = 'hr.employee.crew'  
    _description = 'Employee crew'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name', required=True)
    employee_ids = fields.Many2many('hr.employee', string='Employees', required=True)
    company_id = fields.Many2one('res.company', string='Company', default= lambda s: s.env.company)

    
