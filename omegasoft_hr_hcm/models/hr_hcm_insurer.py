from odoo import fields, models


class HrHCMInsurer(models.Model):
    _name = "hr.hcm.insurer"
    _description = "Insurer"

    name = fields.Char("Name", required=True)
