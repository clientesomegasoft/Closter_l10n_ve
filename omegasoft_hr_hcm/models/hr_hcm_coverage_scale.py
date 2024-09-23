from logging import getLogger

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare

_logger = getLogger(__name__)


class HrHCMCoverage(models.Model):
    _name = "hr.hcm.coverage.scale"
    _description = "HCM Coverage Scale"
    # TODO: Call it as Escala HCM.

    name = fields.Char("Name", required=True)
    code = fields.Char("Code", required=True)

    _sql_constraints = [
        ("coverage_code_uniq", "unique(code)", "Coverage code must be unique"),
    ]

    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self._get_default_currency_id(),
        help="""Tenchincal field used to keep consistency
        on the amounts used in this record""",
    )

    total_quota_amount = fields.Monetary(
        "Total quota amount", currency_field="currency_id"
    )
    total_policy_coverage = fields.Monetary(
        "Total policy coverage", currency_field="currency_id"
    )
    company_percentage_contribution = fields.Float("Percentage Company Contribution")
    company_quota_amount = fields.Monetary(
        "Quota company contribution",
        currency_field="currency_id",
        compute="_compute_quotas",
        store=True,
        help="Field updapted once the record is saved",
    )

    employee_quota_amount = fields.Monetary(
        "Quota employee contribution",
        currency_field="currency_id",
        compute="_compute_quotas",
        store=True,
        help="Field updapted once the record is saved",
    )

    job_ids = fields.Many2many(
        "hr.job",
        "hr_hcm_coverage_scale_hr_job_rel",
        "coverage_id",
        "job_id",
        string="Jobs",
    )

    @api.depends("total_quota_amount", "company_percentage_contribution")
    def _compute_quotas(self):
        for record in self:
            record.company_quota_amount = record.total_quota_amount * (
                record.company_percentage_contribution / 100.0
            )
            record.employee_quota_amount = (
                record.total_quota_amount - record.company_quota_amount
            )

    @api.model
    def _get_default_currency_id(self):
        # PATCH: Fix this in Odoo 17.0
        ves = self.env["res.currency"].search([("name", "=", "VES")])
        if not ves:
            ves = self.env.company.currency_id
            _logger.warning(
                "USING env.company.currency_id {ves} as "
                "default value for hr.hcm.coverage.scale"
            )
        return ves

    @api.constrains("company_percentage_contribution")
    def _constrains_company_percentage_contribution(self):
        for record in self:
            compare = lambda a, b: float_compare(
                a, b, precision_digits=record.currency_id.decimal_places
            )
            if compare(record.company_percentage_contribution, 100) > 0:
                raise ValidationError(
                    _(
                        "Company Percentage is too high (max 100)"
                    )
                )
            elif compare(record.company_percentage_contribution, 0) < 0:
                raise ValidationError(
                    _(
                        "Company Percentage is too low (min 0)"
                    )
                )
