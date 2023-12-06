# -*- coding: utf-8 -*-

import io
from odoo import models
from odoo.tools.misc import xlsxwriter

class AccountReport(models.Model):
	_inherit = "account.report"

	def export_to_xlsx(self, options, response=None):
		if self.custom_handler_model_name != 'account.kardex.report.handler':
			return super().export_to_xlsx(options, response=response)

		self.ensure_one()
		output = io.BytesIO()
		workbook = xlsxwriter.Workbook(output, {
			'in_memory': True,
			'strings_to_formulas': False,
		})

		sheet = workbook.add_worksheet(self.name[:31])
		bold_style = workbook.add_format({'font_name': 'Helvetica Neue', 'bold': True, 'font_size': 10})
		header_style = workbook.add_format({'font_name': 'Helvetica Neue', 'bold': True, 'font_size': 10, 'align': 'center', 'border': True})
		section_style = workbook.add_format({'font_name': 'Helvetica Neue', 'bold': True, 'font_size': 10, 'bg_color': '#d9d9d9'})
		default_style = workbook.add_format({'font_name': 'Helvetica Neue', 'font_size': 10})
		date_default_style = workbook.add_format({'font_name': 'Helvetica Neue', 'font_size': 10, 'num_format': 'yyyy-mm-dd'})

		#ENCABEZADO DE COMPAÑIA
		company_id = self.env.company.partner_id
		sheet.merge_range(1, 1, 1, 10, 'Nombre de la empresa: ' + company_id.name, bold_style)
		sheet.merge_range(2, 1, 2, 10, 'RIF.: ' + company_id.vat, bold_style)
		sheet.merge_range(3, 1, 3, 10, 'Dirección de la empresa: ' + company_id.contact_address.replace('\n', ' '), bold_style)
		sheet.merge_range(4, 1, 4, 10, self.name.upper(), bold_style)
		sheet.merge_range(5, 1, 5, 2, 'Desde: '+options['date']['date_from'], bold_style)
		sheet.merge_range(5, 3, 5, 10, 'Hasta: '+options['date']['date_to'], bold_style)
		y_offset = 8

		header_1 = [
			{'name': '', 'colspan': 3},
			{'name': 'Saldo inicial', 'colspan': 4},
			{'name': 'Entrada', 'colspan': 4},
			{'name': 'Salida', 'colspan': 4},
			{'name': 'Ajuste', 'colspan': 4},
			{'name': 'Saldo final', 'colspan': 4},
		]
		header_2 = [
			{'name': 'Referencia interna'},
			{'name': 'Producto'},
			{'name': 'Fecha'},
		]
		header_2 += [
			{'name': 'Cantidad'},
			{'name': 'Valor unitario'},
			{'name': 'UdM'},
			{'name': 'Valor total'},
		] * 5

		# Add headers.
		for header in [header_1, header_2]:
			x_offset = 1
			for column in header:
				colspan = column.get('colspan', 1)
				if colspan == 1:
					sheet.set_column(x_offset, x_offset, 15)
					sheet.write(y_offset, x_offset, column['name'], header_style)
				else:
					sheet.merge_range(y_offset, x_offset, y_offset, x_offset + colspan - 1, column['name'], header_style)
				x_offset += colspan
			y_offset += 1

		sheet.set_column(2, 2, 25) #COLUMNA DE NOMBRE DE PRODUCTO
		handler = self.env[self.custom_handler_model_name]

		for product in handler._get_product_ids(options):
			product_name = product.display_name
			uom_name = product.uom_id.display_name
			sheet.merge_range(y_offset, 1, y_offset, 23, product_name, section_style)
			y_offset += 1

			for line in handler._get_svl_lines(options, product):
				if line['type'] == 'Entrada':
					x_offset = 8
				elif line['type'] == 'Salida':
					x_offset = 12
				elif line['type'] == 'Ajuste':
					x_offset = 16

				sheet.write(y_offset, 1, product.default_code, default_style)
				sheet.write(y_offset, 2, product_name, default_style)
				sheet.write_datetime(y_offset, 3, line['create_date'], date_default_style)
				#SALDO INICIAL
				sheet.write(y_offset, 4, line['init_quantity'], default_style)
				sheet.write(y_offset, 5, line['init_unit_cost'], default_style)
				sheet.write(y_offset, 6, uom_name, default_style)
				sheet.write(y_offset, 7, line['init_value'], default_style)
				#MOVIMIENTO
				sheet.write(y_offset, x_offset, line['quantity'], default_style)
				sheet.write(y_offset, x_offset + 1, line['unit_cost'], default_style)
				sheet.write(y_offset, x_offset + 2, uom_name, default_style)
				sheet.write(y_offset, x_offset + 3, line['value'], default_style)
				#SALDO FINAL
				sheet.write(y_offset, 20, line['end_quantity'], default_style)
				sheet.write(y_offset, 21, line['end_unit_cost'], default_style)
				sheet.write(y_offset, 22, uom_name, default_style)
				sheet.write(y_offset, 23, line['end_value'], default_style)
				y_offset += 1

		workbook.close()
		output.seek(0)
		generated_file = output.read()
		output.close()
		
		return {
			'file_name': self.get_default_report_filename('xlsx'),
			'file_content': generated_file,
			'file_type': 'xlsx',
		}