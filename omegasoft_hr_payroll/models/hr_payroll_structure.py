from odoo import fields, models


class HrPayrollStructureType(models.Model):
    _inherit = "hr.payroll.structure.type"

    currency_id = fields.Many2one("res.currency", string="Currency")


class HrPayslip(models.Model):
    _name = "hr.payroll.structure"
    _inherit = ["hr.payroll.structure", "mail.thread", "mail.activity.mixin"]

    department_ids = fields.Many2many(
        string="Departments", comodel_name="hr.department"
    )
    currency_id = fields.Many2one(
        "res.currency", string="Currency", related="type_id.currency_id"
    )
    wage_type = fields.Selection(related="type_id.wage_type")
    use_average_wage = fields.Boolean(
        "use average salary calculation?", default=False, tracking=True
    )
    complementary_payroll = fields.Boolean(
        "is complementary payroll?",
        help="This structure will be available when generating payroll for employees with weekly and monthly structures.",
        default=False,
        tracking=True,
    )
    is_bonus = fields.Boolean("Is bonus payroll", default=False, tracking=True)
    is_perfect_attendance = fields.Boolean(
        "Is perfect attendance", default=False, tracking=True
    )
    is_night_bonus = fields.Boolean("Is night bonus", default=False, tracking=True)
    is_special_bonus = fields.Boolean("Is special bonus", default=False, tracking=True)
    is_seniority_bonus_applies = fields.Boolean(
        "Is seniority bonus applies", default=False, tracking=True
    )
    is_productivity_bonus_applies = fields.Boolean(
        "Is productivity bonus applies", default=False, tracking=True
    )
    is_mobility_bonus_applies = fields.Boolean(
        "Is mobility bonus applies", default=False, tracking=True
    )
