from odoo import _, fields, models


class PayslipReport(models.Model):
    _inherit = "hr.payslip"

    def _get_lines(self):
        categories_assignments = self._get_categories_assignments()
        categories_deductions = self._get_categories_deductions()
        lines = self.line_ids.filtered(
            lambda line: line.appears_on_payslip
            and (
                line.category_id.code in categories_assignments
                or line.category_id.code in categories_deductions
            )
        )
        data = [lines[i : i + 15] for i in range(0, len(lines), 15)]
        return data

    def _get_payroll_structure_for_average_vacation_salary(self):
        return (
            self.company_id.payroll_structure_for_average_vacation_salary.ids
            if self.company_id.payroll_structure_for_average_vacation_salary
            else []
        )

    def _get_payroll_structure_for_salary_settlement(self):
        return (
            self.company_id.payroll_structure_for_salary_settlement.ids
            if self.company_id.payroll_structure_for_salary_settlement
            else []
        )

    def _salary_settlement(self):
        for record in self:
            salary_settlement = 0
            if (
                record.struct_id
                and record.struct_id.type_id.default_schedule_pay == "bi-weekly"
            ):
                salary_settlement = self.payslip_get_contract_wage() / 30
            elif (
                record.struct_id
                and record.struct_id.type_id.default_schedule_pay == "weekly"
            ):
                salary_settlement = (self.payslip_get_contract_wage() / 4) / 7
        return salary_settlement

    def _get_categories_assignments(self):
        return (
            self.company_id.salary_rules_categories_assignments.mapped("code")
            if self.company_id.salary_rules_categories_assignments
            else []
        )

    def _get_categories_deductions(self):
        return (
            self.company_id.salary_rules_categories_deductions.mapped("code")
            if self.company_id.salary_rules_categories_deductions
            else []
        )

    def _get_other_entries_type_code(self):
        return (
            self.company_id.lines_other_entries_type.mapped("code")
            if self.company_id.lines_other_entries_type
            else []
        )

    # method for calculating the accumulated Allocations
    def accumulated_assignments(self):
        categories_assignments = self._get_categories_assignments()
        return sum(
            line.total
            for line in self.line_ids.filtered(
                lambda x: x.appears_on_payslip
                and x.category_id.code in categories_assignments
            )
        )

    # method for calculating the accumulated Deductions
    def accumulated_deductions(self):
        categories_deductions = self._get_categories_deductions()
        return sum(
            line.total
            for line in self.line_ids.filtered(
                lambda x: x.appears_on_payslip
                and x.category_id.code in categories_deductions
            )
        )

    def compute_report_name(self):
        return (
            self.struct_id.report_name_id.name.upper()
            if self.struct_id.report_name_id
            else _("Salary Slip")
        )

    def payslip_get_contract_wage(self):
        wage = 0
        for line in self.line_ids:
            wage += line.amount if line.code == "BAS7" else 0
        return wage


class PayrollStructure(models.Model):
    _inherit = "hr.payroll.structure"

    report_name_id = fields.Many2one(
        string="Report name",
        comodel_name="hr_receipt_payment_names",
        ondelete="restrict",
    )


class UomCategory(models.Model):
    _inherit = "uom.category"

    is_payroll_category = fields.Boolean(
        string="Is payroll category",
    )


class PayrollInput(models.Model):
    _inherit = "hr.payslip.input"

    uom_id = fields.Many2one(
        string="Uom",
        comodel_name="uom.uom",
        ondelete="restrict",
    )
