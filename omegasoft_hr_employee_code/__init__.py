from . import models

# from odoo import api, SUPERUSER_ID


# def _create_employee_sequences(cr):
#     env = api.Environment(cr, SUPERUSER_ID, {})
#     company_ids = env['res.company'].search([])
#     for company in company_ids:
#         env['ir.sequence'].create({
#             'name': 'Employee file code',
#             'code': 'hr.employee.code',
#             'prefix': '',
#             'number_next': 1,
#             'number_increment': 1,
#             'padding': 6,
#             'company_id': company.id,
#         })

# def _set_employee_file_code(cr, registry):
#     env = api.Environment(cr, SUPERUSER_ID, {})
#     employee_ids = env['hr.employee'].search([])
#     for employee in employee_ids:
#         employee.registration_number = env['ir.sequence'].next_by_code('hr.employee.code')
