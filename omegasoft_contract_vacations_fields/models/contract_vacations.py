from odoo import fields, models


class ContractVacationsField(models.Model):
    _inherit = "hr.contract"

    vacations_advances_granted = fields.Monetary(
        string="Vacations Advances granted",
        help="",
        currency_field="vacations_advances_granted_currency",
        tracking=True,
    )
    vacations_advances_granted_previous_amount = fields.Monetary(
        string="Vacations Advances granted previous amount",
        help="",
        currency_field="vacations_advances_granted_currency",
        tracking=True,
    )
    vacations_advances_granted_currency = fields.Many2one(
        comodel_name="res.currency", default=lambda self: self.env.company.currency_id
    )
