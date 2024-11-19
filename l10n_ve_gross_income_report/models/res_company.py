from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    town_hall_id = fields.Many2one("res.town.hall", string="Alcaldía")


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    town_hall_id = fields.Many2one(
        "res.town.hall", related="company_id.town_hall_id", readonly=False
    )
    town_hall_percentage = fields.Float(related="town_hall_id.percentage")
