from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ContractBonusesField(models.Model):
    _inherit = "hr.contract"

    custom_contract_currency_bonus = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.company.currency_id
    )

    complementary_bonus_check = fields.Boolean(
        string="Complementary bonus",
        help="Indicates whether the employee has an active bonus",
        default=False,
        tracking=True,
    )
    complementary_bonus = fields.Monetary(
        string="Complementary bonus amount",
        help="It is an extra salary in dollars to compensate for the basic salary.",
        currency_field="complementary_bonus_currency",
        tracking=True,
    )
    complementary_bonus_currency = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.company.currency_id
    )

    night_bonus = fields.Boolean(
        string="Night bonus",
        help="Indicates whether the employee has an active bonus",
        default=False,
        tracking=True,
    )
    night_bonus_amount = fields.Monetary(
        string="Night bonus amount",
        help="Value assigned to the worker for night shift",
        currency_field="custom_contract_currency_bonus",
        tracking=True,
    )
    night_bonus_currency = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.company.currency_id
    )

    perfect_attendance_bonus_check = fields.Boolean(
        string="Perfect attendance bonus",
        help="Indicates whether the employee has an active bonus",
        default=False,
        tracking=True,
    )
    perfect_attendance_bonus = fields.Monetary(
        string="Perfect attendance bonus amount",
        help="Bonus for punctual attendance at the assigned schedule.",
        currency_field="custom_contract_currency_bonus",
        tracking=True,
    )
    perfect_attendance_bonus_currency = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.company.currency_id
    )

    @api.constrains(
        "complementary_bonus", "night_bonus_amount", "perfect_attendance_bonus"
    )
    def _check_amount_bonuses_salarys(self):
        for record in self:
            if (
                record.complementary_bonus < 0
                or record.night_bonus_amount < 0
                or record.perfect_attendance_bonus < 0
            ):
                raise ValidationError(
                    "Los montos de los bonos de salarios deben ser superiores a cero."
                )
