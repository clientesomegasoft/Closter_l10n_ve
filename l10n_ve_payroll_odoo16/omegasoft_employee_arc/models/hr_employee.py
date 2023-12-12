# -*- coding: utf-8 -*-

from odoo import models

class HrEmployeePrivate(models.Model):
	_inherit = "hr.employee"

	def get_arc_month_lines(self, months_table):
		self.ensure_one()
		self._cr.execute("""
			SELECT
				months_table.month_name AS month,
				COALESCE(SUM(CASE WHEN hpl.code = 'NET200' THEN hpl.total ELSE 0.0 END), 0.0) AS base,
				COALESCE(hc.percentage_income_tax_islr, 0.0) AS percentage,
				COALESCE(SUM(CASE WHEN hpl.code = 'COMP64' THEN hpl.total ELSE 0.0 END), 0.0) AS amount
			FROM {months_table}
			LEFT JOIN hr_payslip hp ON hp.date BETWEEN months_table.date_from AND months_table.date_to AND
				hp.employee_id = {employee_id} AND
				hp.state IN ('done', 'paid') AND
				hp.company_id = {company_id}
			LEFT JOIN hr_payslip_line hpl ON hpl.slip_id = hp.id
			LEFT JOIN hr_contract hc ON hc.id = hp.contract_id
			GROUP BY month, months_table.date_from, percentage
			ORDER BY months_table.date_from
		""".format(
			months_table=months_table,
			employee_id=self.id,
			company_id=self.company_id.id
		))
		return self._cr.dictfetchall()