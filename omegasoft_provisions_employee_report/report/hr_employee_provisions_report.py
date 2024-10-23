# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools


class HrContractEmployeeReport(models.Model):
    _name = "hr.employee.provisions.report"
    _description = "Employees Provisions Report"
    _auto = False

    contract_id = fields.Many2one("hr.contract", "Contract", readonly=True)
    employee_id = fields.Many2one("hr.employee", "Employee", readonly=True)
    company_id = fields.Many2one("res.company", "Company", readonly=True)
    department_id = fields.Many2one("hr.department", "Department", readonly=True)

    # Utilidades
    earnings_generated = fields.Float("Earnings generated", readonly=True)
    advances_granted = fields.Float("Advances granted", readonly=True)
    earnings_generated_total_available = fields.Float(
        "Earnings generated total available", readonly=True
    )

    # Prestaciones Sociales
    social_benefits_generated = fields.Float("Social benefits generated", readonly=True)
    accrued_social_benefits = fields.Float("Accrued social benefits", readonly=True)
    advances_of_social_benefits = fields.Float(
        "Advances of social benefits", readonly=True
    )
    total_available_social_benefits_generated = fields.Float(
        "Total available social benefits generated", readonly=True
    )
    benefit_interest = fields.Float("Benefit interest", readonly=True)
    days_per_year_accumulated = fields.Float("Days per year accumulated", readonly=True)

    # Vacaciones
    vacations_advances_granted = fields.Float(
        "Vacations advances granted", readonly=True
    )

    def init(self):
        query = """
            SELECT
                c.id AS id,
                c.id AS contract_id,
                e.id AS employee_id,
                e.company_id AS company_id,
                d.id AS department_id,
                CASE
                 WHEN c.earnings_generated IS NOT NULL
                 THEN c.earnings_generated
                 ELSE 0
                END AS earnings_generated,
                CASE
                 WHEN c.advances_granted IS NOT NULL
                 THEN c.advances_granted
                 ELSE 0
                END AS advances_granted,
                CASE
                 WHEN c.earnings_generated_total_available IS NOT NULL
                 THEN c.earnings_generated_total_available
                 ELSE 0
                END AS earnings_generated_total_available,
                CASE
                 WHEN c.social_benefits_generated IS NOT NULL
                 THEN c.social_benefits_generated
                 ELSE 0
                END AS social_benefits_generated,
                CASE
                 WHEN c.accrued_social_benefits IS NOT NULL
                 THEN c.accrued_social_benefits
                 ELSE 0
                END AS accrued_social_benefits,
                CASE
                 WHEN c.advances_of_social_benefits IS NOT NULL
                 THEN c.advances_of_social_benefits
                 ELSE 0
                END AS advances_of_social_benefits,
                CASE
                 WHEN c.total_available_social_benefits_generated IS NOT NULL
                 THEN c.total_available_social_benefits_generated
                 ELSE 0
                END AS total_available_social_benefits_generated,
                CASE
                 WHEN c.benefit_interest IS NOT NULL
                 THEN c.benefit_interest
                 ELSE 0
                END AS benefit_interest,
                CASE
                 WHEN c.days_per_year_accumulated IS NOT NULL
                 THEN c.days_per_year_accumulated
                 ELSE 0
                END AS days_per_year_accumulated,
                CASE
                 WHEN c.vacations_advances_granted IS NOT NULL
                 THEN c.vacations_advances_granted
                 ELSE 0
                END AS vacations_advances_granted
            FROM
                (SELECT * FROM hr_contract AS c WHERE state != 'cancel') c
                LEFT JOIN hr_employee e ON (e.id = c.employee_id)
                LEFT JOIN hr_department d ON (d.id = e.department_id )
            GROUP BY
                c.id,
                e.id,
                d.id,
                c.earnings_generated,
                c.advances_granted,
                c.earnings_generated_total_available,
                c.social_benefits_generated,
                c.accrued_social_benefits,
                c.advances_of_social_benefits,
                c.total_available_social_benefits_generated,
                c.benefit_interest,
                c.days_per_year_accumulated,
                c.vacations_advances_granted
                """
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """CREATE OR REPLACE VIEW {self_table} AS ({query})"""
        self._cr.execute(
            sql,
            (
                tuple(
                    self_table=self._table,
                    query=query,
                ),
            ),
        )
