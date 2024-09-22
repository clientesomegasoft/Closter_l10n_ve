from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ContractParafiscalContributionsField(models.Model):
    _inherit = "hr.contract"

    mandatory_social_security = fields.Boolean(
        string="Mandatory Social Security",
        help="Indicates that the employee pays social security contributions.",
        tracking=True,
    )
    forced_unemployment = fields.Boolean(
        string="Forced Unemployment",
        help="Indicates that the employee makes the forced unemployment contribution.",
        tracking=True,
    )
    housing_policy_law = fields.Boolean(
        string="Housing Policy Law",
        help="Indicates that the employee makes the Housing Policy Law contribution.",
        tracking=True,
    )
    income_tax_islr = fields.Boolean(
        string="Income Tax ISRL",
        help="Indicates that the employee makes the income tax contribution.",
        tracking=True,
    )
    inces = fields.Boolean(
        string="Inces",
        help="Indicates that the employee makes the INCES.",
        tracking=True,
    )

    percentage_income_tax_islr = fields.Float(
        string="Percentage Income Tax ISRL",
        help="""Indicates the percentage figure to
        be applied for Income Tax Withholding.""",
        tracking=True,
    )

    @api.constrains("percentage_income_tax_islr")
    def _check_percentage_income_tax_islr(self):
        for record in self:
            if (
                record.percentage_income_tax_islr < 0
                or record.percentage_income_tax_islr > 99
            ):
                raise ValidationError(
                    _("Los montos permitidos para el porcentaje "
                    "de ISLR estan en el rango [0,99].")
                )
