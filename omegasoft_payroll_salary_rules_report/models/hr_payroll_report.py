from odoo import fields, models, tools


class HrPayrollReport(models.Model):
    _inherit = "hr.payroll.report"

    salary_rule_name = fields.Char("Salary rule", readonly=True)
    count_assignments = fields.Float("Assignments", readonly=True)
    count_deductions = fields.Float("Deductions", readonly=True)
    employee_category_id = fields.Many2one(
        "hr.employee.category", "Category", readonly=True
    )

    def init(self):
        query = """
            SELECT
                p.id AS id,
                CASE
                 WHEN wd.id = min_id.min_line
                 AND src.case = 1
                 THEN 1
                 ELSE 0
                END AS count,
                CASE
                 WHEN wet.is_leave or src.case = 0
                 THEN 0
                 ELSE wd.number_of_days
                END AS count_work,
                CASE
                 WHEN wet.is_leave or src.case = 0
                 THEN 0
                 ELSE wd.number_of_hours
                END AS count_work_hours,
                CASE
                 WHEN wet.is_leave
                 AND wd.amount <> 0
                 AND src.case = 1
                 THEN wd.number_of_days
                 ELSE 0
                END AS count_leave,
                CASE
                 WHEN wet.is_leave
                 AND wd.amount = 0
                 AND src.case = 1
                 THEN wd.number_of_days
                 ELSE 0
                END AS count_leave_unpaid,
                CASE
                 WHEN wet.is_unforeseen
                 AND src.case = 1
                 THEN wd.number_of_days
                 ELSE 0
                END AS count_unforeseen_absence,
                CASE
                 WHEN wet.is_leave
                 AND src.case = 1
                 THEN wd.amount
                 ELSE 0
                END AS leave_basic_wage,
                p.name AS name,
                p.date_from AS date_from,
                p.date_to AS date_to,
                e.id AS employee_id,
                e.department_id AS department_id,
                c.job_id AS job_id,
                e.company_id AS company_id,
                d.master_department_id AS master_department_id,
                wet.id AS work_code,
                CASE
                 WHEN wet.is_leave IS NOT TRUE
                 THEN '1' WHEN wd.amount = 0 THEN '3'
                 ELSE '2'
                END AS work_type,
                CASE
                 WHEN src.case = 1
                 HEN wd.number_of_days
                 ELSE 0
                END AS number_of_days,
                CASE
                 WHEN src.case = 1
                 THEN wd.number_of_hours
                 ELSE 0
                END AS number_of_hours,
                CASE
                 WHEN wd.id = min_id.min_line
                 AND src.case = 1
                 THEN pln.total
                 ELSE 0
                END AS net_wage,
                CASE
                 WHEN wd.id = min_id.min_line
                 AND src.case = 1
                 THEN plb.total
                 ELSE 0
                END AS basic_wage,
                CASE
                 WHEN wd.id = min_id.min_line
                 AND src.case = 1
                 THEN plg.total
                 ELSE 0
                END AS gross_wage,
                pl.name AS salary_rule_name,
                CASE
                 WHEN src.code IN ('BASIC','ALW','BASIC2','BASIC3')
                 AND wd.id = min_id.min_line
                 THEN pl.total
                 ELSE 0
                END AS count_assignments,
                CASE
                 WHEN src.code IN ('DED','COMP','CONTRIB')
                 AND wd.id = min_id.min_line
                 THEN pl.total
                 ELSE 0
                END AS count_deductions,
                ec.category_id AS employee_category_id
            FROM
                (SELECT * FROM hr_payslip WHERE state IN ('done', 'paid')) p
                    LEFT JOIN hr_employee e ON (p.employee_id = e.id)
                    LEFT JOIN hr_payslip_worked_days wd ON (wd.payslip_id = p.id)
                    LEFT JOIN hr_work_entry_type wet ON (wet.id = wd.work_entry_type_id)
                    LEFT JOIN (
                        SELECT payslip_id, min(id) AS min_line
                        FROM hr_payslip_worked_days
                        GROUP BY payslip_id
                    ) min_id ON (min_id.payslip_id = p.id)
                    LEFT JOIN hr_payslip_line pln ON (
                        pln.slip_id = p.id
                        AND  pln.code = 'NET')
                    LEFT JOIN hr_payslip_line plb ON (
                        plb.slip_id = p.id
                        AND plb.code IN ('TBASIC','TBASICQ','TBASICP')
                    )
                    LEFT JOIN hr_payslip_line plg ON (
                        plg.slip_id = p.id
                        AND plg.code IN ('TA', 'TAQ')
                    )
                    LEFT JOIN hr_contract c ON (p.contract_id = c.id)
                    LEFT JOIN hr_payslip_line pl ON (
                        pl.slip_id = p.id
                        AND pl.category_id IN (
                            SELECT src.id
                            FROM hr_salary_rule_category src
                            WHERE src.code IN (
                                'NET','BASIC','ALW','BASIC2','BASIC3', 'DED','COMP','CONTRIB'
                            )
                        )
                    )
                    LEFT JOIN (
                        SELECT id, code,
                        CASE
                         WHEN code = 'NET'
                         THEN 1
                         ELSE 0
                        END
                        FROM hr_salary_rule_category
                    ) src ON (pl.category_id = src.id)
                    LEFT JOIN employee_category_rel ec ON (ec.emp_id = e.id)
                    LEFT JOIN hr_department d ON (e.department_id = d.id)
            GROUP BY
                e.id,
                e.department_id,
                e.company_id,
                wd.id,
                wet.id,
                p.id,
                p.name,
                p.date_from,
                p.date_to,
                pln.total,
                plb.total,
                plg.total,
                min_id.min_line,
                c.id,
                pl.name,
                src.code,
                pl.total,
                src.case,
                ec.category_id,
                d.master_department_id
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
