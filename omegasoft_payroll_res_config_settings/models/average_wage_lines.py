from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AverageWageLines(models.Model):
    _name = "average_wage_lines"
    _description = "Average Wage Lines"
    # _order = 'allocation_date desc'

    payroll_structure_type = fields.Many2one(
        "hr.payroll.structure.type", string="Structure type", ondelete="restrict"
    )
    structure_type_default_schedule_pay = fields.Selection(
        related="payroll_structure_type.default_schedule_pay"
    )
    salary_rule_category = fields.Many2many(
        "hr.salary.rule.category",
        string="Categories of wage rules",
        ondelete="restrict",
    )
    average_days = fields.Float(string="Average days")
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, ondelete="restrict"
    )
    number_of_weeks = fields.Float(string="number of weeks")
    best_weeks_check = fields.Boolean(string="Best Weeks Check", default=False)
    number_of_best_weeks = fields.Float(string="Number of Best Weeks")

    @api.constrains("average_days")
    def _check_average_days(self):
        for record in self:
            if (
                record.average_days <= 0
                and record.structure_type_default_schedule_pay == "monthly"
            ):
                raise ValidationError(_("El promedio de días debe ser superior a cero."))

    @api.constrains("number_of_best_weeks")
    def _check_number_of_best_weeks(self):
        for record in self:
            if record.number_of_best_weeks <= 0 and record.best_weeks_check:
                raise ValidationError(
                    _("Cantidad de mejores semanas debe ser mayor a cero.")
                )

    @api.constrains("number_of_weeks")
    def _check_number_of_weeks(self):
        for record in self:
            if (
                record.number_of_weeks <= 0
                and record.structure_type_default_schedule_pay == "weekly"
            ):
                raise ValidationError(
                    _("Cantidad de semanas a tomar debe ser mayor a cero.")
                )
