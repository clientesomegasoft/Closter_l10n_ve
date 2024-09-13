# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime  import date

class Canapdis(models.Model):
    _name = 'hr.canapdis'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'CANAPDIS'

    name = fields.Char('Name', default="CANAPDIS-%s" % date.today().strftime("%d/%m/%Y"))
    date = fields.Date(string='Date', default= date.today(), readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda s: s.env.company)
    employee_ids = fields.Many2many('hr.employee', string='Employees') 

    def get_employee(self):
        query = """
        SELECT 
            DISTINCT employee.id
        FROM
            hr_employee employee
            JOIN hr_employee_hr_employee_disability_rel dis_rel ON dis_rel.hr_employee_id = employee.id
        """
        self._cr.execute(query)
        result = self._cr.fetchall()
        self.employee_ids = [(6, 0, [rec[0] for rec in result])]