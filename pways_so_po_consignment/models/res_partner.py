from odoo import fields, models


class ResPartnerIn(models.Model):
    _inherit = "res.partner"

    is_consignments = fields.Boolean(
        string="Consignments", help="Consignments", copy=False
    )
    commission = fields.Float(string="Commission (%)")


class Product(models.Model):
    _inherit = "product.template"

    is_consignments = fields.Boolean(
        string="Consignments", help="Consignments", copy=False
    )
