from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    hcm_currency_id = fields.Many2one(
        "res.currency",
        related="hcm_coverage_scale_id.currency_id",
        help="""Tenchincal field used to keep consistency
        on the amounts used in this record""",
    )

    hcm_is_inclusion = fields.Boolean("Inclusion")
    hcm_is_exclusion = fields.Boolean("Exclusion")

    hcm_insurer_id = fields.Many2one("hr.hcm.insurer", string="Insurer")

    hcm_start_date = fields.Date("Start date")
    hcm_end_date = fields.Date("End date")

    hcm_coverage_scale_id = fields.Many2one(
        "hr.hcm.coverage.scale", string="HCM coverage scale"
    )

    hcm_total_quota_amount = fields.Monetary(
        "Total quota amount", currency_field="hcm_currency_id"
    )
    hcm_total_policy_coverage = fields.Monetary(
        "Total policy coverage", currency_field="hcm_currency_id"
    )
    hcm_company_quota_amount = fields.Monetary(
        "Company quota contribution", currency_field="hcm_currency_id"
    )
    hcm_employee_quota_amount = fields.Monetary(
        "Employee quota contribution", currency_field="hcm_currency_id"
    )

    @api.onchange("hcm_coverage_scale_id")
    def _onchange_hcm_coverage_scale_id(self):
        for record in self:
            source = record.hcm_coverage_scale_id

            record.hcm_total_quota_amount = source.total_quota_amount
            record.hcm_total_policy_coverage = source.total_policy_coverage
            record.hcm_company_quota_amount = source.company_quota_amount
            record.hcm_employee_quota_amount = source.employee_quota_amount
