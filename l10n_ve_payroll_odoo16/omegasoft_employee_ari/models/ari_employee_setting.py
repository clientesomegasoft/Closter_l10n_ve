# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AriEmployeeSetting(models.Model):
	_name = "ari.employee.setting"
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = "Configuración ARI"
	_rec_name = "employee_id"

	fiscal_year = fields.Integer(string='Año gravable', default=fields.Date.today().year, required=True)
	employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
	line_ids = fields.One2many('ari.employee.setting.lines', 'ari_setting_id', string='Lineas')
	company_id = fields.Many2one('res.company', string='compañia', default=lambda self: self.env.company.id)

	_sql_constraints = [('unique_employee_per_year', 'UNIQUE(fiscal_year, employee_id)', 'Ya existe un registro del empleado para el año gravable seleccionado !!!')]
	
	# employee file code
	employee_file = fields.Boolean('Employee file', related="company_id.employee_file")
	employee_file_code_id = fields.Many2one('employee.file.code', string='Employee File')
	company_id = fields.Many2one(comodel_name='res.company', ondelete='restrict', string='Company', default=lambda self: self.env.company, tracking=True)
	
	@api.onchange('employee_file_code_id')
	def _onchange_employee_file_code_id(self):
		if self.employee_file:
			if self.employee_file_code_id and self.employee_file:
				self.write({'employee_id': self.employee_file_code_id.employee_id.id})
			elif not self.employee_file_code_id and self.employee_id:
				self.write({'employee_id': False})

            
	@api.onchange('employee_id')
	def _onchange_employee(self):
		if self.employee_file:
			if self.employee_id:
				self.write({'employee_file_code_id': self.employee_id.employee_file_code_id.id})
			elif not self.employee_id and self.employee_file_code_id:
				self.write({'employee_file_code_id': False})
    
    # employee file code

class AriEmployeeSettingLines(models.Model):
	_name = "ari.employee.setting.lines"
	_description = "Lineas configuración ARI"

	ari_setting_id = fields.Many2one('ari.employee.setting', string='Configuracion ARI')
	fiscal_year = fields.Integer(related='ari_setting_id.fiscal_year')
	employee_id = fields.Many2one(related='ari_setting_id.employee_id', store=True)
	expense = fields.Selection([
		('education', 'Institutos docentes por la educación del contribuyente y descendientes no mayores de 25 años'),
		('HCM', 'Primas de seguros de Hospitalizacion, cirugia y maternidad'),
		('odontology', 'Gastos de servicios Medicos, Odontologicos y de Hospitalizacion'),
		('house', 'Intereses para la adquisicion de la vivienda principal o del pago del alquiler de la vivienda'),
		('extra', 'Monto retenido de mas en años anteriores')],
		string='Degravamenes',
		required=True
	)
	amount = fields.Float(string='Monto')
	trimester_1 = fields.Boolean(string='1er Trimestre', default=False)
	trimester_2 = fields.Boolean(string='2do Trimestre', default=False)
	trimester_3 = fields.Boolean(string='3er Trimestre', default=False)
	trimester_4 = fields.Boolean(string='4to Trimestre', default=False)

	_sql_constraints = [
		('at_lest_one_active_tremester', 'CHECK(trimester_1 OR trimester_2 OR trimester_3 OR trimester_4)', 'Al menos un trimestre debe estar activo para la creacion de la linea.'),
		('amount_greater_than_zero', 'CHECK(amount > 0.0)', 'El monto de cada linea debe ser mayor a cero.'),
	]

	def _get_ari_setting_by_trimester(self, trimester):
		return {line.expense: line.amount for line in self if getattr(line, trimester)}


class HrEmployeeARI(models.Model):
	_name = "hr.employee.ari"
	_description = "Lineas ARI"

	employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
	fiscal_year = fields.Integer(string='Año gravable')
	trimester = fields.Selection([
		('trimester_1', '1er Trimestre'),
		('trimester_2', '2do Trimestre'),
		('trimester_3', '3er Trimestre'),
		('trimester_4', '4to Trimestre')],
		string='Trimestre',
		required=True
	)
	wage = fields.Float(string='Salario')
	ut = fields.Float(string='Unidad tributaria')
	education = fields.Float(string='Educación')
	HCM = fields.Float(string='HCM')
	odontology = fields.Float(string='Odontologia')
	house = fields.Float(string='Vivienda')
	family = fields.Float(string='Carga familiar')
	extra = fields.Float(string='Retenido de mas')
	percentage = fields.Float(string='Porcentaje a retener')

	_sql_constraints = [('unique_line_per_trimester', 'UNIQUE(employee_id, fiscal_year, trimester)', 'Ya existen lineas generadas en este trimestre para los empleados.'),]