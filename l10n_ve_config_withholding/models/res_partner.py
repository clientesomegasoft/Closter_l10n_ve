from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    is_company_partner = fields.Boolean(compute="_compute_is_company_partner")

    def _compute_is_company_partner(self):
        companies = self.env["res.company"].search([]).partner_id.ids
        for partner in self:
            partner.is_company_partner = partner.id in companies
