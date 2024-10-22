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
                p.id as id,
                CASE WHEN wd.id = min_id.min_line and src.case = 1 THEN 1 ELSE 0 END as count,
                CASE WHEN wet.is_leave or src.case = 0 THEN 0 ELSE wd.number_of_days END as count_work,
                CASE WHEN wet.is_leave or src.case = 0 THEN 0 ELSE wd.number_of_hours END as count_work_hours,
                CASE WHEN wet.is_leave and wd.amount <> 0 and src.case = 1 THEN wd.number_of_days ELSE 0 END as count_leave,
                CASE WHEN wet.is_leave and wd.amount = 0 and src.case = 1 THEN wd.number_of_days ELSE 0 END as count_leave_unpaid,
                CASE WHEN wet.is_unforeseen and src.case = 1 THEN wd.number_of_days ELSE 0 END as count_unforeseen_absence,
                CASE WHEN wet.is_leave and src.case = 1 THEN wd.amount ELSE 0 END as leave_basic_wage,
                p.name as name,
                p.date_from as date_from,
                p.date_to as date_to,
                e.id as employee_id,
                e.department_id as department_id,
                c.job_id as job_id,
                e.company_id as company_id,
                d.master_department_id as master_department_id,
                wet.id as work_code,
                CASE WHEN wet.is_leave IS NOT TRUE THEN '1' WHEN wd.amount = 0 THEN '3' ELSE '2' END as work_type,
                CASE WHEN src.case = 1 THEN wd.number_of_days ELSE 0 END as number_of_days,
                CASE WHEN src.case = 1 THEN wd.number_of_hours ELSE 0 END as number_of_hours,
                CASE WHEN wd.id = min_id.min_line and src.case = 1 THEN pln.total ELSE 0 END as net_wage,
                CASE WHEN wd.id = min_id.min_line and src.case = 1 THEN plb.total ELSE 0 END as basic_wage,
                CASE WHEN wd.id = min_id.min_line and src.case = 1 THEN plg.total ELSE 0 END as gross_wage,
                pl.name as salary_rule_name,
                CASE WHEN src.code in ('BASIC','ALW','BASIC2','BASIC3') and wd.id = min_id.min_line THEN pl.total ELSE 0 END as count_assignments,
                CASE WHEN src.code in ('DED','COMP','CONTRIB') and wd.id = min_id.min_line THEN pl.total ELSE 0 END as count_deductions,
                ec.category_id as employee_category_id
            FROM
                (SELECT * FROM hr_payslip WHERE state IN ('done', 'paid')) p
                    left join hr_employee e on (p.employee_id = e.id)
                    left join hr_payslip_worked_days wd on (wd.payslip_id = p.id)
                    left join hr_work_entry_type wet on (wet.id = wd.work_entry_type_id)
                    left join (select payslip_id, min(id) as min_line from hr_payslip_worked_days group by payslip_id) min_id on (min_id.payslip_id = p.id)
                    left join hr_payslip_line pln on (pln.slip_id = p.id and  pln.code = 'NET')
                    left join hr_payslip_line plb on (plb.slip_id = p.id and plb.code in ('TBASIC','TBASICQ','TBASICP'))
                    left join hr_payslip_line plg on (plg.slip_id = p.id and plg.code in ('TA', 'TAQ'))
                    left join hr_contract c on (p.contract_id = c.id)
                    left join hr_payslip_line pl on (pl.slip_id = p.id and pl.category_id in (select src.id from hr_salary_rule_category src where src.code IN ('NET','BASIC','ALW','BASIC2','BASIC3', 'DED','COMP','CONTRIB')))
                    left join (select id, code, case when code = 'NET' then 1 else 0 end from hr_salary_rule_category) src on (pl.category_id = src.id)
                    left join employee_category_rel ec on (ec.emp_id = e.id)
                    left join hr_department d on (e.department_id = d.id)
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
        sql = """CREATE or REPLACE VIEW {self_table} as ({query})"""
        self._cr.execute(
            sql,
            (
                tuple(
                    self_table=self._table,
                    query=query,
                ),
            ),
        )
