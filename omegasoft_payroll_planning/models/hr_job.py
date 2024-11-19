from odoo import fields, models


class HrJob(models.Model):
    _inherit = "hr.job"

    rotating_job = fields.Boolean(string="Rotating job")
