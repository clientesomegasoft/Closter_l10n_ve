from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrContract(models.Model):
    _inherit = "hr.contract"

    special_bonus_applies = fields.Boolean(string="Special Bonus", default=False)
    special_bonus_currency_id = fields.Many2one(
        comodel_name="res.currency", string="Special Bonus Currency"
    )
    special_bonus_amount = fields.Monetary(
        string="Special Bonus Amount", currency_field="special_bonus_currency_id"
    )

    productivity_bonus_applies = fields.Boolean(
        string="Productivity Bonus", default=False
    )
    productivity_bonus_currency_id = fields.Many2one(
        comodel_name="res.currency", string="Productivity Bonus Currency"
    )
    productivity_bonus_amount = fields.Monetary(
        string="Productivity Bonus Amount",
        currency_field="productivity_bonus_currency_id",
    )

    seniority_bonus_applies = fields.Boolean(string="Seniority Bonus", default=False)
    seniority_bonus_currency_id = fields.Many2one(
        comodel_name="res.currency", string="Seniority Bonus Currency"
    )
    seniority_bonus_amount = fields.Monetary(
        string="Seniority Bonus Amount", currency_field="seniority_bonus_currency_id"
    )
    seniority_bonus_cap = fields.Float(string="Seniority Bonus Cap", default=0)

    mobility_bonus_applies = fields.Boolean(string="Mobility Bonus", default=False)
    mobility_bonus_currency_id = fields.Many2one(
        comodel_name="res.currency", string="Mobility Bonus Currency"
    )
    mobility_bonus_amount = fields.Monetary(
        string="Mobility Bonus Amount", currency_field="mobility_bonus_currency_id"
    )

    @api.constrains("seniority_bonus_cap", "seniority_bonus_amount")
    def seniority_bonus_amount_less_than_cap(self):
        for record in self:
            if (
                record.seniority_bonus_amount > record.seniority_bonus_cap
                and record.seniority_bonus_cap > 0
            ):
                raise ValidationError(
                    _("The seniority bonus amount must be less than its cap.")
                )
