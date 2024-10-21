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
                c.id as id,
                c.id as contract_id,
                e.id as employee_id,
                e.company_id as company_id,
                d.id as department_id,
                case when c.earnings_generated IS NOT NULL then c.earnings_generated else 0 end as earnings_generated,
                case when c.advances_granted IS NOT NULL then c.advances_granted else 0 end as advances_granted,
                case when c.earnings_generated_total_available IS NOT NULL then c.earnings_generated_total_available else 0 end as earnings_generated_total_available,
                case when c.social_benefits_generated IS NOT NULL then c.social_benefits_generated else 0 end as social_benefits_generated,
                case when c.accrued_social_benefits IS NOT NULL then c.accrued_social_benefits else 0 end as accrued_social_benefits,
                case when c.advances_of_social_benefits IS NOT NULL then c.advances_of_social_benefits else 0 end as advances_of_social_benefits,
                case when c.total_available_social_benefits_generated IS NOT NULL then c.total_available_social_benefits_generated else 0 end as total_available_social_benefits_generated,
                case when c.benefit_interest IS NOT NULL then c.benefit_interest else 0 end as benefit_interest,
                case when c.days_per_year_accumulated IS NOT NULL then c.days_per_year_accumulated else 0 end as days_per_year_accumulated,
                case when c.vacations_advances_granted IS NOT NULL then c.vacations_advances_granted else 0 end as vacations_advances_granted
            FROM
                (Select * FROM hr_contract as c WHERE state != 'cancel') c
                left join hr_employee e ON (e.id = c.employee_id)
                left join hr_department d on (d.id = e.department_id )
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
        self.env.cr.execute(f"""CREATE or REPLACE VIEW {self._table} as ({query})""")
